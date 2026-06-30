"""Catálogo dinâmico de temas e composições de mesa.

A plataforma lê os arquivos de `temas/` e `composicao_mesa/` em tempo de
execução — adicionar/remover áreas, subtemas, temas de mesa ou personas é
refletido automaticamente no próximo deploy (reinício), sem mexer em código.

Este módulo INSPECIONA e VALIDA essa estrutura: conta tudo, aponta problemas
(ex.: tema com menos personas que o tamanho da mesa) e expõe um resumo para:
  - log de inicialização (main.py),
  - endpoint GET /api/catalog,
  - verificação de deploy (`python -m catalog`).
"""
from typing import Dict, List

from core import config
from temas import loader as temas_loader
from composicao_mesa import loader as mesa_loader

# Tipos de item que exigem opções / escala (para validação)
_NEEDS_OPTIONS = {"single_select", "multi_select", "ranking"}
_NUMERIC_RANGE = {"number", "slider"}


def table_size() -> int:
    return config.TABLE_SIZE


def _temas_block() -> Dict:
    errors: List[str] = []
    warnings: List[str] = []
    areas_out: List[Dict] = []
    subtemas_total = 0
    try:
        areas = temas_loader.load_areas()
    except Exception as e:  # arquivo ausente / malformado
        return {
            "source": str(temas_loader.temas_file()),
            "areas_count": 0, "subtemas_count": 0, "areas": [],
            "errors": [f"temas: {e}"], "warnings": [],
        }
    seen = set()
    for a in areas:
        aid = a.get("id") or "(sem id)"
        subs = a.get("subtemas") or []
        if aid in seen:
            errors.append(f"temas: área duplicada '{aid}'")
        seen.add(aid)
        if not a.get("title"):
            warnings.append(f"temas: área '{aid}' sem título")
        if not subs:
            errors.append(f"temas: área '{aid}' não tem subtemas")
        subtemas_total += len(subs)
        areas_out.append({"id": aid, "title": a.get("title"), "subtemas_count": len(subs)})
    return {
        "source": str(temas_loader.temas_file()),
        "areas_count": len(areas),
        "subtemas_count": subtemas_total,
        "areas": areas_out,
        "errors": errors,
        "warnings": warnings,
    }


def _mesa_block(n: int) -> Dict:
    errors: List[str] = []
    warnings: List[str] = []
    themes_out: List[Dict] = []
    personas_total = 0

    d = mesa_loader.mesa_dir()
    files = [f for f in sorted(d.glob("*.yaml")) if not f.name.startswith("_")] if d.exists() else []
    if not files:
        errors.append(f"composicao_mesa: nenhum arquivo .yaml em {d}")

    seen = set()
    for f in files:
        try:
            c = mesa_loader.load_table(f.stem)
        except Exception as e:  # arquivo malformado → reporta, não derruba
            errors.append(f"composicao_mesa: '{f.name}' inválido — {e}")
            continue
        count = len(c.personas)
        personas_total += count
        if c.id in seen:
            errors.append(f"composicao_mesa: id de tema duplicado '{c.id}'")
        seen.add(c.id)
        if count < n:
            warnings.append(
                f"composicao_mesa: tema '{c.id}' tem {count} persona(s) "
                f"(< tamanho da mesa = {n}); a mesa sentará só {count}.")
        themes_out.append({"id": c.id, "title": c.title, "personas_count": count})

    return {
        "source": str(d),
        "themes_count": len(themes_out),
        "personas_total": personas_total,
        "themes": themes_out,
        "errors": errors,
        "warnings": warnings,
    }


