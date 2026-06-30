# Protocolos

Um **protocolo** é um arquivo YAML em `protocols/<id>.yaml` que define todas as variáveis manipuláveis de uma sessão. É a unidade científica da plataforma — pra rodar um estudo comparativo, basta criar dois protocolos com diferenças controladas.

O sistema vem com 4 protocolos prontos:

| Arquivo | Diferença chave |
|---|---|
| `default.yaml` | Configuração base. 4 atos, garçom árbitro, dono neutro, memória refletida. |
| `blind_personas.yaml` | Esconde nome/role das IAs pro humano (vê "Persona A", "B"...). |
| `solo_baseline.yaml` | Humano sozinho, sem IAs. Control científico. 3 rodadas em vez de 4. |
| `passive_waiter.yaml` | Garçom só responde a comandos diretos. Sem desempate automático. |

## Estrutura completa

```yaml
id: meu_protocolo                    # único; corresponde ao nome do arquivo
version: 1.0.0                       # SEMVER, manualmente
description: |
  Descrição livre. Aparece na UI no seletor.
language: pt                         # pt | en — define idioma de prompts e UI

# === LLM defaults ===
llm_default_provider: google         # google | openai
llm_default_model: gemini-1.5-flash
llm_temperature: 0.7

# === Reprodutibilidade ===
llm_seed_strategy: random_logged     # ou "fixed:42"
randomization_seed: null             # ou um inteiro pra fixar tudo

# === 4 atos ===
phases:
  - name: warmup                     # warmup | discussion | convergence | closing
    rounds: 1                        # nº de rodadas nesta fase
    bidding_enabled: false           # se permite apostar
    bid_multiplier: 0.0              # multiplicador da aposta efetiva
    description: "Aquecimento"
  - name: discussion
    rounds: 4
    bidding_enabled: true
    bid_multiplier: 1.0
  - name: convergence
    rounds: 1
    bidding_enabled: true
    bid_multiplier: 2.0              # convergence dobra a aposta
  - name: closing
    rounds: 0                        # closing sempre 0; é só síntese
    bidding_enabled: false

# === Drinks → temperatura ===
economy:
  drinks_to_temperature_step: 0.1    # cada drink soma X
  drinks_temperature_max: 1.4        # teto absoluto
  base_balance: 1000.0
  bid_min: 1.0

# === Modo do Garçom ===
waiter:
  mode: active_arbiter               # passive | active_arbiter | autonomous
  bid_extreme_threshold: 0.5         # aposta > N×saldo dispara intervenção

# === Viés do Dono na síntese ===
owner:
  bias: neutral                      # neutral | pro_winner | pro_human | pro_bidder

# === Memória das personas ===
memory:
  mode: reflected_summary            # none | private_memo | reflected_summary

# === Telemetria ===
telemetry:
  capture_keystrokes: true
  aggregate_metrics: true

# === Instrumentos a aplicar ===
instruments:
  pre_session: pre_session_cocreation_v1   # id de arquivo em instruments/
  post_session: post_session_cocreation_v1
  post_round: null                         # placeholder; não aplicado ainda

# === Manipulações experimentais ===
display:
  blind_personas: false              # esconde nome/role das IAs
  solo_baseline: false               # ignora as personas IA
```

## Como criar um protocolo novo

1. Copia um existente: `cp protocols/default.yaml protocols/meu_estudo.yaml`
2. Muda `id`, `version`, `description`
3. Edita os campos que você quer manipular
4. Salva. Não precisa reiniciar — `protocols/` é montado como volume read-only e o loader recarrega no próximo `/setup`
5. No setup, escolha "meu_estudo" no dropdown

## Variáveis manipuláveis comuns

**Pra estudar efeito da identidade da IA**: `display.blind_personas: true` vs `false`. Pareie sessões com mesmas personas e mesmo seed.

**Pra estudar efeito da co-criação**: `display.solo_baseline: true` vs default. Compara qualidade percebida da ideia, ownership, satisfação.

**Pra estudar efeito do mediador**: `waiter.mode: active_arbiter` vs `passive`. Compara diversidade de propostas, taxa de empate, tempo gasto.

**Pra estudar efeito do viés do dono**: `owner.bias: neutral` vs `pro_human`. Compara similaridade da síntese vs propostas do humano.

**Pra estudar custo de memória**: `memory.mode: reflected_summary` vs `none`. Compara qualidade percebida vs custo em tokens.

## Validação

O backend valida o YAML via Pydantic. Se um campo é incompatível com o schema, `/api/setup` retorna 422. Pra testar antes:

```bash
docker compose exec backend python -c "
from protocols.loader import load_protocol
p = load_protocol('meu_estudo')
print(p)
"
```

## Estado congelado da sessão

Quando uma sessão é criada, o protocolo é serializado em `data/sessions/<sid>/protocol.json`. **Edições posteriores ao YAML não afetam sessões existentes.** Garante reprodutibilidade.
