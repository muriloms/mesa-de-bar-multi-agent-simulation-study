# Prompts

Templates Jinja2 versionados. Cada subpasta é um **papel** (proposal, garçom,
dono do bar, etc), e cada arquivo é uma **versão** desse papel (`v1.jinja2`,
`v2.jinja2`, ...).

## Por que versionar?

Reprodutibilidade. Quando uma chamada LLM é feita, registramos em
`data/sessions/<id>/llm_calls.jsonl` o `prompt_id`, a `prompt_version` e o
`prompt_hash` (sha256). Isso permite que sessões antigas sejam comparáveis
mesmo se o prompt mudar depois.

## Subpastas

- `proposal/` — prompt principal: IA gera ideia + aposta
- `persona_mind_update/` — atualiza estado interno da IA entre rodadas (Fase 2)
- `persona_generation/` — gera time de personas a partir de um tema
- `warmup_intro/` — Ato 1: posicionamento inicial sem aposta
- `waiter_choose/` — voto delegado ao Garçom
- `waiter_summarize/` — síntese parcial entre rodadas (Fase 2)
- `waiter_provoke/` — Garçom provoca propostas tímidas (Fase 2)
- `waiter_tiebreak/` — Garçom força defesa em empate (Fase 2)
- `owner_summary_*/` — síntese final do Dono do Bar com diferentes vieses
- `lab_structure/` — converte síntese em proposta de projeto estruturada

## Status

- **Fase 1** — Migração dos prompts hardcoded em `client_gemini.py` e
  `client_openAI.py` para arquivos versionados aqui.
- **Fase 2** — Adição dos prompts novos das mecânicas dos 4 atos.

Veja `docs/PROMPT_GUIDE.md` (Fase 5) para convenções de naming e variáveis.