def _instrumentos_block() -> Dict:
    """Inspeciona os formulários (instrumentos) em instruments/."""
    from instruments.loader import load_instrument

    errors: List[str] = []
    warnings: List[str] = []
    forms_out: List[Dict] = []

    d = config.INSTRUMENTS_DIR
    files = [f for f in sorted(d.glob("*.yaml")) if not f.name.startswith("_")] if d.exists() else []
    if not files:
        errors.append(f"instruments: nenhum arquivo .yaml em {d}")

    items_total = 0
    for f in files:
        try:
            inst = load_instrument(f.stem)
        except Exception as e:  # malformado → reporta, não derruba
            errors.append(f"instruments: '{f.name}' inválido — {e}")
            continue

        items = [it for sec in inst.sections for it in sec.items]
        items_total += len(items)
        types: Dict[str, int] = {}
        required_count = 0
        seen_ids = set()
        for it in items:
            types[it.type] = types.get(it.type, 0) + 1
            if it.required:
                required_count += 1
            if it.id in seen_ids:
                errors.append(f"instruments[{inst.id}]: id de item duplicado '{it.id}'")
            seen_ids.add(it.id)
            # Validações por tipo
            if it.type in _NEEDS_OPTIONS and not (it.options or []):
                errors.append(f"instruments[{inst.id}]: item '{it.id}' ({it.type}) sem 'options'")
            if it.type == "likert" and not it.scale:
                errors.append(f"instruments[{inst.id}]: item '{it.id}' (likert) sem 'scale'")
            if it.type == "likert" and it.scale and it.labels and len(it.labels) != it.scale:
                warnings.append(
                    f"instruments[{inst.id}]: item '{it.id}' tem {len(it.labels)} rótulos "
                    f"para escala {it.scale}")
            if it.type in _NUMERIC_RANGE and it.min is not None and it.max is not None and it.min >= it.max:
                errors.append(f"instruments[{inst.id}]: item '{it.id}' tem min >= max")

        forms_out.append({
            "id": inst.id,
            "title": inst.title,
            "moment": inst.moment,
            "sections_count": len(inst.sections),
            "items_count": len(items),
            "required_count": required_count,
            "item_types": types,
        })

    return {
        "source": str(d),
        "forms_count": len(forms_out),
        "items_total": items_total,
        "forms": forms_out,
        "errors": errors,
        "warnings": warnings,
    }


def _plataforma_block() -> Dict:
    """Resumo da configuração da plataforma (plataforma.yaml)."""
    from plataforma.loader import load_plataforma, plataforma_file
    errors: List[str] = []
    try:
        p = load_plataforma()
    except Exception as e:
        return {"source": "", "errors": [f"plataforma: {e}"], "config": {}}
    return {
        "source": str(plataforma_file()),
        "errors": errors,
        "config": {
            "mode": p.mode,
            "api_user_provides_key": p.api.user_provides_key,
            "api_provider": p.api.provider,
            "api_model": p.api.model,
            "theme_mode": p.theme.mode,
            "table_mode": p.table.mode,
            "table_size": p.table.size,
            "rounds": p.rounds,
            "best_idea": p.dynamics.best_idea,
            "judge_criterion": p.dynamics.judge_criterion,
            "owner_bias": p.dynamics.owner_bias,
            "pre_form": p.forms.pre_session_enabled,
            "post_form": p.forms.post_session_enabled,
        },
    }


def _juiz_block() -> Dict:
    from juiz.loader import load_juiz, juiz_file
    try:
        j = load_juiz()
    except Exception as e:
        return {"source": "", "errors": [f"juiz: {e}"], "juiz": {}}
    return {
        "source": str(juiz_file()),
        "errors": [],
        "juiz": {"name": j.name, "role": j.role, "criterion": j.criterion,
                 "blind_to_source": j.blind_to_source},
    }


def build_catalog() -> Dict:
    """Resumo completo da estrutura atual (contagens + avisos + erros)."""
    n = table_size()
    temas_block = _temas_block()
    mesa_block = _mesa_block(n)
    instr_block = _instrumentos_block()
    plat_block = _plataforma_block()
    juiz_block = _juiz_block()
    errors = (temas_block["errors"] + mesa_block["errors"] + instr_block["errors"]
              + plat_block.get("errors", []) + juiz_block.get("errors", []))
    warnings = temas_block["warnings"] + mesa_block["warnings"] + instr_block["warnings"]
    return {
        "table_size": n,
        "temas": temas_block,
        "composicao_mesa": mesa_block,
        "formularios": instr_block,
        "plataforma": plat_block,
        "juiz": juiz_block,
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def summary_line() -> str:
    """Uma linha curta para o log de inicialização."""
    c = build_catalog()
    t, m, fo = c["temas"], c["composicao_mesa"], c["formularios"]
    return (
        f"[catálogo] {t['areas_count']} áreas / {t['subtemas_count']} subtemas · "
        f"{m['themes_count']} temas de mesa / {m['personas_total']} personas · "
        f"{fo['forms_count']} formulários / {fo['items_total']} itens · "
        f"mesa={c['table_size']} · {len(c['errors'])} erro(s), {len(c['warnings'])} aviso(s)"
    )
