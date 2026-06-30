# prompts/ (módulo Python)

**Não confundir** com `prompts/` na raiz do repo, que contém os templates
Jinja2. Este módulo Python contém o **registry** (carrega + indexa + calcula
hash dos templates) e o **renderer** (Jinja2).

## Status

- **Fase 1** — `registry.py` indexa todos os prompts de `prompts/` (raiz)
  com sha256 calculado, e `renderer.py` renderiza um prompt nomeado com
  contexto. Toda chamada LLM vai logar `prompt_id`, `prompt_version` e
  `prompt_hash`.
