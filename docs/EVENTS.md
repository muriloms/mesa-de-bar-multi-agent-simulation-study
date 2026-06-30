# Eventos

Cada decisão da sessão vira uma linha em `data/sessions/<sid>/events.jsonl`. Append-only. JSON por linha.

## Schema base

Toda linha segue:

```json
{
  "event_id": "evt_<uuid>",
  "session_id": "<sid>",
  "timestamp": "2025-12-08T14:32:11.847Z",
  "elapsed_ms": 12847,
  "type": "<event_type>",
  "actor": "user | ai_<id> | system",
  "phase": "warmup | discussion | convergence | closing | null",
  "round": 3,
  "payload": { ... }
}
```

`elapsed_ms` é o tempo desde `session.created`. Útil pra plotar timeline.

## Tipos de evento

### Ciclo de vida

#### `session.created`
Sessão criada. Primeira linha do arquivo.
```json
"payload": {
  "user_name": "Mateus",
  "topic": "Cidade do futuro",
  "num_personas": 4,
  "personas": ["Sócrates", "Tesla", "Marie Curie", "Steve Jobs"],
  "llm_provider": "google",
  "llm_model": "gemini-1.5-flash",
  "seed": 1827361,
  "language": "pt"
}
```

#### `phase.entered`
Entrou em uma fase nova.
```json
"phase": "warmup",
"payload": { "phase": "warmup", "from": null }
```

#### `phase.changed`
Transição entre fases (warmup→discussion→convergence→closing).
```json
"payload": { "from": "discussion", "to": "convergence" }
```

#### `round.started`
Nova rodada começou (dentro de uma fase).
```json
"payload": {
  "global_round": 3,
  "phase_round": 2,
  "phase_total_rounds": 4,
  "bidding_enabled": true,
  "bid_multiplier": 1.0
}
```

### Propostas e votação

#### `round.ai_sampling`
Amostragem aleatória de quais IAs participam da rodada.
```json
"payload": {
  "sampled_ids": [2, 3, 5],
  "sampled_names": ["Sócrates", "Tesla", "Steve Jobs"],
  "total_ais": 4,
  "user_passed": false  // true se humano usou Passar
}
```

#### `round.proposal_submitted`
Uma proposta entrou na rodada. Um evento por proposta (humano + IAs).
```json
"actor": "ai_2",  // ou "user"
"payload": {
  "player_id": 2,
  "idea_text": "...",
  "bid_amount_raw": 50.0,        // o que a IA ou usuário "queria" apostar
  "bid_amount_effective": 100.0, // depois do bid_multiplier
  "bid_multiplier": 2.0,
  "drinks": 1,                   // só pra IAs
  "effective_temperature": 0.8   // só pra IAs
}
```

#### `phase.changed` (bidding → voting)
Quando todas as propostas chegaram.
```json
"payload": { "from": "bidding", "to": "voting" }
```

#### `vote.resolved`
Vencedor da rodada determinado.
```json
"payload": {
  "winner_id": 2,
  "winner_name": "Sócrates",
  "pot": 175.0,
  "winning_bid": 100.0,
  "drink_awarded": true,
  "balances": {1: 950, 2: 1075, ...},
  "drinks": {1: 0, 2: 2, ...}
}
```

#### `vote.delegated`
Quando o usuário delegou ao Garçom.
```json
"payload": {
  "winner_id": 3,
  "tiebreak": false,         // true se apostas próximas (10%) e modo ativo
  "prompt_used": "waiter_choose"  // ou "waiter_tiebreak"
}
```

### Drinks e memória

#### `drink.awarded`
Vencedor ganhou drink.
```json
"payload": {
  "winner_id": 2,
  "winner_name": "Sócrates",
  "drinks_total": 3,
  "next_temperature": 1.0
}
```

#### `persona.reflected`
Reflexão privada antes de propor (modo `reflected_summary`).
```json
"actor": "ai_2",
"payload": {
  "player_id": 2,
  "memo": "A mesa está convergindo demais. Vou puxar pra um ângulo crítico.",
  "memo_chars": 67
}
```

### Garçom

#### `waiter.summary`
Resumo parcial pedido pelo botão.
```json
"payload": {
  "summary": "...",
  "summary_length": 420
}
```

#### `waiter.provocation`
Provocação pedida pelo botão.
```json
"payload": { "text": "Por que ninguém questionou o pressuposto X?" }
```

### Ações do humano

#### `user.passed`
Humano passou a vez.
```json
"actor": "user",
"payload": {
  "player_id": 1,
  "justification": "Quero ouvir mais antes de propor.",
  "justification_chars": 36
}
```

#### `user.endorsed`
Humano endossou proposta.
```json
"actor": "user",
"payload": {
  "endorser_id": 1,
  "target_player_id": 2,
  "target_name": "Sócrates",
  "justification": "Concordo, e quero adicionar...",
  "justification_chars": 31
}
```

#### `input.keystroke_log`
Telemetria de digitação (capturada se `protocol.telemetry.capture_keystrokes`).
```json
"actor": "user",
"payload": {
  "kind": "bid",  // bid | pass | endorse
  "metrics": {
    "time_to_first_keystroke_ms": 2340,
    "total_keystrokes": 187,
    "total_edits": 23,
    "total_pastes": 0,
    "longest_pause_ms": 4200,
    "total_duration_ms": 38000,
    "final_length": 142
  },
  "events": [
    {"t": 0, "k": "M"},
    {"t": 80, "k": "i"},
    {"t": 156, "k": "n"},
    {"t": 1200, "k": "Backspace"},
    ...
    {"t": 12000, "k": "<paste>", "n": 47}  // colagem; texto não capturado
  ]
}
```

### Encerramento

#### `session.summary_generated`
Síntese final do Dono pronta.
```json
"phase": "closing",
"payload": {
  "summary_length": 890,
  "owner_bias": "neutral",
  "had_summary": true
}
```

#### `lab.structured`
Estrutura pro Lab gerada.
```json
"phase": "closing",
"payload": { "title": "Cidade vertical biotech 2050" }
```

### Instrumentos

#### `instrument.submitted`
Respostas a um instrumento gravadas.
```json
"actor": "user",
"payload": {
  "instrument_id": "pre_session_cocreation_v1",
  "instrument_version": "1.0.0",
  "moment": "pre_session",
  "duration_ms": 222000,
  "responses_count": 10,
  "missing_required": []
}
```

## Análise

Pra carregar todos os eventos de uma sessão em pandas:

```python
import json, pandas as pd
events = [json.loads(l) for l in open("data/sessions/<sid>/events.jsonl")]
df = pd.DataFrame(events)
print(df["type"].value_counts())
```

Pra cruzar com LLM calls e analisar custo por evento:

```python
calls = [json.loads(l) for l in open("data/sessions/<sid>/llm_calls.jsonl")]
calls_df = pd.DataFrame(calls)
# join por timestamp ou por session_id+round+actor
```
