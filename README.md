> **v2 (Fases A-D):** loop científico (propor cego → escolher anônimo → juiz IA → revelar → avançar), runner experimental balanceado (braços/CoT/composições), avaliação automática por embeddings + export CAT, e painel CAT cego com validação juiz-IA × humano. Ver `FASE_A.md`…`FASE_D.md`.

# Mesa de Bar

> Plataforma científica de co-criação humano-IA. Sente-se à mesa com 1 a 4 personas de inteligência artificial customizáveis, defenda suas ideias com apostas reais, e ao fim da noite o Dono do Bar sintetiza tudo numa ideia final estruturada.

A Mesa de Bar é simultaneamente uma **ferramenta de brainstorming** e uma **plataforma de pesquisa empírica** sobre como humanos co-criam com IAs. Tudo o que acontece numa sessão (cada decisão, cada chamada LLM, cada keystroke opcional) é registrado de forma estruturada para análise posterior.

---

## Sumário

- [Visão e ideia central](#visão-e-ideia-central)
- [Conceitos do jogo](#conceitos-do-jogo)
- [Como funciona uma sessão](#como-funciona-uma-sessão)
- [Início rápido](#início-rápido)
- [Configuração detalhada](#configuração-detalhada)
- [Composições de mesa](#composições-de-mesa)
- [Protocolos experimentais](#protocolos-experimentais)
- [Instrumentos de pesquisa](#instrumentos-de-pesquisa)
- [O que sai no fim da sessão](#o-que-sai-no-fim-da-sessão)
- [Arquitetura](#arquitetura)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Stack técnica](#stack-técnica)
- [Documentação técnica](#documentação-técnica)
- [Estado do projeto](#estado-do-projeto)

---

## Visão e ideia central

A Mesa de Bar foi desenhada para responder perguntas que estão no centro do debate sobre IA generativa hoje:

- **Quando uma IA realmente colabora vs. apenas concorda?** Forçando cada IA a tomar uma postura explícita (complementar, contrapor ou redirecionar), conseguimos medir o tipo de contribuição que ela está fazendo.
- **A identidade da IA importa para a percepção de qualidade?** Pela manipulação `blind_personas`, o usuário pode jogar sem saber quem é cada IA — e comparamos com sessões abertas.
- **Co-criação humano-IA produz ideias melhores que criação solo?** Pelo protocolo `solo_baseline`, rodamos sessões sem IAs como controle científico.
- **Como mediação afeta o resultado?** O Garçom pode ser passivo, árbitro ativo ou autônomo — três modos experimentais.

A plataforma é **research-in-a-box**: o pesquisador clona o repositório, sobe `docker compose up`, joga uma ou mais sessões, e baixa um ZIP completo com todos os dados estruturados.

**Sem banco de dados. Sem cadastro. Cada sessão vive em uma pasta.** Análise depois com pandas, R ou ferramenta da sua preferência.

---

## Conceitos do jogo

A metáfora é a mesa de bar — um espaço informal onde ideias circulam, ganham apoio (ou não), e personagens diversos contribuem com suas perspectivas.

### Personas IA

Você escolhe **4 personas** para acompanhar você na mesa. Cada uma tem:

- **Nome, papel, objetivo, descrição e instruções** — definem como ela se posiciona.
- **Persona** real (ex: Sócrates, Tesla, Nietzsche) ou arquetípica (O Cético, O Otimista).

Como montar o time:
1. Escolher uma **composição pronta** (12 disponíveis — filósofos clássicos, empreendedores tech, pensadoras feministas, etc).
2. **Gerar com IA** a partir de um tema livre ("piratas espaciais", "fundadoras de ONGs", "críticos do capitalismo").
3. **Editar manualmente** cada persona, ajustando role, goal e instructions.

### A aposta como sinal de confiança

A cada rodada, cada participante (você e as IAs) propõe uma ideia e **aposta dinheiro virtual nela**. A aposta funciona como sinal escasso de confiança: "estou colocando $80 dos $1000 que tenho — acho que esta ideia merece atenção".

O vencedor da rodada leva o pote inteiro. Apostas altas aumentam o saldo para próximas rodadas, criando dinâmica estratégica.

### Drinks → temperatura do LLM

O vencedor de uma rodada ganha um **drink**. Cada drink aumenta a `temperature` do modelo LLM da persona vencedora na rodada seguinte — uma analogia gameplay direta com a embriaguez progressiva de uma mesa de bar. Personas que vencem muito ficam progressivamente mais ousadas, criativas, menos previsíveis.

### O Garçom (mediador)

Um árbitro neutro com 3 funções:

1. **Voto delegado** — em vez de votar você mesmo, pode pedir ao Garçom para escolher o vencedor da rodada.
2. **Resumo parcial** — em qualquer momento, o Garçom resume o que rolou até agora.
3. **Provocar a mesa** — pede uma pergunta provocativa ao Garçom para destravar a conversa.

O Garçom também **desempata automaticamente** quando duas apostas são muito próximas (configurável por protocolo).

### O Dono do Bar (sintetizador)

Ao fim da noite, o Dono lê todo o histórico e escreve a **síntese final** — a "carta" que apresenta a ideia que emergiu. O viés do Dono é configurável: pode favorecer o vencedor, o humano, o mais corajoso nas apostas, ou ser estritamente neutro.

### Postura (stance) das IAs

A partir da Fase 6, cada proposta das IAs vem com uma postura explícita declarada:

- **complement** — construir por cima da ideia anterior, aprofundando
- **counter** — discordar e apresentar contraponto firme
- **redirect** — puxar a conversa para um ângulo novo

Isso quebra o problema de "todas as IAs concordam vagamente" e cria dado científico analisável (em quais rodadas a mesa convergiu vs. divergiu?).

### Os 4 atos

Toda sessão tem 4 fases:

| Fase | Apostas | Descrição |
|---|---|---|
| **Aquecimento** | Não | Apresentação livre, sem pressão. |
| **Discussão** | Sim | Apostas normais, ideias se desenvolvem. |
| **Convergência** | Sim, **dobradas** | Hora de fechar — apostas dobram. |
| **Encerramento** | — | Síntese do Dono. |

Cada fase tem número de rodadas configurável no protocolo.

---

## Como funciona uma sessão

```
1. Setup
   └── Você define: nome, tópico, 4 personas, protocolo, idioma

2. Pesquisa pré-sessão (opcional, configurado pelo protocolo)
   └── Questionário breve sobre você e suas atitudes

3. Mesa
   ├── Várias rodadas de proposta → votação → vencedor
   ├── Você pode: apostar, passar, endossar, delegar ao Garçom
   ├── Garçom: resumo / provocação / dashboard de custos
   └── Encerrar quando quiser ou ao fim da Convergência

4. Carta do Dono do Bar
   └── Síntese final num formato de carta, com avatar e tipografia caprichada

5. Pesquisa pós-sessão (opcional)
   └── Como foi a experiência? Quão sua era a ideia final?

6. Resultado da sessão
   ├── Estatísticas (rodadas, stances, vitórias, custos LLM)
   ├── Ideia organizada (título, problema, solução, features, próximos passos)
   ├── Conversa completa
   └── Downloads (ZIP completo, JSON, Markdown, copiar)
```

---

## Início rápido

### Pré-requisitos

- **Docker** + **Docker Compose** instalados
- Chave de API de um provedor LLM: **Google Gemini** (recomendado, plano gratuito generoso) ou **OpenAI**

### Subir o projeto

```bash
git clone <seu-fork-aqui>
cd mesa-de-bar
cp .env.example .env
# edite o .env e coloque sua GOOGLE_API_KEY ou OPENAI_API_KEY
docker compose up --build
```

Abre em **`http://localhost:5173`**.

### Primeira sessão

1. Em **Configurações ⚙️**, confirme provider e cole sua chave de API.
2. Preencha **seu nome** e a **pauta principal** (ou clique "Me Dê uma Ideia").
3. Em **Sobre os Participantes**, clique **"Carregar Time de Template"** e escolha uma das 12 composições.
4. Escolha um **protocolo** (default já é bom para começar) e o **idioma**.
5. **Iniciar Discussão**.

Joga, encerra, baixa o ZIP no final.

---

## Configuração detalhada

### Variáveis de ambiente (`.env`)

```bash
# Pelo menos uma das duas é obrigatória
GOOGLE_API_KEY=sua_chave_gemini_aqui
OPENAI_API_KEY=sua_chave_openai_aqui

# Origens permitidas pro CORS (default cobre localhost:5173)
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### LLM no setup

Na engrenagem ⚙️ da tela de setup, você define:

- **Provedor** — `google` ou `openai`
- **Modelo** — sugestões:
  - `gemini-1.5-flash` (rápido, barato, plano gratuito)
  - `gemini-2.0-flash-exp` (mais rápido, ainda em preview)
  - `gpt-4o-mini` (alternativa balanceada)
  - `gpt-4o` (qualidade máxima, custo maior)
- **Chave de API** — fica salva localmente no `localStorage` do navegador

Cada **persona** pode ainda **sobrescrever** o provedor/modelo individualmente no editor.

---

## Composições de mesa

12 composições prontas em `compositions/*.yaml`. Cada uma traz 4 personas curadas com profundidade (papel + objetivo + instruções detalhadas):

1. **Filósofos clássicos** — Sócrates, Aristóteles, Nietzsche, Simone de Beauvoir
2. **Inventores e cientistas** — Tesla, Marie Curie, Einstein, Da Vinci
3. **Empreendedores tech** — Steve Jobs, Elon Musk, Jeff Bezos, Bill Gates
4. **Pensadoras feministas** — Beauvoir, Arendt, bell hooks, Angela Davis
5. **Artistas plásticos** — Picasso, Frida Kahlo, Basquiat, Yayoi Kusama
6. **Escritores latino-americanos** — Borges, Clarice, Machado, García Márquez
7. **Pioneiros da IA** — Turing, McCarthy, Hinton, LeCun
8. **Designers e arquitetos** — Niemeyer, Zaha Hadid, Dieter Rams, Lina Bo Bardi
9. **Líderes históricos** — Gandhi, MLK, Mandela, Lula
10. **Críticos contemporâneos** — Chomsky, Žižek, Byung-Chul Han, Krenak
11. **Cientistas sociais brasileiros** — Darcy Ribeiro, Florestan Fernandes, Lélia Gonzalez, Milton Santos
12. **Antagonistas saudáveis** — O Cético, O Otimista, O Pragmático, O Visionário

### Criar uma composição própria

```bash
cp compositions/filosofos_classicos.yaml compositions/minha_mesa.yaml
# editar id, title, description, e as 4 personas
```

Sem rebuild. Ao reabrir o setup, a composição aparece no modal.

---

## Protocolos experimentais

4 protocolos prontos em `protocols/*.yaml`:

| Protocolo | Manipulação |
|---|---|
| **`default`** | Configuração base, sem manipulação. |
| **`blind_personas`** | Personas aparecem como "Persona A/B/C/D" pro usuário (mas mantém identidade real internamente). |
| **`solo_baseline`** | Humano sozinho, sem IAs. Controle científico. |
| **`passive_waiter`** | Garçom só responde a comandos diretos. Sem desempate automático. |

Cada protocolo é um YAML que controla:

- Número e duração das 4 fases
- Sistema de drinks (incremento de temperatura, máximo)
- Modo do Garçom: `passive` / `active_arbiter` / `autonomous`
- Viés do Dono: `neutral` / `pro_winner` / `pro_human` / `pro_bidder`
- Modo de memória das personas: `none` / `private_memo` / `reflected_summary`
- Telemetria de digitação on/off
- Instrumentos pre/post sessão
- Idioma da sessão (`pt` / `en`)
- Flags experimentais: `blind_personas`, `solo_baseline`

Detalhes completos em **[docs/PROTOCOL.md](docs/PROTOCOL.md)**.

---

## Instrumentos de pesquisa

Questionários customizáveis em `instruments/*.yaml`, aplicados antes ou depois da sessão. Suporte a:

- Texto curto / longo
- Likert 1-N com rótulos
- Seleção única / múltipla
- Slider numérico
- Ranking drag-and-drop

Coletam telemetria por item (tempo gasto, ordem de resposta) além das respostas em si. Detalhes em **[docs/INSTRUMENTS.md](docs/INSTRUMENTS.md)**.

---

## O que sai no fim da sessão

Ao clicar **Baixar ZIP completo** na Tela 3, você recebe um arquivo com:

```
<session_id>/
├── README.md                  ← documentação auto-gerada
├── manifest.json              ← protocolo + LLM + composição + personas + prompts ativos
├── protocol.json              ← protocolo congelado
├── events.jsonl               ← cada decisão como evento (append-only)
├── llm_calls.jsonl            ← toda chamada LLM com prompt versionado e hash
├── transcript.json            ← conversa estruturada
├── transcript.md              ← conversa em markdown legível
├── final_idea.json            ← síntese + estruturação semântica
├── stats.json                 ← estatísticas agregadas (duração, stances, vitórias)
├── costs.json                 ← dashboard completo de custos LLM
├── ideia.md                   ← ideia organizada em markdown
└── instruments/
    ├── pre_session_*.json     ← respostas com telemetria por item
    └── post_session_*.json
```

Tudo o que precisa para análise científica completa fica num único arquivo. Sem dependência de banco ou serviços online.

### Carregando em pandas

```python
import json, pandas as pd
from pathlib import Path

# Eventos
events = [json.loads(l) for l in open("data/sessions/<sid>/events.jsonl")]
df_events = pd.DataFrame(events)

# Distribuição de stances
proposals = df_events[df_events["type"] == "round.proposal_submitted"]
stances = proposals["payload"].apply(lambda p: p.get("stance"))
print(stances.value_counts())

# Custos LLM
calls = [json.loads(l) for l in open("data/sessions/<sid>/llm_calls.jsonl")]
df_calls = pd.DataFrame(calls)
print(df_calls.groupby("prompt_id")["latency_ms"].mean())
```

---

## Arquitetura

```
┌────────────────────────────────────────────────────────────┐
│  Frontend (React + Vite)         Backend (FastAPI)         │
│                                                            │
│  SetupScreen        ─────►   /api/setup                    │
│  InstrumentForm     ─────►   /api/instruments/{id}         │
│  TableScreen        ─────►   /api/bid /pass /endorse /vote │
│  EndGameSummary     ─────►   /api/end                      │
│  SessionResults     ─────►   /api/sessions/{sid}/stats     │
│                              /api/sessions/{sid}/idea      │
│                              /api/sessions/{sid}/export    │
│                                                            │
└────────────────────────────┬───────────────────────────────┘
                             │
                             ▼
                  ┌────────────────────────┐
                  │  data/sessions/<id>/   │
                  │   (append-only logs +  │
                  │    snapshots JSON)     │
                  └────────────────────────┘
```

### Princípios de design

- **Sem banco de dados.** Cada sessão vive em uma pasta. `events.jsonl` e `llm_calls.jsonl` são append-only.
- **Protocolo é a unidade científica.** Manipular variáveis = trocar um YAML.
- **Prompts versionados e hashados.** Cada chamada LLM grava `prompt_id`, `prompt_version`, `prompt_hash` (sha256). Edita o prompt depois, sessões antigas seguem comparáveis pelo hash.
- **Reprodutibilidade.** `seed` no manifest, RNG seedado, snapshot dos prompts ativos no momento da criação.
- **Paralelismo.** Quando 4 IAs participam de uma rodada, todas chamam LLM ao mesmo tempo via `asyncio.gather()` — speedup 4-8x vs sequencial.

Detalhes completos em **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

---

## Estrutura do repositório

```
mesa-de-bar/
├── backend/
│   ├── app/
│   │   ├── core/          # config, ids, time, exceptions, parallel
│   │   ├── domain/        # modelos Pydantic puros
│   │   ├── persistence/   # IO de arquivos (paths, event_log, llm_log)
│   │   ├── prompts/       # registry + renderer Jinja2
│   │   ├── protocols/     # loader
│   │   ├── compositions/  # loader
│   │   ├── instruments/   # loader
│   │   ├── llm/           # manager (Google/OpenAI) + tasks
│   │   ├── game/          # phase_engine + randomization
│   │   ├── services/      # orquestração (game, costs, export, stats, ...)
│   │   └── routes/        # endpoints FastAPI
│   └── tests/             # pytest (34 testes)
│
├── frontend/
│   └── src/
│       ├── pages/         # SetupScreen, TableScreen, EndGameSummary, SessionResults
│       ├── components/    # WaiterBar, VotingPanel, ConversationPanel, ...
│       ├── i18n/          # pt.json, en.json + sistema mínimo
│       └── services/      # api.js
│
├── prompts/               # Jinja2 templates (proposal/, waiter_choose/, owner_summary_*/)
├── protocols/             # default.yaml, blind_personas.yaml, solo_baseline.yaml, ...
├── compositions/          # 12 composições de mesa
├── instruments/           # questionários pre_session e post_session
├── config/                # pricing.yaml (custos LLM por modelo)
├── data/sessions/         # uma pasta por sessão (sem versionar)
├── docs/                  # documentação técnica
└── docker-compose.yml
```

---

## Stack técnica

**Backend**
- Python 3.12, FastAPI, Uvicorn
- Pydantic v2 (validação de modelos)
- Jinja2 (templates de prompts)
- PyYAML (protocolos, instrumentos, composições)
- `google-generativeai` e `openai` (clientes LLM)
- pytest (34 testes)

**Frontend**
- React 18 + Vite
- Axios (HTTP)
- Remarkable (renderização Markdown)
- CSS puro com variáveis CSS (sem framework)
- Sistema mínimo de i18n próprio (sem deps externas)

**Infra**
- Docker Compose (2 serviços: backend + frontend)
- Volumes read-only para `prompts/`, `protocols/`, `compositions/`, `instruments/`, `config/`
- Volume read-write para `data/sessions/`

---

## Documentação técnica

Em **`docs/`**:

- **[README.md](docs/README.md)** — Visão geral
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** — Arquitetura, fluxo de dados, decisões de design
- **[PROTOCOL.md](docs/PROTOCOL.md)** — Como criar e validar um protocolo
- **[INSTRUMENTS.md](docs/INSTRUMENTS.md)** — Como criar instrumentos de pesquisa
- **[PROMPTS.md](docs/PROMPTS.md)** — Convenções, versionamento, tradução, hash
- **[EVENTS.md](docs/EVENTS.md)** — Referência completa dos eventos no `events.jsonl`

---

## Estado do projeto

### Fases implementadas

- ✅ **Fase 0** — Saneamento e estrutura base
- ✅ **Fase 1** — Persistência por arquivos, prompts versionados, RNG seedado
- ✅ **Fase 2A** — UI imersiva (mesa top-down, animações, ambiente de bar)
- ✅ **Fase 2B** — 4 atos, drinks, memória refletida, garçom modular, viés do dono, telemetria, dashboard de custos
- ✅ **Fase 3** — Instrumentos de pesquisa (6 tipos de pergunta, pre/post sessão)
- ✅ **Fase 4** — Exportação ZIP da sessão
- ✅ **Fase 5** — Múltiplos protocolos (4), i18n PT/EN, docs técnica completa
- ✅ **Fase 6** — Performance paralela (4-8x), prompt engineering com stance, 12 composições YAML, telas pós-conversa redesenhadas, ZIP completo

### O que ainda não tem (potenciais próximas fases)

- Streaming SSE das respostas das IAs (mostrar progressivamente cada IA respondendo)
- Modo multi-jogador (mais de um humano na mesma mesa)
- Comparação visual de sessões na própria UI
- Tradução completa dos prompts para mais idiomas além de PT/EN

---

## Licença e contribuição

Projeto de pesquisa. Sinta-se à vontade para clonar, adaptar e usar em seus próprios estudos. Issues e PRs bem-vindos.

Se for usar academicamente, considere citar a plataforma e referenciar este repositório.

---

**Mesa de Bar** — porque as melhores ideias sempre apareceram entre pessoas que se ouvem.
