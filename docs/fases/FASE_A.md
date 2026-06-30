# Fase A — Novo loop de rodada (v2)

Refactor do loop de rodada de "apostar → votar vencedor" (v1) para o ciclo
científico da v2. Sem economia, sem drinks, temperatura fixa.

## Novo loop de rodada
1. **Propor** — o jogador escreve a ideia (cego às ideias de IA da rodada);
   todas as personas IA propõem em paralelo (sem subconjunto sorteado).
2. **Escolher** — todas as ideias são reveladas ANÔNIMAS; o jogador escolhe a melhor.
3. **Juiz** — o Juiz IA (antigo Garçom) escolhe a melhor, cego à autoria e à
   escolha do jogador, por um critério explícito (default: originalidade).
4. **Revelar** — autoria + as duas escolhas + comparação (match/mismatch).
   No mismatch, o jogador decide se concorda com o juiz.
5. **Avançar** — a ideia que segue pra mesa é definida por `quem_avanca`
   (`juiz_ia` | `jogador`). A conversa = trajetória das ideias que avançaram.

Após N rodadas (default 4), o Dono do Bar sintetiza; seguem os instrumentos pós.

## Principais mudanças
- **Fases colapsadas** em `rounds: int` (default 4). `PhaseEngine` virou um
  contador linear de rodadas.
- **Garçom → Juiz**: o `choose_best_idea` virou `judge_choose` (ideias anônimas,
  numeradas, critério explícito). Removidos summarize/provoke/tiebreak.
- **Economia removida**: sem `bid`/saldo/drinks; temperatura fixa do protocolo.
- **Cegueira de fonte** (`source_blind_on_choice`): ideias anônimas na escolha,
  autoria revelada depois (mede viés de fonte). Embaralhadas via SessionRNG.
- **`quem_avanca`** (`juiz_ia` | `jogador`): manipulação experimental central
  (model-led vs human-led), comparada ENTRE sessões.
- **Todas as personas sempre participam** (removido o subconjunto sorteado).

## Novos eventos (events.jsonl)
`round.choices_revealed`, `player.picked`, `judge.picked`,
`round.choices_compared`, `player.judged`, `round.idea_advanced`.
Mantidos: `session.created`, `round.started`, `round.proposal_submitted`,
`persona.reflected`, `phase.entered`, `session.summary_generated`.

## API (backend)
Novos: `POST /api/idea`, `/api/pick`, `/api/advance`. Mantidos: `/api/pass`,
`/api/end`, `/api/telemetry`, `/api/setup`, sessões/instrumentos/catálogos.
Removidos: `/api/bid`, `/api/vote`, `/api/delegate-vote`, `/api/endorse`,
`/api/waiter/*`, `/api/lab/process`.

## Protocolos
`default` (model-led, anônimo, originalidade), `jogador_avanca` (human-led),
`fonte_revelada` (sem cegueira), `blind_personas`, `solo_baseline`.

## Pendente (próximas fases)
- Fase B: composições de mesa e CoT como manipulações; randomização de braços.
- Fase C: avaliação automática (originalidade/flexibilidade por embeddings) +
  export pro painel CAT. As métricas de `stats.py` ainda refletem a v1.
- Fase D: painel CAT humano cego + validação juiz-IA vs humano.
