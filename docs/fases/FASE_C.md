# Fase C — Avaliação automática + export CAT

Camada de análise **offline** (separada do jogo ao vivo) que lê as sessões em
disco e produz métricas de criatividade por distância semântica, além do bundle
cego pro painel CAT.

## Foco: originalidade e flexibilidade
Seguindo a literatura (fluência/elaboração são manipuláveis com LLM no circuito),
medimos:
- **Originalidade** de cada ideia: distância semântica média às demais do mesmo
  pool (rodada/sessão) e ao tópico.
- **Flexibilidade/diversidade** do pool: distância média par-a-par das propostas
  — baixa = homogeneização (medida central de H2).
- **Distintividade da ideia final**: distância ao centroide das ideias finais do
  mesmo tópico (cross-sessão).
- **Concordância juiz×jogador** por braço (preparação pra validação da Fase D).

## Embeddings plugáveis (com cache)
`MDB_EMBED_BACKEND`:
- `google` (default): API `text-embedding-004` (multilíngue, determinístico).
  Chave em `MDB_EMBED_API_KEY` ou `GOOGLE_API_KEY`.
- `local`: sentence-transformers `paraphrase-multilingual-MiniLM-L12-v2`
  (offline, reprodutível; requer `pip install sentence-transformers`).
- `hash`: pseudo-embedding determinístico (sem rede) — só testes/dev.

Cache append-only em `data/analysis/embeddings_cache.jsonl` (não recomputa).

## Export CAT (cego)
Bundle pro painel CAT (5-8 juízes, Likert-5):
- `cat_items.csv`: itens EMBARALHADOS, só `item_id` + `text` + colunas vazias
  `novelty`/`quality`/`refinement`. Sem braço, sem autoria, sem sessão.
- `cat_key.csv`: chave de desanonimização (item_id → sessão/braço/tópico),
  **separada** — aberta só após coletar as notas.
- `cat_README.md`: instruções pros juízes.
Padrão: avalia as ideias finais (alvo clássico do CAT); `--include-proposals`
adiciona as propostas individuais.

## Como rodar
CLI (offline):
```
cd backend/app
python -m analysis.run --study main --backend google --out ../../data/analysis
```
Saídas: `report.json`, `report.md`, `ideas.json`, `cat_items.csv`, `cat_key.csv`,
`cat_README.md`.

Endpoints:
- `GET /api/analysis/report?study_id=&backend=` — métricas por braço (usa embeddings).
- `GET /api/studies/<id>/cat-export?include_proposals=` — ZIP do bundle CAT (rápido, sem embeddings).

## Pendente (Fase D)
- Painel CAT humano cego (ferramenta separada de coleta de notas).
- Validação cruzada: concordância juiz-IA × notas humanas (correlação, kappa).
- `stats.py` da v1 segue inalterado; a análise nova vive em `analysis/`.
