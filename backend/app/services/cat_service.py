"""Serviço do painel CAT: materializa o bundle cego, serve itens e coleta notas.

O bundle (itens + chave) é materializado UMA vez por estudo em
data/cat/<study_id>/ — assim os item_ids ficam estáveis entre juízes. As notas
vão pra ratings.jsonl (append-only). A chave (item_id → condição) NUNCA é
servida pro juiz.
"""
import json
from datetime import datetime, timezone
from typing import List, Optional

from core.exceptions import MesaDeBarError
from persistence import paths


def _read_json(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def materialize_bundle(study_id: str, *, include_proposals: bool = False,
                       refresh: bool = False) -> dict:
    """Gera e persiste o bundle cego do estudo (idempotente, salvo refresh)."""
    items_path = paths.cat_items_path(study_id)
    key_path = paths.cat_key_path(study_id)
    if items_path.exists() and key_path.exists() and not refresh:
        return {"items": _read_json(items_path), "key": _read_json(key_path),
                "materialized": False}

    from analysis import dataset
    from analysis.cat_export import build_cat_bundle

    sessions = [s for s in dataset.load_all()
                if s["condition"].get("study_id") == study_id]
    finals = dataset.final_ideas(sessions)
    proposals = dataset.flatten_ideas(sessions) if include_proposals else None
    bundle = build_cat_bundle(finals, proposal_records=proposals)

    paths.cat_dir(study_id).mkdir(parents=True, exist_ok=True)
    items_path.write_text(json.dumps(bundle["items"], ensure_ascii=False, indent=2), encoding="utf-8")
    key_path.write_text(json.dumps(bundle["key"], ensure_ascii=False, indent=2), encoding="utf-8")
    return {"items": bundle["items"], "key": bundle["key"], "materialized": True}


def get_items(study_id: str) -> List[dict]:
    """Itens CEGOS pro juiz (item_id + text apenas)."""
    bundle = materialize_bundle(study_id)
    items = bundle["items"] or []
    # remove eventuais colunas de nota vazias do export; serve só id+texto
    return [{"item_id": it["item_id"], "text": it["text"]} for it in items]


def get_key(study_id: str) -> List[dict]:
    bundle = materialize_bundle(study_id)
    return bundle["key"] or []


_LIKERT = {1, 2, 3, 4, 5}
_DIMS = ("novelty", "quality", "refinement")


def submit_ratings(study_id: str, judge_id: str, ratings: List[dict]) -> dict:
    """Anexa as notas de um juiz (append-only). Valida Likert 1-5."""
    if not judge_id or not str(judge_id).strip():
        raise MesaDeBarError("judge_id é obrigatório.")
    valid_ids = {it["item_id"] for it in get_items(study_id)}
    path = paths.cat_ratings_path(study_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    written = 0
    with path.open("a", encoding="utf-8") as f:
        for r in ratings:
            iid = r.get("item_id")
            if iid not in valid_ids:
                continue
            rec = {"judge_id": str(judge_id).strip(), "item_id": iid, "timestamp": ts}
            for d in _DIMS:
                v = r.get(d)
                rec[d] = int(v) if v in _LIKERT or (isinstance(v, int) and v in _LIKERT) else None
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            written += 1
    return {"stored": True, "count": written, "judge_id": str(judge_id).strip()}


def load_ratings(study_id: str) -> List[dict]:
    path = paths.cat_ratings_path(study_id)
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out
