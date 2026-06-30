# Mesa de Bar

Plataforma científica de co-criação humano-IA. O usuário entra numa "mesa de bar" virtual com 1-4 personas IA customizáveis, defende suas ideias com apostas (sinal de confiança), e ao fim da noite o "Dono do Bar" sintetiza tudo numa ideia final estruturada.

A plataforma é desenhada como **research-in-a-box**: um pesquisador clona o repositório, sobe `docker compose up`, joga e baixa um ZIP com todos os dados pra análise. Sem banco de dados, sem cadastro — uma sessão = uma pasta em `data/sessions/<id>/`.

## Início rápido

```bash
git clone <repo>
cd mesa-de-bar
cp .env.example .env  # adicione sua chave de API
docker compose up --build
# abre http://localhost:5173
```

Ao final de uma sessão, clique **⤓ Baixar dados** pra exportar tudo em ZIP.

## Conceitos centrais

**Personas IA**: 4 caracteres (Sócrates, Tesla, etc) com role/goal/instructions custom. Cada uma propõe ideias na sua identidade. Você pode usar um time pronto, gerar com IA a partir de um tema, ou montar um por persona.

**Aposta como sinal**: cada vez que você (ou uma IA) propõe uma ideia, aposta dinheiro nela. Apostas altas = "tô confiante". Vencedor da rodada leva o pote. **Drinks** acumulados pelo vencedor aumentam a temperatura do LLM dela na próxima rodada — analogia gameplay-style com a embriaguez progressiva de uma mesa de bar.

**Garçom**: árbitro neutro. Pode votar por você (delegação), resumir o que rolou até agora, provocar a mesa com uma pergunta, ou desempatar quando duas apostas são parecidas. Modos: passivo / árbitro ativo / autônomo (configurado por protocolo).

**Dono do Bar**: sintetizador final. Lê todo o histórico e escreve a ideia final. Pode ter viés configurável: neutral (default), pro_winner, pro_human, pro_bidder.

**4 atos**: warmup (sem aposta) → discussion → convergence (aposta dobrada) → closing (síntese).

## Estrutura científica

A plataforma foi feita pra rodar **estudos comparativos**. Cada sessão registra:

- `events.jsonl` — toda decisão como evento timestampado
- `llm_calls.jsonl` — toda chamada LLM com prompt versionado, tokens, latência, custo
- `transcript.json/md` — conversa final estruturada
- `instruments/*.json` — respostas a questionários pré e pós-sessão
- `manifest.json` — metadados (seed, protocolo, modelo, idioma)

Variáveis manipuláveis via **protocolo** (YAML em `protocols/`):
- Número e duração das fases
- Comportamento do Garçom e Dono
- Memória das personas
- Visibilidade da identidade das IAs (`blind_personas`)
- Presença das IAs (`solo_baseline`)
- Telemetria de digitação on/off
- Idioma (PT/EN)

## Documentação

- **[ARCHITECTURE.md](ARCHITECTURE.md)** — visão da arquitetura, fluxo de dados, decisões de design
- **[PROTOCOL.md](PROTOCOL.md)** — como criar e validar um protocolo
- **[INSTRUMENTS.md](INSTRUMENTS.md)** — como criar instrumentos de pesquisa
- **[PROMPTS.md](PROMPTS.md)** — convenções, versionamento, tradução
- **[EVENTS.md](EVENTS.md)** — referência completa dos eventos

## Estado atual

Fases implementadas:
- ✅ Fase 0 — saneamento e estrutura
- ✅ Fase 1 — persistência por arquivos, prompts versionados, RNG com seed
- ✅ Fase 2A — UI imersiva (mesa top-down, animações, ambiente)
- ✅ Fase 2B — 4 atos, drinks, memória refletida, garçom modular, viés do dono, Passar/Endossar, telemetria, dashboard de custos
- ✅ Fase 3 — instrumentos de pesquisa (pré e pós-sessão, 6 tipos de pergunta)
- ✅ Fase 4 — exportação ZIP da sessão
- ✅ Fase 5 — múltiplos protocolos, i18n PT/EN, docs
