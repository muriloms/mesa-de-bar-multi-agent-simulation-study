# persistence/

Toda interação com o sistema de arquivos vive aqui. Nenhum outro módulo deve
abrir arquivos diretamente — sempre via funções deste módulo.

Por que? Porque garante que toda escrita passe pelos lugares certos com os
formatos certos. Em particular, `events.jsonl` e `llm_calls.jsonl` são
**append-only** e a única forma correta de escrever é usar `event_log.append`
e `llm_log.append` daqui.

## Status

- **Fase 1** — Módulos: `paths.py`, `session_store.py`, `event_log.py`,
  `llm_log.py`, `transcript.py`.
- **Fase 4** — `export_packager.py` para montar o ZIP.
