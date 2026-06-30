# Estrutura dos formulários (pré e pós jogo)

Cada formulário é um arquivo **YAML** nesta pasta (`instruments/`). A plataforma
lê esse arquivo e **monta o formulário sozinha** — você não precisa mexer em
código. Para incluir, remover ou editar perguntas, basta editar o arquivo e
fazer o deploy (reinício). Depois, confira em `/?admin=1` ou rodando
`python -m catalog` (em `backend/app`) que a plataforma "enxergou" as mudanças.

- **Formulário pré-jogo:** `pre_session_cocreation_v1.yaml`
- **Formulário pós-jogo:** `post_session_cocreation_v1.yaml`

Qual arquivo é usado como pré/pós é definido no protocolo
(`core/protocols/<arm>.yaml`, campos `instruments.pre_session` e
`instruments.post_session`) — aponta para o `id` do formulário.

---

## 1. Esqueleto do arquivo

```yaml
id: pre_session_cocreation_v1     # único; igual ao nome do arquivo (sem .yaml)
version: 1.0.0                    # versão do instrumento (vai para os dados)
moment: pre_session              # pre_session | post_session | post_round
title: Antes de começarmos       # título mostrado no topo
description: >                    # subtítulo opcional
  Texto curto explicando o formulário.

sections:                        # uma ou mais seções
  - id: profile                  # id único da seção
    title: Sobre você            # opcional
    description: Dados básicos.   # opcional
    items:                       # as perguntas (veja a seção 3)
      - id: ...
        type: ...
        question: ...
```

A ordem das seções e dos itens no arquivo é a ordem em que aparecem na tela.

---

## 2. Campos comuns a TODOS os itens

| Campo         | Obrigatório | Descrição                                                        |
|---------------|-------------|------------------------------------------------------------------|
| `id`          | sim         | Identificador único do item dentro do formulário (sem espaços).  |
| `type`        | sim         | Um dos tipos da seção 3.                                          |
| `question`    | sim         | O enunciado mostrado ao participante.                            |
| `description` | não         | Texto de apoio abaixo da pergunta.                              |
| `required`    | não         | `true` (padrão) ou `false`. Se `true`, não dá pra enviar sem responder. |

> **Obrigatório ou não:** todo item é obrigatório por padrão. Para tornar
> opcional, escreva `required: false`. O botão de enviar só libera quando todos
> os itens obrigatórios estiverem respondidos.

---

## 3. Tipos de item

### `text_short` — texto curto (uma linha)
Use para **nome (fictício)**, área de atuação, respostas curtas.

| Campo extra   | Descrição                          |
|---------------|------------------------------------|
| `placeholder` | dica dentro do campo (opcional)    |
| `max_length`  | nº máximo de caracteres (opcional) |

```yaml
- id: nome_ficticio
  type: text_short
  question: Que nome (fictício) você quer usar na mesa?
  placeholder: ex. Andorinha, Tom, Capivara...
  max_length: 40
  required: true
```

### `text_long` — texto longo (várias linhas)
Mesmos campos do `text_short`, renderiza uma caixa maior.

```yaml
- id: expectativa
  type: text_long
  question: Em uma frase, o que você espera dessa conversa?
  placeholder: ex. quero destravar um problema...
  max_length: 280
  required: false
```

### `number` — número (idade, quantidade)
Campo numérico com faixa opcional. Use para **idade** ou qualquer número.

| Campo extra | Descrição                                  |
|-------------|--------------------------------------------|
| `min`       | menor valor aceito (opcional)              |
| `max`       | maior valor aceito (opcional)              |
| `step`      | incremento (padrão 1)                      |
| `unit`      | unidade exibida ao lado (ex.: `anos`)      |
| `placeholder` | dica dentro do campo (opcional)          |

```yaml
- id: idade
  type: number
  question: Qual a sua idade?
  min: 18
  max: 99
  step: 1
  unit: anos
  required: true
```

### `likert` — escala de concordância/intensidade
Escala de N pontos com rótulos.

| Campo extra | Descrição                                              |
|-------------|--------------------------------------------------------|
| `scale`     | nº de pontos (ex.: 5 ou 7) — **obrigatório**           |
| `labels`    | rótulos dos pontos (idealmente `scale` rótulos)        |

```yaml
- id: confianca_ia
  type: likert
  question: Quanto você confia nas respostas da IA generativa?
  scale: 5
  labels: ["Confio muito pouco", "Pouco", "Mais ou menos", "Bastante", "Confio bastante"]
```

### `single_select` — escolha única (uma de várias)
Use para **faixa etária por faixas**, escolaridade, etc.

| Campo extra | Descrição                          |
|-------------|------------------------------------|
| `options`   | lista de opções — **obrigatório**  |

```yaml
- id: faixa_etaria
  type: single_select
  question: Qual sua faixa etária?
  options: ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
```

### `multi_select` — múltipla escolha (várias ao mesmo tempo)

| Campo extra | Descrição                          |
|-------------|------------------------------------|
| `options`   | lista de opções — **obrigatório**  |

```yaml
- id: usos_ia
  type: multi_select
  question: Pra que você usa IA hoje? (marque todas que se aplicam)
  options: [Curiosidade, Estudo, Trabalho, Programação, Criação artística]
```

### `slider` — controle deslizante (valor contínuo)
Use para intensidade/expectativa numa barra arrastável.

| Campo extra | Descrição                                |
|-------------|------------------------------------------|
| `min`       | valor mínimo (padrão 0)                  |
| `max`       | valor máximo (padrão 100)                |
| `step`      | incremento (padrão 1)                    |
| `default`   | valor inicial da barra                   |
| `min_label` | rótulo da ponta esquerda                 |
| `max_label` | rótulo da ponta direita                  |

```yaml
- id: expectativa_criatividade
  type: slider
  question: Quão criativa você espera que essa discussão seja?
  min: 0
  max: 100
  step: 1
  default: 50
  min_label: nada criativa
  max_label: muito criativa
```

### `ranking` — ordenar por arrastar-e-soltar

| Campo extra | Descrição                                  |
|-------------|--------------------------------------------|
| `options`   | itens a ordenar — **obrigatório**          |

```yaml
- id: prioridades
  type: ranking
  question: Ordene do mais para o menos importante para você.
  options: [Originalidade, Utilidade, Rapidez, Diversão]
```

---

## 4. Receitas rápidas

**Nome fictício** → `text_short` (veja acima).

**Idade como número com faixa** → `number` com `min`/`max`/`unit: anos`.

**Idade por faixas** → `single_select` com `options: ["18-24", ...]`.

**Pergunta opcional** → adicione `required: false`.

---

## 5. O que a plataforma valida

Ao subir (e em `/?admin=1` / `python -m catalog`), a plataforma confere:

- `single_select`, `multi_select`, `ranking` precisam de `options`.
- `likert` precisa de `scale` (avisa se o nº de `labels` não bate com a escala).
- `number` e `slider`: se tiver `min` e `max`, exige `min < max`.
- ids de itens **duplicados** no mesmo formulário são erro.
- arquivo malformado é reportado (sem derrubar a plataforma).

Itens com erro aparecem na tela de estrutura (`/?admin=1`) e fazem o verificador
de deploy (`python -m catalog`) sair com código de erro — útil pra travar um
deploy quebrado antes de ir ao ar.
