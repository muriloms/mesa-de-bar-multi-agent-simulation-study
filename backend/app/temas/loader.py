"""Carregador e sorteio de temas da mesa (áreas × subtemas).

Dados em `temas/temas.yaml` na raiz do repo (5 áreas × 3 subtemas).
O subtema sorteado é a frase inicial (pauta) que abre a mesa.
"""
from pathlib import Path
from typing import List, Optional
import os
import random as _random
import yaml

from core import config
from core.exceptions import MesaDeBarError


def _temas_dir() -> Path:
    env = os.getenv("MDB_TEMAS_DIR")
    if env:
        return Path(env)
    return config.RESEARCH_DIR / "temas"


def temas_file() -> Path:
    """Caminho público do arquivo de temas (para inspeção)."""
    return _temas_dir() / "temas.yaml"


def load_areas() -> List[dict]:
    """Lê todas as áreas (cada uma com seus subtemas)."""
    path = _temas_dir() / "temas.yaml"
    if not path.exists():
        raise MesaDeBarError(f"Arquivo de temas não encontrado em {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise MesaDeBarError(f"Erro ao parsear {path}: {e}")
    areas = data.get("areas") if isinstance(data, dict) else None
    if not areas:
        raise MesaDeBarError(f"Nenhuma área de tema definida em {path}")
    return areas


def draw_topic(rng: Optional[_random.Random] = None) -> dict:
    """Sorteia uma ÁREA e, dentro dela, um SUBTEMA (a pauta da mesa)."""
    r = rng or _random
    areas = load_areas()
    area = r.choice(areas)
    subtemas = area.get("subtemas") or []
    if not subtemas:
        raise MesaDeBarError(f"Área '{area.get('id')}' não tem subtemas")
    subtema = r.choice(subtemas)
    return {
        "area_id": area.get("id"),
        "area_title": area.get("title"),
        "subtema": subtema,
    }
