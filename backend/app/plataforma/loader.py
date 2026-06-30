"""Carregador da configuração da plataforma (research_settings/plataforma.yaml).

Define funcionalidades e dinâmicas: fonte da chave de API, modo de escolha de
tema e de composição, nº de rodadas, dinâmica da melhor ideia, etc. Validado
via Pydantic; se o arquivo não existir, usa padrões seguros.
"""
from pathlib import Path
from typing import Literal
import yaml
from pydantic import BaseModel, Field

from core import config
from core.exceptions import MesaDeBarError


class ApiCfg(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    user_provides_key: bool = True
    key: str = ""


class ThemeCfg(BaseModel):
    mode: Literal["random", "choose", "write"] = "random"


class TableCfg(BaseModel):
    mode: Literal["random", "choose"] = "random"
    size: int = Field(default=4, ge=1)


class DynamicsCfg(BaseModel):
    best_idea: Literal["player_decides", "judge", "player"] = "player_decides"
    judge_criterion: Literal["originalidade", "viabilidade", "interesse", "composto"] = "originalidade"
    judge_blind_to_source: bool = True
    source_blind_on_choice: bool = True
    owner_bias: Literal["neutral", "pro_human"] = "neutral"


class FormsCfg(BaseModel):
    pre_session_enabled: bool = True
    post_session_enabled: bool = True


class Plataforma(BaseModel):
    mode: Literal["live", "simulation"] = "live"
    api: ApiCfg = Field(default_factory=ApiCfg)
    theme: ThemeCfg = Field(default_factory=ThemeCfg)
    table: TableCfg = Field(default_factory=TableCfg)
    rounds: int = Field(default=4, ge=1)
    dynamics: DynamicsCfg = Field(default_factory=DynamicsCfg)
    forms: FormsCfg = Field(default_factory=FormsCfg)


def plataforma_file() -> Path:
    return config.RESEARCH_DIR / "plataforma.yaml"


def load_plataforma() -> Plataforma:
    """Lê e valida plataforma.yaml. Sem o arquivo, retorna padrões."""
    path = plataforma_file()
    if not path.exists():
        return Plataforma()
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise MesaDeBarError(f"Erro ao parsear {path}: {e}")
    if not isinstance(data, dict):
        raise MesaDeBarError(f"Conteúdo de {path} não é um mapping YAML")
    return Plataforma(**data)


# Mapeia best_idea -> quem_avanca do protocolo
BEST_IDEA_TO_QUEM_AVANCA = {
    "judge": "juiz_ia",
    "player": "jogador",
    "player_decides": "jogador",  # interativo: jogador decide ao divergir
}
