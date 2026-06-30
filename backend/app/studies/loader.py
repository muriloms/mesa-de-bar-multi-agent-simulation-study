"""Carregador de estudos YAML (studies/<id>.yaml)."""
from pathlib import Path
from typing import List
import os
import yaml

from core import config
from core.exceptions import MesaDeBarError
from domain.study import Study


def _studies_dir() -> Path:
    env = os.getenv("MDB_STUDIES_DIR")
    if env:
        return Path(env)
    return config.PROTOCOLS_DIR.parent / "studies"


def load_study(study_id: str) -> Study:
    path = _studies_dir() / f"{study_id}.yaml"
    if not path.exists():
        raise MesaDeBarError(f"Estudo '{study_id}' não encontrado em {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise MesaDeBarError(f"Erro ao parsear {path}: {e}")
    if not isinstance(data, dict):
        raise MesaDeBarError(f"Conteúdo de {path} não é um mapping YAML")
    return Study(**data)


def list_studies() -> List[dict]:
    d = _studies_dir()
    if not d.exists():
        return []
    out = []
    for f in sorted(d.glob("*.yaml")):
        if f.name.startswith("_"):
            continue
        try:
            s = load_study(f.stem)
            out.append({
                "id": s.id, "title": s.title, "description": s.description.strip(),
                "arms": s.arms, "num_topics": len(s.topics),
                "compositions": s.compositions, "blind_condition": s.blind_condition,
            })
        except Exception as e:
            out.append({"id": f.stem, "title": "?", "error": str(e)})
    return out
