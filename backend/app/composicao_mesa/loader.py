"""Carregador e sorteio de composições de mesa (tema → pool de personas).

Cada arquivo `composicao_mesa/<tema>.yaml` (na raiz do repo) traz um tema
(ex.: filosofos, escritores) com um POOL de personas. No jogo, sorteia-se
um tema e, do pool dele, N personas (4 por padrão) para sentar à mesa.

Reaproveita o modelo `domain.composition.Composition` (mesmo schema).
"""
from pathlib import Path
from typing import List, Optional
import os
import random as _random
import yaml

from core import config
from core.exceptions import MesaDeBarError
from domain.composition import Composition


def _mesa_dir() -> Path:
    env = os.getenv("MDB_COMPOSICAO_MESA_DIR")
    if env:
        return Path(env)
    return config.RESEARCH_DIR / "composicao_mesa"


def mesa_dir() -> Path:
    """Diretório público das composições de mesa (para inspeção)."""
    return _mesa_dir()


def load_table(theme_id: str) -> Composition:
    """Carrega um tema de composição por id (nome do arquivo sem extensão)."""
    path = _mesa_dir() / f"{theme_id}.yaml"
    if not path.exists():
        raise MesaDeBarError(f"Composição de mesa '{theme_id}' não encontrada em {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise MesaDeBarError(f"Erro ao parsear {path}: {e}")
    if not isinstance(data, dict):
        raise MesaDeBarError(f"Conteúdo de {path} não é um mapping YAML")
    return Composition(**data)


def list_tables() -> List[Composition]:
    """Lista todos os temas de composição disponíveis."""
    d = _mesa_dir()
    if not d.exists():
        return []
    out: List[Composition] = []
    for f in sorted(d.glob("*.yaml")):
        if f.name.startswith("_"):
            continue
        try:
            out.append(load_table(f.stem))
        except Exception:
            continue  # ignora arquivo malformado
    return out


def draw_table(n_personas: int = 4, rng: Optional[_random.Random] = None) -> dict:
    """Sorteia um TEMA de composição e N personas do pool dele."""
    r = rng or _random
    tables = list_tables()
    if not tables:
        raise MesaDeBarError("Nenhuma composição de mesa disponível para sorteio")
    comp = r.choice(tables)
    pool = list(comp.personas)
    chosen = pool if len(pool) <= n_personas else r.sample(pool, n_personas)
    return {
        "theme_id": comp.id,
        "theme_title": comp.title,
        "personas": chosen,
    }
