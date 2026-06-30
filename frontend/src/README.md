# Frontend src/

Estrutura prevista nas próximas fases:

- `pages/` — uma página por etapa do fluxo do sujeito (Welcome, Consent,
  PreQuestionnaire, Setup, Warmup, Table, Convergence, Closing,
  PostQuestionnaire, Lab, Export).
- `components/Persona/` — cards e editores de persona (atual já tem PersonaCard,
  PersonaEditorModal, LoadTeamModal).
- `components/Game/` — mesa, assento, votação, área de aposta (atual tem
  PlayerSeat, PlayerDisplay, UserInput, VotingPanel, HistoryPanel).
- `components/Waiter/` — render genérico das intervenções do Garçom (Fase 2).
- `components/Instruments/` — Likert, free-text, NASA-TLX, etc (Fase 3).
- `components/Config/` — modais de configuração (atual tem LlmConfigModal).
- `components/Common/` — banners, overlays, indicadores.
- `hooks/` — useSession, usePhase, useTelemetry, useTimer (Fase 1+).
- `state/` — Context API para estado global (Fase 2 ou antes, conforme
  o `App.jsx` ficar grande demais).
- `services/` — `api.js` (já existe), `telemetry.js` (Fase 3), `markdown.js`
  com sanitização (Fase 1).

## Status (Fase 0)

Pastas criadas vazias, componentes/páginas atuais permanecem em
`components/` e `pages/` na raiz de `src/`. A migração para a estrutura
agrupada acontece nas fases que forem mexer naqueles componentes.
