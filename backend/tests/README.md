# tests/

Suíte de testes do backend. Foco mínimo viável: cobrir as partes onde uma
regressão causa perda silenciosa de dados ou comportamento incorreto que o
pesquisador não percebe.

## Prioridades

- **Fase 1** — Testes para: parser de protocolos YAML, append no event log,
  parser de JSON dos LLMs (com casos de fallback), montagem do manifest,
  resolução de paths por sessão.
- **Fase 2** — Lógica de economia (apostas, drinks, saldos), transições
  entre atos, seleção aleatória reprodutível com seed.
- **Fase 4** — Montagem do export.zip.

## Como rodar

```bash
cd backend && pytest
```

## Convenção

Testes que precisam de fixtures vão em `tests/fixtures/` (ex: protocolo de
exemplo, sessão de exemplo com 3 rodadas).
