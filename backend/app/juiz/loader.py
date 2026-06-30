"""Carregador da persona do Juiz (research_settings/juiz/juiz.yaml)."""
from pathlib import Path
from typing import List, Optional
import yaml
from pydantic import BaseModel, Field

from core import config
from core.exceptions import MesaDeBarError


class Juiz(BaseModel):
    id: str = "juiz_padrao"
    name: str = "O Juiz"
    role: str = "Juiz da mesa"
    description: Optional[str] = None
    criterion: str = "originalidade"
    blind_to_source: bool = True
    instructions: Optional[str] = None


def juiz_file(jid: str = "juiz") -> Path:
    return config.RESEARCH_DIR / "juiz" / f"{jid}.yaml"


def load_juiz(jid: str = "juiz") -> Juiz:
    path = juiz_file(jid)
    if not path.exists():
        # fallback para o juiz padrão se o id pedido não existir
        path = juiz_file("juiz")
    if not path.exists():
        return Juiz()
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise MesaDeBarError(f"Erro ao parsear {path}: {e}")
    return Juiz(**data)
