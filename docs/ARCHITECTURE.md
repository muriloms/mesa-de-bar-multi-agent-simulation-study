# Arquitetura

## Visão de alto nível

```
┌──────────────────────────────────────────────────────────────┐
│  Frontend (React + Vite)            Backend (FastAPI)        │
│  ─────────────────────              ──────────────────       │
│                                                              │
│  SetupScreen ─┐                     /api/setup ──────┐       │
│               │                                      │       │
│               ↓                                      ↓       │
│  InstrumentForm (pré)               game_service.create_     │
│               │                                      │       │
│               ↓                                      ↓       │
│  TableScreen ─┐                     /api/bid                 │
│   ├ ActIndicator                    /api/pass                │
│   ├ ConversationPanel               /api/endorse             │
│   ├ UserInput ──────── telemetria → /api/telemetry           │
│   ├ WaiterBar                       /api/delegate-vote       │
│   ├ VotingPanel                     /api/waiter/summary      │
│   └ CostsDashboard ←── 3s reload ── /api/sessions/{id}/costs │
│               │                                              │
│               ↓                                              │
│  InstrumentForm (pós)               /api/instruments/...     │
│               │                                              │
│               ↓                                              │
│  EndGameSummary ────── ZIP ──────── /api/sessions/{id}/export│
│  LabScreen                          /api/lab/process         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                          │
                          ↓
              ┌───────────────────────┐
              │  data/sessions/<id>/  │
              │   manifest.json       │
              │   protocol.json       │
              │   events.jsonl        │
              │   llm_calls.jsonl     │
              │   transcript.json/md  │
              │   final_idea.json     │
              │   instruments/*.json  │
              └───────────────────────┘
```

## Princípios de design

**Sem banco de dados.** Cada sessão vive em uma pasta. Append-only para `events.jsonl` e `llm_calls.jsonl`. Snapshot para `transcript.json`. Isso simplifica drasticamente: pesquisador faz `cd data/sessions && ls`, pega o que quer, analisa em pandas. Zero migrações, zero ORM.

**Protocolo é a unidade científica.** Um arquivo YAML em `protocols/` define todas as variáveis manipuláveis de uma sessão: fases, drinks, memória, garçom, dono, instrumentos, idioma, e flags experimentais (`blind_personas`, `solo_baseline`). Pra rodar um estudo comparativo, basta criar dois protocolos e alternar.

**Prompts versionados e hashados.** Todo prompt em `prompts/<id>/<version>.jinja2`. Cada chamada LLM grava `prompt_id`, `prompt_version`, `prompt_hash` (sha256 do conteúdo na hora). Se você editar o prompt depois, sessões antigas continuam comparáveis pelo hash.

**Reprodutibilidade.** Cada sessão tem `seed` no manifest. RNG (sample de IAs participando, etc) usa esse seed. LLM com seed quando o provedor suporta (OpenAI sim, Gemini ainda não respeita totalmente). O snapshot dos prompts ativos e o protocolo congelado ficam no manifest.

**Tudo logado.** Eventos cobrem desde `session.created` até `lab.structured`. LLM calls cobrem prompt completo, resposta crua, parseamento, latência, tokens. Custo é calculado on-the-fly por `services/costs.py` lendo `config/pricing.yaml`.

## Backend — camadas

```
backend/app/
├── core/              # Helpers — config, ids, time, exceções
├── domain/            # Modelos Pydantic — sem dependência de IO
│   ├── persona.py
│   ├── player.py
│   ├── round.py
│   ├── session.py     # GameState
│   ├── protocol.py    # Protocol — TODOS os campos configuráveis
│   ├── instrument.py
│   ├── event.py
│   ├── llm_call.py
│   └── ...
├── persistence/       # IO — leitura/escrita de arquivos
│   ├── paths.py
│   ├── session_store.py
│   ├── event_log.py   # append-only events.jsonl
│   ├── llm_log.py     # append-only llm_calls.jsonl
│   └── ...
├── prompts/
│   ├── registry.py    # detecta arquivos, calcula sha256
│   └── renderer.py    # Jinja2 com fallback de idioma
├── protocols/
│   └── loader.py
├── instruments/
│   └── loader.py
├── llm/
│   ├── manager.py     # wrapper sobre google/openai
│   ├── tasks.py       # generate_proposal, choose_best_idea, etc.
│   └── parsers.py     # JSON parser robusto
├── game/
│   ├── phase_engine.py  # máquina de estado dos 4 atos
│   └── randomization.py # SessionRNG
├── services/          # Orquestração
│   ├── game_service.py    # core
│   ├── instrument_service.py
│   ├── costs.py
│   └── export.py
└── routes/
    └── game_routes.py
```

