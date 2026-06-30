"""Configuração central — paths e defaults.

Em Docker, os caminhos vêm das env vars MDB_* setadas pelo docker-compose.
Em dev local sem Docker, o fallback resolve a partir da raiz do repo.

IMPORTANTE: usamos `_path_from_env` em vez de `os.getenv(var, default)`
porque o segundo argumento de getenv é AVALIADO EAGERLY mesmo quando a
env var existe — e em Docker o cálculo de `_repo_root()` falha (não há
3 níveis de parents acima de /app/core/config.py).
"""
from pathlib import Path
import os


def _repo_root() -> Path:
    """Raiz do repo. Usado só em dev local; em Docker, env vars cobrem tudo."""
    p = Path(__file__).resolve()
    # backend/app/core/config.py → mesa-de-bar/ (parents[3]).
    # Em Docker, /app/core/config.py não tem 3 parents acima → fallback CWD.
    parents = p.parents
    if len(parents) > 3:
        return parents[3]
    return Path.cwd()


def _path_from_env(env_var: str, default_subdir: str) -> Path:
    val = os.getenv(env_var)
    if val:
        return Path(val)
    return _repo_root() / default_subdir


DATA_DIR = _path_from_env("MDB_DATA_DIR", "data")
SESSIONS_DIR = DATA_DIR / "sessions"

# Pasta única com as definições de pesquisa (temas, composição da mesa,
# formulários, juiz, e o arquivo de plataforma). Override por env.
RESEARCH_DIR = _path_from_env("MDB_RESEARCH_DIR", "research_settings")

# Quantas personas sentam à mesa (sorteadas do pool do tema). Override por env.
try:
    TABLE_SIZE = max(1, int(os.getenv("MDB_TABLE_SIZE", "4")))
except ValueError:
    TABLE_SIZE = 4

PROTOCOLS_DIR = _path_from_env("MDB_PROTOCOLS_DIR", "core/protocols")
PROMPTS_DIR = _path_from_env("MDB_PROMPTS_DIR", "core/prompts")
INSTRUMENTS_DIR = _path_from_env("MDB_INSTRUMENTS_DIR", "research_settings/instruments")
CONFIG_DIR = _path_from_env("MDB_CONFIG_DIR", "core/config")
PRICING_FILE = CONFIG_DIR / "pricing.yaml"
