"""Carregador de protocolos YAML."""
from typing import List
import yaml

from core import config
from core.exceptions import ProtocolError
from domain.protocol import Protocol


def load_protocol(name: str = "default") -> Protocol:
    """Carrega `protocols/<name>.yaml` e devolve um Protocol validado."""
    path = config.PROTOCOLS_DIR / f"{name}.yaml"
    if not path.exists():
        raise ProtocolError(f"Protocolo '{name}' não encontrado em {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise ProtocolError(f"Erro ao parsear {path}: {e}")
    if not isinstance(data, dict):
        raise ProtocolError(f"Conteúdo de {path} não é um mapping YAML")
    return Protocol(**data)


def list_protocols() -> List[str]:
    """Lista os ids dos protocolos disponíveis (filenames sem extensão)."""
    if not config.PROTOCOLS_DIR.exists():
        return []
    return sorted(
        p.stem for p in config.PROTOCOLS_DIR.glob("*.yaml")
        if not p.name.startswith("_")
    )


def list_protocols_with_metadata() -> List[dict]:
    """Lista protocolos com metadados básicos (id, version, description, language)."""
    out = []
    for name in list_protocols():
        try:
            p = load_protocol(name)
            out.append({
                "id": p.id,
                "version": p.version,
                "description": p.description.strip() if p.description else "",
                "language": p.language,
            })
        except Exception as e:
            # Protocolo malformado — sinaliza pra UI
            out.append({
                "id": name,
                "version": "?",
                "description": f"⚠ Erro ao carregar: {e}",
                "language": "pt",
                "error": str(e),
            })
    return out