**Domain** são modelos puros (Pydantic). **Persistence** sabe ler/escrever arquivos. **Services** orquestra (regras de negócio). **Routes** apenas adapta HTTP↔services. Esta separação permite testar tudo do domain pra cima sem subir API.

## Frontend — fluxo de telas

1. **SetupScreen** — usuário escolhe nome, tópico, personas, protocolo, idioma. POST `/api/setup`. Recebe `GameState` com `pre_session_instrument` definido.
2. **InstrumentForm (pré)** — se houver, carrega via `GET /api/instruments/{id}`. Usuário responde, POST `/api/sessions/{sid}/instruments/{iid}/responses`.
3. **TableScreen** — mostra mesa, ouve eventos, dispara apostas/passa/endossa. Telemetria de digitação fire-and-forget pra `/api/telemetry`.
4. **InstrumentForm (pós)** — se houver, depois de `/api/end`.
5. **EndGameSummary** — síntese do Dono. CTAs: enviar ao Lab ou baixar ZIP.
6. **LabScreen** — ideia estruturada (título, problem, solução, features).

## Fluxo de uma rodada

```
[user submits bid via UserInput]
        │
        ↓ POST /api/bid
        │
process_user_bid:
  ├ aplica multiplicador da fase à aposta
  ├ emite round.proposal_submitted (user)
  ├ sample N IAs participantes (RNG seedado)
  ├ pra cada IA participante:
  │    ├ se memory.mode == reflected_summary:
  │    │    └ chama reflect_persona → grava em state.persona_memos
  │    │      e emite persona.reflected
  │    └ chama generate_proposal com:
  │        - persona REAL (mesmo em blind mode)
  │        - memo refletido
  │        - temperatura efetiva (base + drinks * step)
  │        - language do protocolo
  ├ adiciona propostas a state.current_proposals
  └ state.game_phase = "voting"
        │
        ↓ resposta retorna ao frontend
        │
VotingPanel renderiza
        │
[user vota OU clica delegar]
        │
        ↓ POST /api/vote ou /api/delegate-vote
        │
finalize_round:
  ├ se waiter ativo + apostas próximas: usa waiter_tiebreak
  ├ resolve apostas (pot pro vencedor)
  ├ se aposta habilitada: vencedor ganha drink
  ├ adiciona vencedor à state.conversation
  ├ engine.advance_round() → atualiza fase/rodada
  └ se for última: phase=closing, aguarda Encerrar
```

## Decisões importantes

**`pre_session_instrument` vai no GameState.** Em vez de o frontend buscar o protocolo separadamente, o backend já popula o id do instrumento na resposta de `/setup`. UI fica burra: "se tem id, mostra; senão, pula".

**Blind personas mantém persona real internamente.** Em `blind_personas: true`, o backend mantém um dict `session_internal_personas[sid][player_id] → AIPersonaSetup` com a persona real. Helper `_player_with_real_persona()` substitui pra IA "ser ela mesma" no prompt, mas o frontend só vê "Persona A". Os logs (`events.jsonl`, `llm_calls.jsonl`) gravam tanto o nome exibido quanto o real, permitindo análise científica.

**Auto-recuperação no Lab.** Se o usuário clica "Enviar ao Lab" sem ter clicado "Encerrar", `process_summary_for_lab()` chama `end_game_session()` automaticamente. Não confia que o frontend tenha disparado as ações na ordem correta.

**Custos calculados sob demanda, não cacheados.** `services/costs.py` lê `llm_calls.jsonl` toda vez. Permite editar `config/pricing.yaml` no host (mounted read-only) e ver preços atualizados sem reiniciar backend. O modal recarrega a cada 3s.
