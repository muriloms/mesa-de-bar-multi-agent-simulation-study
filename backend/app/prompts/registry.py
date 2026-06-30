"""Registry de prompts versionados, com suporte a múltiplos idiomas.

Convenção de arquivos:
  - `prompts/<id>/<version>.jinja2`        → versão padrão (PT)
  - `prompts/<id>/<version>.<lang>.jinja2` → tradução para <lang>

Exemplo:
  prompts/proposal/v1.jinja2       (PT, default)
  prompts/proposal/v1.en.jinja2    (EN)

Ao pedir `get(prompt_id, version, language="en")`, o registry tenta
primeiro o arquivo com sufixo do idioma; se não existir, faz fallback
para o arquivo sem sufixo. Isso permite ter PT já completo e ir
adicionando traduções EN gradualmente.
"""
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from core import config
from core.exceptions import PromptNotFoundError


class PromptInfo:
    def __init__(self, prompt_id: str, version: str, language: str, path: Path,
                 content: str, sha256: str):
        self.prompt_id = prompt_id
        self.version = version
        self.language = language
        self.path = path
        self.content = content
        self.sha256 = sha256

    def __repr__(self) -> str:
        return f"PromptInfo({self.prompt_id}/{self.version}/{self.language}, sha={self.sha256[:8]})"


# Cache key: (prompt_id, version, language)
_cache: Optional[Dict[Tuple[str, str, str], PromptInfo]] = None
DEFAULT_LANGUAGE = "pt"


def _parse_filename(stem: str) -> Tuple[str, str]:
    """Extrai (version, language) do nome do arquivo (sem .jinja2).

    "v1" → ("v1", DEFAULT_LANGUAGE)
    "v1.en" → ("v1", "en")
    """
    if "." in stem:
        version, language = stem.rsplit(".", 1)
        return version, language
    return stem, DEFAULT_LANGUAGE


def _scan() -> Dict[Tuple[str, str, str], PromptInfo]:
    result: Dict[Tuple[str, str, str], PromptInfo] = {}
    if not config.PROMPTS_DIR.exists():
        return result
    for sub in config.PROMPTS_DIR.iterdir():
        if not sub.is_dir():
            continue
        prompt_id = sub.name
        for f in sub.glob("*.jinja2"):
            version, language = _parse_filename(f.stem)
            content = f.read_text(encoding="utf-8")
            sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
            result[(prompt_id, version, language)] = PromptInfo(
                prompt_id, version, language, f, content, sha
            )
    return result


def get(prompt_id: str, version: str = "v1", language: str = DEFAULT_LANGUAGE) -> PromptInfo:
    """Busca um prompt em (prompt_id, version, language) com fallback pra PT."""
    global _cache
    if _cache is None:
        _cache = _scan()

    # Primeiro tenta o idioma pedido
    key = (prompt_id, version, language)
    if key in _cache:
        return _cache[key]

    # Fallback: idioma default
    fallback_key = (prompt_id, version, DEFAULT_LANGUAGE)
    if fallback_key in _cache:
        return _cache[fallback_key]

    raise PromptNotFoundError(
        f"Prompt {prompt_id}/{version} (lang={language}) não encontrado em {config.PROMPTS_DIR}"
    )


def all_known() -> List[Tuple[str, str]]:
    """Lista (prompt_id, version) — sem distinguir idioma; pra logging do manifest."""
    global _cache
    if _cache is None:
        _cache = _scan()
    return sorted(set((pid, ver) for (pid, ver, _) in _cache.keys()))


def all_known_with_languages() -> List[Tuple[str, str, str]]:
    """Lista (prompt_id, version, language) — útil pra introspection."""
    global _cache
    if _cache is None:
        _cache = _scan()
    return sorted(_cache.keys())


def clear_cache() -> None:
    global _cache
    _cache = None
