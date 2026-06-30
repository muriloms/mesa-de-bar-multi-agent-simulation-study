# Fase B — Camada experimental (runner + CoT + composições)

Transforma as manipulações da Fase A num experimento rodável: atribuição
balanceada de condições, CoT como variável, e composição de mesa como fator.

## B1 — Runner (randomização de braços)
- **Estudo** (`studies/<id>.yaml`): lista braços (protocolos), banco de tópicos
  padronizado e composições a balancear.
- **Atribuição balanceada e aninhada** (round-robin pelo menos-preenchido):
  braço → tópico (dentro do braço) → composição (dentro de braço×tópico).
  Empate resolvido pela ordem listada (reprodutível).
- **Ledger append-only** em `data/studies/<id>/assignments.jsonl` — fonte de
  verdade da contagem, auditável.
- **Single-blind**: o participante não escolhe nem vê a condição; ela vai pro
  manifest (`manifest.study`) e pro evento `study.assigned`, não pro GameState.
- Endpoints: `GET /api/studies`, `POST /api/study/start`,
  `GET /api/studies/<id>/balance`.

## B2 — CoT como manipulação
- `reasoning_mode: direct | cot` no protocolo. Em `cot`, a persona raciocina
  antes de propor; o raciocínio é capturado no evento `round.proposal_submitted`
  (campo `reasoning`) mas NUNCA exibido na mesa.
- Gancho com a hipótese de homogeneização/fixação (H2). Protocolo `default_cot`
  é o braço com CoT ligado.

## B3 — Composição como fator + pessoas comuns
- Composições já eram logadas; agora são um fator balanceável do estudo.
- Nova composição `pessoas_comuns_brasil` (professora, entregador, comerciante,
  técnica de enfermagem) — mesa-controle pra contrastar com figuras notáveis
  (efeito de fixação/antropomorfização).

## Tópicos
Banco padronizado dentro de cada estudo (comparabilidade entre braços). Sessão
livre (sandbox) continua disponível no setup normal, fora de qualquer estudo.

## Estudos inclusos
- `main`: model-led × human-led × (notável vs comum), 6 tópicos. 2×2×6 células.
- `cot_homogeneizacao`: default vs default_cot, composição fixa (comum), 6 tópicos.

## Frontend
Setup ganhou um toggle **Sessão livre / Estudo**. No modo estudo: nome +
seletor de estudo + começar; o sistema atribui a condição (cego ao participante).

## Eventos novos
`study.assigned` (braço/tópico/composição/célula). `round.proposal_submitted`
agora inclui `reasoning_mode` e `reasoning`.

## Pendente (Fase C/D)
- Fase C: avaliação automática (originalidade/flexibilidade por embeddings) +
  export pro painel CAT. `stats.py` ainda no esquema da v1.
- Fase D: painel CAT humano cego + validação juiz-IA vs humano.
