# domain/

Modelos Pydantic puros — sem I/O, sem regra de negócio. Só estrutura de dados.

Vai substituir `app/models/` quando a Fase 1 estiver completa. Os modelos
atuais ficam em `app/models/game.py` durante a transição.

## Status

- **Fase 1** — Migra os modelos de `app/models/game.py` para arquivos
  separados aqui (`persona.py`, `player.py`, `session.py`, `round.py`,
  `proposal.py`, `event.py`, `llm_call.py`, `protocol.py`, `instrument.py`,
  `consent.py`, `exports.py`).

Quando a Fase 1 terminar, `app/models/` será removido.
