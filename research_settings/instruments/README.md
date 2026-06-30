# Instrumentos

Questionários e escalas aplicados antes/durante/depois das sessões.

Cada arquivo é um JSON descrevendo um questionário: lista de itens, tipo de
cada item (Likert, free-text, múltipla escolha, NASA-TLX), e metadados
(versão, fonte bibliográfica, instruções).

## Itens previstos

- `pre_default.json` — pré-questionário padrão (familiaridade com IA,
  criatividade auto-percebida, expectativa)
- `post_default.json` — pós-questionário padrão (experiência geral, surpresas)
- `nasa_tlx.json` — NASA-TLX adaptado (carga cognitiva)
- `trust_in_ai.json` — escala de confiança em IA
- `creativity_self_perception.json` — percepção da própria criatividade
- `summary_evaluation.json` — avaliação humana da síntese final do Dono do Bar

## Status

- **Fase 3** — Implementação completa: loader, frontend, registro de respostas
  em `pre_responses.json` e `post_responses.json` na pasta da sessão.
