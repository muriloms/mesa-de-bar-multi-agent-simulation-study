"""Carregador de instrumentos YAML."""
from typing import List
import yaml

from core import config
from core.exceptions import MesaDeBarError
from domain.instrument import Instrument


class InstrumentNotFoundError(MesaDeBarError):
    pass


def load_instrument(instrument_id: str) -> Instrument:
    """Carrega `instruments/<id>.yaml` e valida via Pydantic."""
    path = config.INSTRUMENTS_DIR / f"{instrument_id}.yaml"
    if not path.exists():
        raise InstrumentNotFoundError(
            f"Instrumento '{instrument_id}' não encontrado em {path}"
        )
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise MesaDeBarError(f"Erro ao parsear {path}: {e}")
    if not isinstance(data, dict):
        raise MesaDeBarError(f"Conteúdo de {path} não é um mapping YAML")
    return Instrument(**data)


def list_instruments() -> List[str]:
    """Lista os ids dos instrumentos disponíveis."""
    if not config.INSTRUMENTS_DIR.exists():
        return []
    return sorted(
        p.stem for p in config.INSTRUMENTS_DIR.glob("*.yaml")
        if not p.name.startswith("_")
    )
