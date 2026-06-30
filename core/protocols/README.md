# Protocolos

Cada arquivo `*.yaml` aqui representa uma **configuração de estudo** — define
quais atos rodam, quais mecânicas estão ativas, quais questionários são
aplicados, qual modelo de LLM é o padrão, etc.

Quando uma sessão começa, o protocolo escolhido é **copiado** para
`data/sessions/<id>/protocol.json` e **congelado** ali — alterações posteriores
neste diretório não afetam sessões em andamento.

## Status

- **Fase 1** — Carregador de protocolos + protocolo `default.yaml` mínimo.
- **Fase 2** — Suporte completo a todas as mecânicas (4 atos, economia, etc).
- **Fase 5** — Protocolos para manipulações experimentais:
  `blind_personas.yaml`, `blind_proposals.yaml`, `solo_baseline.yaml`,
  `critical_only.yaml`, `passive_waiter.yaml`, `pro_human_summary.yaml`.

Veja `docs/PROTOCOL_GUIDE.md` para o esquema completo (a partir da Fase 5).
