"""Renderiza um prompt nomeado com contexto Jinja2."""
from typing import Tuple

from jinja2 import Environment, BaseLoader

from . import registry

# autoescape=False porque a saída é prompt para LLM (não HTML)
_env = Environment(
    loader=BaseLoader(),
    autoescape=False,
    trim_blocks=False,
    lstrip_blocks=False,
    keep_trailing_newline=False,
)


def render(prompt_id: str, version: str = "v1", language: str = "pt", **context) -> Tuple[str, registry.PromptInfo]:
    """Renderiza e devolve (texto_renderizado, PromptInfo).

    `language` controla qual variante do prompt usar — fallback pra PT
    se não houver tradução pro idioma pedido.
    """
    info = registry.get(prompt_id, version, language=language)
    template = _env.from_string(info.content)
    return template.render(**context), info
