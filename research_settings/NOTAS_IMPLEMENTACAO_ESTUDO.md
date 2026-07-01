# Artefatos do estudo de simulação — notas de implementação

> Arquivos construídos para a `research_settings/` a partir do desenho fatorial.
> Cobrem o **núcleo A×B×C×D**, a **população sintética 3×3**, o **Fator A
> (composição)**, os **temas em níveis de complexidade**, o **juiz composto** e
> as **variantes do loop (decomposição da homogeneização)**.

---

## 1. Inventário (onde cada arquivo vai)

```
research_settings/
├── simulacao.yaml                 (TESTE MÍNIMO — roda por padrão; ~12 sessões, ~264 calls)
├── simulacao_abc.yaml             (produção A×B×C — 72 células, ~12.960 sessões)
├── simulacao_completa.yaml        (A×B×C×D — requer os 3 itens novos do runner)
├── simulacao_decomposicao.yaml    (variantes do loop B0–B3 — requer runner)
├── temas/
│   └── temas.yaml                 (SUBSTITUI o atual) — 6 níveis de complexidade
├── composicao_mesa/
│   ├── comum.yaml                 (novo) — Fator A, nível 'comum'
│   └── celebridade.yaml           (novo) — Fator A, nível 'celebridade'
└── jogadores_simulados/
    ├── cauteloso_t04 / _t07 / _t10.yaml      (novos)
    ├── equilibrado_t04 / _t07 / _t10.yaml    (novos)
    └── ousado_t04 / _t07 / _t10.yaml         (novos)   → 9 jogadores
```

> **Para testar agora:** `simulacao.yaml` é o teste mínimo (3 células × 2
> jogadores × n_games 2 = 12 sessões). Cobre os 3 modos de `best_idea` e dá 4
> sessões/célula (diversidade coletiva calculável). Gera dados suficientes para
> desenvolver o notebook. Os outros `simulacao_*.yaml` são para escalar depois.
>
> A pasta `juiz/` NÃO é tocada: o critério `composto` vem da condição
> `judge_criterion: [composto]`, usando o seu `juiz/juiz.yaml` original.

Os 3 jogadores antigos ficam **superados** pelos 9 novos (antes confundiam
persona com temperatura). Pode removê-los ou só não listá-los em `jogadores`.

---

## 2. Como o desenho fatorial mapeia nos arquivos

| Fator | Níveis | Onde, no arquivo |
|---|---|---|
| **A. Composição** | `comum` / `celebridade` | `condicoes.composicao` → `composicao_mesa/{comum,celebridade}.yaml` |
| **B. Dinâmica** | `judge` / `player` / `player_decides` | `condicoes.best_idea` (já existia) |
| **C. Cegueira de fonte** | `anonima` / `identificada` | `condicoes.source_blind_on_choice` + `judge_blind_follows_choice` |
| **D. Pareamento de modelos** | `same_model` / `cross_model` | `condicoes.model_pairing` + `model_map` *(novo)* |
| **Controle: tema** | 6 temas (1 por nível) | `condicoes.tema` (efeito aleatório; nível = moderador) |
| **População** | 3 personas × 3 temps = 9 | `jogadores_simulados/*.yaml` + `jogadores:` |

**População 3×3.** Persona e temperatura são **eixos cruzados**: cada arquivo é
uma célula persona×temp, com `traits.persona_base` e `traits.temperatura` para a
análise estratificar. São as 9 unidades de replicação / intercepto aleatório.
Temperaturas 0.4 / 0.7 / 1.0.

**Fator A.** Contraste forte: `comum` (heterogênea, baixa densidade no corpus)
vs `celebridade` (ícones canônicos, alta densidade → sinal mais forte de
homogeneização). Alternativas se quiser: apontar `celebridade` para uma mesa de
domínio único existente (ex.: `filosofos`) para homogeneidade estrita; ou usar as
5 mesas de domínio como o arm `celebridade/homogênea` na extensão A(4)
(Diversidade × Fama).

---

## 3. Fator D — só OpenAI disponível (importante)

Como só há acesso à **OpenAI**, o pareamento entre **famílias/fornecedores
distintos** (o `cross_family` original) **não é possível**. O fator foi
reformulado para testar o artefato adjacente, que ainda é o cerne do H5:

- **`same_model`** — o MESMO modelo OpenAI em todos os papéis (personas, juiz,
  jogador-agente).
- **`cross_model`** — modelos OpenAI **diferentes** por papel.

