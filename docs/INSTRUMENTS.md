# Instrumentos de pesquisa

Um **instrumento** é um questionário definido em YAML em `instruments/<id>.yaml`. A plataforma aplica antes (`pre_session`) ou depois (`post_session`) de uma sessão, baseado no que o protocolo declara.

## Tipos de pergunta suportados

| Tipo | Uso | Como o frontend renderiza |
|---|---|---|
| `text_short` | Texto curto livre | Input single-line |
| `text_long` | Texto longo livre | Textarea |
| `likert` | Escala 1-N | N botões redondos com rótulos opcionais |
| `single_select` | Uma opção | Botões empilhados, ○/● |
| `multi_select` | Várias opções | Botões empilhados, ▢/▣ |
| `slider` | Numérico contínuo | Input range com rótulos extremos |
| `ranking` | Ordenar opções | Drag-and-drop + botões ↑/↓ |

## Estrutura

```yaml
id: meu_instrumento_v1                   # único; nome do arquivo sem .yaml
version: 1.0.0
moment: pre_session                      # pre_session | post_session
title: "Antes de começarmos"
description: "Algumas perguntas rápidas..."

sections:
  - id: profile                          # agrupamento lógico
    title: "Sobre você"
    description: "Dados básicos."
    items:
      - id: age_range
        type: single_select
        question: "Qual sua faixa etária?"
        options: ["18-24", "25-34", "35-44", "45+"]
        required: true                   # default true

      - id: open_field
        type: text_long
        question: "Comentários livres"
        placeholder: "opcional..."
        max_length: 500
        required: false

  - id: scale_section
    title: "Suas atitudes"
    items:
      - id: trust
        type: likert
        question: "Quanto você confia em IA?"
        scale: 5                         # número de pontos
        labels:                          # opcional, um por ponto
          - "Nada"
          - "Pouco"
          - "Mais ou menos"
          - "Bastante"
          - "Muito"

      - id: creativity
        type: slider
        question: "De 0 a 100, quão criativa foi a discussão?"
        min: 0
        max: 100
        step: 1
        default: 50
        min_label: "nada"
        max_label: "muito"

      - id: priorities
        type: ranking
        question: "Ordene por importância (arraste)"
        options:
          - "Ter ideias novas"
          - "Aprofundar uma ideia"
          - "Ser desafiado"
          - "Sair com algo concreto"
```

## Como criar um instrumento

1. Copia um exemplo: `cp instruments/pre_session_cocreation_v1.yaml instruments/meu_estudo_v1.yaml`
2. Muda `id`, `title`, edita os items
3. Vincula no protocolo:
   ```yaml
   instruments:
     pre_session: meu_estudo_v1
     post_session: post_session_cocreation_v1
   ```
4. Pronto. Frontend carrega via `GET /api/instruments/{id}` na hora certa.

## Onde as respostas vão

Em `data/sessions/<sid>/instruments/<iid>.json`:

```json
{
  "instrument_id": "meu_estudo_v1",
  "instrument_version": "1.0.0",
  "session_id": "20251208-...",
  "moment": "pre_session",
  "started_at": "2025-12-08T14:00:00Z",
  "submitted_at": "2025-12-08T14:03:42Z",
  "duration_ms": 222000,
  "responses": [
    {
      "item_id": "age_range",
      "value": "25-34",
      "time_spent_ms": 4200,
      "answered_at": null
    },
    ...
  ],
  "response_order": ["age_range", "trust", "creativity", "open_field", ...]
}
```

**`response_order`** é a ordem de primeira interação com cada item — útil pra detectar respondedores em sequência vs que pulam pra trás.

**`time_spent_ms`** por item é o tempo entre primeira interação e última edição daquele item.

**`duration_ms`** total é desde o load do form até o submit.

## Itens não-respondidos

Itens com `required: true` que ficaram sem resposta:
- Frontend desabilita o botão "Enviar respostas" e mostra contador
- Se mesmo assim chegar ao backend (pular via `Pular`), o evento `instrument.submitted` lista em `missing_required`

A política atual é **permissiva**: se você pular, gravamos o que tem e marcamos os faltantes. Pra modo strict, edite `submit_instrument_response` em `services/instrument_service.py` — tem comentário no lugar.

## Validação

Itens com `item_id` desconhecido (ex: você renomeou um item depois) são silenciosamente descartados na submissão. O contador de `responses_count` no payload do evento reflete apenas os válidos.

## Análise

A estrutura JSON é diretamente plottável em pandas:

```python
import json, pandas as pd
from pathlib import Path

records = []
for d in Path("data/sessions").iterdir():
    f = d / "instruments" / "post_session_cocreation_v1.json"
    if not f.exists():
        continue
    inst = json.loads(f.read_text())
    row = {"session_id": inst["session_id"], "duration_s": inst["duration_ms"] / 1000}
    for r in inst["responses"]:
        row[r["item_id"]] = r["value"]
    records.append(row)

df = pd.DataFrame(records)
print(df["ownership"].describe())
```
