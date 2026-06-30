"""Carregador de composições YAML."""
from typing import List, Optional
import yaml

from core import config
from core.exceptions import MesaDeBarError
from domain.composition import Composition


# Adiciona compositions dir no config caso não exista
def _compositions_dir():
    from pathlib import Path
    import os
    env = os.getenv("MDB_COMPOSITIONS_DIR")
    if env:
        return Path(env)
    return config.PROTOCOLS_DIR.parent / "compositions"


def load_composition(comp_id: str) -> Composition:
    """Carrega `compositions/<id>.yaml` e valida via Pydantic."""
    path = _compositions_dir() / f"{comp_id}.yaml"
    if not path.exists():
        raise MesaDeBarError(f"Composição '{comp_id}' não encontrada em {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise MesaDeBarError(f"Erro ao parsear {path}: {e}")
    if not isinstance(data, dict):
        raise MesaDeBarError(f"Conteúdo de {path} não é um mapping YAML")
    return Composition(**data)


def list_compositions() -> List[Composition]:
    """Lista todas as composições disponíveis."""
    d = _compositions_dir()
    if not d.exists():
        return []
    out = []
    for f in sorted(d.glob("*.yaml")):
        if f.name.startswith("_"):
            continue
        try:
            out.append(load_composition(f.stem))
        except Exception:
            continue  # ignora composição malformada
    return out