Isso responde a "quanto da homogeneização é por usar **literalmente o mesmo
modelo** em todos os assentos?". O que **fica como limitação declarada /
trabalho futuro**: a crítica mais ampla de circularidade ("LLM julgando LLM, todos
da mesma distribuição de treino") só se neutraliza com **fornecedores distintos**,
fora de alcance agora. Registrar isso na seção *Limitations* e enfraquecer a
alegação de H5 para "não é artefato de modelo idêntico" (em vez de "não é artefato
de modelo compartilhado"). Os defensores do loop multi-agente + os baselines de
decomposição (B0–B3) seguem ancorando o argumento.

> Confirme quais modelos OpenAI você tem na conta e ajuste os nomes em
> `model_map.cross_model` (coloquei `gpt-4o-mini` / `gpt-4o` / `gpt-4.1-mini`
> como exemplo).

---

## 4. Temas em níveis de complexidade (novo)

`temas.yaml` foi reorganizado em **6 níveis**, do concreto ao abstrato/aberto.
A área (= nível) é o estratificador; mantém o schema antigo, então a plataforma
'live' continua lendo igual.

| id (nível) | complexidade | tema escolhido para o núcleo |
|---|---|---|
| t1 `cotidiano` | 1 | Como reduzir o desperdício de comida em casa? |
| t2 `convivencia_social` | 2 | Uma nova forma de as pessoas fazerem amizades na vida adulta |
| t3 `filosofico` | 3 | O que torna uma vida bem vivida? |
| t4 `tecnico_cientifico` | 4 | Como reduzir as alucinações de modelos de linguagem? |
| t5 `complexo_sistemico` | 5 | Como uma cidade média pode se adaptar a eventos climáticos extremos? |
| t6 `criativo_especulativo` | 6 | Como seria uma cidade projetada para o ócio, e não para o trabalho? |

Cada nível tem 3 subtemas no arquivo (18 no total); o núcleo usa 1 por nível
(os 6 acima) para varrer o gradiente. **Ganho científico:** além de réplica
(efeito aleatório), o **nível de complexidade** entra como **covariável/moderador**
— dá para perguntar se a homogeneização (RQ2) muda do tema cotidiano ao técnico
ao especulativo. Isso vira um achado secundário no notebook.

> Resolução de tema: referenciei pela **frase exata** (subtemas são strings em
> `temas.yaml`). Se o runner resolver por **id**, troque `condicoes.tema` por
> `[t1..t6]` usando o mapa acima e me avise — ajusto.

---

## 5. Dimensionamento (confira no `dry_run`)

Núcleo: A(2) × B(3) × C(2) × D(2) = **24 células** × 6 temas = **144 células×tema**.

`sessões = n_games × |jogadores| × |células×tema|`

- `n_games=20`, 9 jogadores: `20 × 9 × 144 = 25 920 sessões`.
- Enxuto (`n_games=10`, 6 jogadores, 4 temas): `10 × 6 × (24×4) = 5 760 sessões`.

Reduza nesta ordem se o custo apertar: `n_games` → temas → jogadores.
Procedimento: **(1) `dry_run: true`** → **(2) piloto** 1–2 sessões/célula →
**(3) análise de poder** (menor efeito de interesse: `judge`–`player`, RQ2) →
**(4) estudo completo** com `dry_run: false`.

---

## 6. *** O que exige suporte NOVO do runner *** (3 itens + 1 opcional)

1. **Fator D — `model_pairing` + `model_map` (modelo por papel).** Hoje o modelo
   é único; o runner precisa atribuir, por sessão, o modelo de cada papel
   conforme `model_map[<nivel>]` (agora só com modelos OpenAI).

2. **Acoplamento do Fator C — `judge_blind_follows_choice: true`.** Para C ser
   **um** fator de 2 níveis (24 células), a cegueira do juiz deve seguir a da
   escolha por sessão. Sem isso, os dois flags geram 4 combinações (a extensão
   C-juiz × C-escolhedor).

3. **Variantes do loop** (`simulacao_decomposicao.yaml`): `independente` (B0 —
   gera o *reference set* de originalidade), `selecao_aleatoria` (B1),
   `sem_realimentacao` (B2), `loop_completo` (B3). Cada uma remove/mantém um
   mecanismo do loop.

4. **(Opcional) `yoked_seeds`.** Parear seeds entre níveis de C e D → mais poder.

Já cobertos pelo runner atual: `best_idea`, `composicao`, `tema`, `rounds`,
`source_blind_on_choice`, `judge_criterion`, população, `dry_run`, marcação
sintética e saída em `data/sim_runs/`.

---

## 7. Decisões a confirmar antes de rodar

1. **A(2) (assumido)** `comum` vs `celebridade`, ou extensão **A(4)**?
2. **`model_map.cross_model`** — confirme os 3 modelos OpenAI que você tem.
3. **Operacionalização da `celebridade`** — mista (atual) ou domínio único estrito?
4. **`n_games`** — definido por poder após o piloto (default 20).
5. **Resolução de tema** — string (atual) ou id (§4)?
6. Defaults do documento confirmados: `R=6` + sweep {4,6,8}; `K=4`; 9 jogadores;
   embedding multilíngue + segundo de robustez (entra no notebook).

**Robustez (execuções à parte):** duplicar `simulacao.yaml` com
`rounds: [4, 6, 8]` (RQ4) e `judge_criterion: [originalidade, viabilidade, composto]`.

---

## 8. O que falta para eu construir o notebook de análise

O notebook lê `data/sim_runs/<run_id>/sessions/<sessao>/`. Para escrever o parser
que vira `ideas` / `rounds` / `sessions` / `cells` / `system` **sem adivinhar o
schema**, preciso de **uma pasta de sessão simulada real da v2** (mesmo de um
piloto): `events.jsonl`, `manifest.json` e `final_idea.json`. O crítico é o
**payload dos eventos `round.*`** — autor de cada ideia, escolha do juiz, escolha
do jogador, qual avançou e como autoria/modelo ficam registrados.

Sugestão: `dry_run: true` (valida contagem) → piloto minúsculo
(`n_games: 1`, 1 jogador, 1 célula, `dry_run: false`) → me mandar a pasta de saída.