# game/

Lógica pura do jogo: fases, economia, estado mental das personas, comportamento
do Garçom e do Dono do Bar, randomização com seed.

Sem I/O direto. Quando precisa persistir alguma coisa, chama `persistence/`.
Quando precisa falar com LLM, chama `llm/`.

## Status

- **Fase 2** — Implementação completa:
  - `state.py` — GameState em memória (substitui o dict atual em
    `services/game_service.py`).
  - `phases.py` — warmup / discussion / convergence / closing.
  - `economy.py` — apostas livres, drinks, saldos.
  - `persona_minds.py` — estado interno persistente das IAs entre rodadas.
  - `waiter.py` — Garçom modular (síntese parcial, provocação, empate).
  - `owner.py` — Dono do Bar com viés configurável.
  - `randomization.py` — RNG com seed por sessão (reprodutibilidade).
