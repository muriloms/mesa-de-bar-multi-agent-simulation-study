# protocols/ (módulo Python)

**Não confundir** com `protocols/` na raiz do repo, que contém os arquivos
YAML. Este módulo Python contém o **carregador** que lê esses YAML, valida
o esquema e devolve um objeto Pydantic.

## Status

- **Fase 1** — `loader.py` com `load_protocol(path) -> Protocol`.
