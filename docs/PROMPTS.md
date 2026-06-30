# Prompts

Os prompts da plataforma vivem em `prompts/<id>/<version>.<lang>.jinja2`. São templates Jinja2 puros, versionados e hashados.

## Convenções de nome

```
prompts/
  proposal/
    v1.jinja2          ← versão padrão, idioma default (pt)
    v1.en.jinja2       ← tradução EN
    v2.jinja2          ← se quiser experimentar uma versão nova
  owner_summary_neutral/
    v1.jinja2
    v1.en.jinja2
  ...
```

**Sem sufixo** = idioma default (pt). **Com sufixo** = aquela tradução específica. Quando você pede um prompt em EN e não há `v1.en.jinja2`, o sistema cai no `v1.jinja2` (PT) automaticamente.

## Prompts existentes

| Pasta | Quando é chamado | Em PT | Em EN |
|---|---|---|---|
| `proposal/` | A cada IA propondo uma ideia | ✓ | ✓ |
| `persona_reflect/` | Antes de cada proposta (memória refletida) | ✓ | ✓ |
| `waiter_choose/` | Voto delegado | ✓ | ✓ |
| `waiter_tiebreak/` | Desempate quando apostas próximas | ✓ | — |
| `waiter_summarize/` | Botão "Resumo parcial" | ✓ | — |
| `waiter_provoke/` | Botão "Provocar" | ✓ | — |
| `owner_summary_neutral/` | Síntese final, viés neutral | ✓ | ✓ |
| `owner_summary_pro_winner/` | Síntese, viés pro_winner | ✓ | — |
| `owner_summary_pro_human/` | Síntese, viés pro_human | ✓ | — |
| `owner_summary_pro_bidder/` | Síntese, viés pro_bidder | ✓ | — |
| `lab_structure/` | Estruturação pro Lab | ✓ | — |
| `persona_generation/` | Gerar time com IA | ✓ | — |

A versão EN está completa apenas pros prompts críticos. Pra adicionar uma tradução, basta criar `<id>/<version>.en.jinja2` ao lado do PT — o registry detecta na próxima requisição.

## Variáveis disponíveis em cada prompt

**`proposal/v1`**:
- `topic`, `phase`, `bidding_enabled`, `balance`, `max_bid`
- `persona`: objeto com `name`, `role`, `goal`, `description`, `instructions`
- `history`: lista de `ChatMessage` (`player_name`, `message`)
- `memo`: string com a reflexão privada da persona (vazio na 1ª rodada)

**`persona_reflect/v1`**:
- `topic`, `persona`, `previous_memo`, `history`

**`waiter_choose/v1`** e **`waiter_tiebreak/v1`**:
- `topic`, `proposals`: lista de `IdeaProposal` (`player_id`, `player_name`, `idea_text`, `bid_amount`)

**`waiter_summarize/v1`** e **`waiter_provoke/v1`**:
- `topic`, `history`, `round`, `phase`

**`owner_summary_*/v1`**:
- `topic`, `history`, `players`: lista de `Player` (com `balance`, `drinks`)

**`lab_structure/v1`**:
- `summary` (texto da síntese final)

**`persona_generation/v1`**:
- `theme`

## Versionamento

Mudou um prompt? Crie uma versão nova em vez de editar a antiga:

```bash
cp prompts/proposal/v1.jinja2 prompts/proposal/v2.jinja2
# edita v2
```

Pra usar v2, você precisaria editar `services/game_service.py` ou expor isso via protocolo. **Mas não recomendamos.** Edite v1 mesmo, e confie no `prompt_hash` registrado em `llm_calls.jsonl` — sessões antigas continuam comparáveis pelo hash do conteúdo na hora.

A regra: **só crie v2 se você quer rodar v1 e v2 na mesma sessão**, o que não é o uso típico.

## Hash e log

Quando uma chamada LLM acontece, ela registra:

```json
{
  "prompt_id": "proposal",
  "prompt_version": "v1",
  "prompt_hash": "a3f8e2c1...",  // sha256 do conteúdo na hora
  "rendered_prompt": "Você está em uma mesa...",  // já interpolado
  ...
}
```

Em análise depois, agrupa por `prompt_hash` pra ter certeza de comparar a mesma versão real do conteúdo.

## i18n no fluxo

O `protocol.language` (lido do YAML) é passado pra todas as funções em `llm/tasks.py`. Cada chamada de `renderer.render()` passa `language=protocol.language`. Se o prompt não existir naquele idioma, fallback automático pra PT.

A UI segue o seletor `mdb_language` em `localStorage`, definido pelo dropdown no `SetupScreen`. UI e prompts podem estar em idiomas diferentes — útil pra rodar UI em PT e prompts em EN (ou o contrário) se for comparar com pesquisa internacional.

## Snapshot dos prompts ativos

Quando uma sessão é criada, `manifest.json["prompts"]` lista todos os prompts conhecidos no momento (`prompt_id` + `version`). Permite saber retroativamente quais prompts existiam quando a sessão rodou.
