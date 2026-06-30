# Fase D — Painel CAT cego + validação juiz-IA × humano

Fecha o argumento metodológico: juízes humanos avaliam as ideias às cegas, e a
gente checa se o juiz-IA (e as métricas automáticas) concordam com o consenso.

## Painel CAT (ferramenta cega, separada)
- Tela isolada no front, acessada por URL dedicada: `?cat=<study_id>`. Sem
  nenhum elemento do jogo. O juiz se identifica, recebe as ideias EMBARALHADAS
  (só texto) e avalia cada uma de 1 a 5 em novidade/qualidade/refinamento.
- Bundle materializado uma vez por estudo (item_ids estáveis entre juízes) em
  `data/cat/<study_id>/` (items.json + key.json). A chave (item→condição)
  NUNCA é servida pro juiz.
- Notas em `data/cat/<study_id>/ratings.jsonl` (append-only, por juiz).
- Endpoints: `POST /api/cat/<id>/materialize`, `GET /api/cat/<id>/items`,
  `POST /api/cat/<id>/ratings`, `GET /api/cat/<id>/validation`.

## Validação (analysis/cat_validation.py)
- **Confiabilidade entre juízes**: alpha de Cronbach por dimensão e composto
  (padrão do CAT; juízes como medidas, ideias como sujeitos, listwise).
- **Escore CAT humano por item**: média entre juízes (composto = média das 3
  dimensões).
- **Validade do juiz-IA**: por rodada, a proposta escolhida pelo juiz-IA bate
  com a de maior CAT humano? → `judge_ia_hit_rate`. Idem pra escolha do jogador
  (`player_hit_rate`) — contraste direto.
- **CAT humano por braço**: responde à RQ-Output (qualidade do output por
  condição).
- **Validade das métricas automáticas** (opcional): correlação (Pearson/
  Spearman) entre originalidade automática e novidade humana.

## Como usar
1. Colete sessões (runner da Fase B).
2. `POST /api/cat/<id>/materialize?include_proposals=true` (operador).
3. Mande a cada juiz a URL `…/?cat=<id>` (5-8 juízes).
4. `GET /api/cat/<id>/validation` para o relatório.

## Estado da v2
Fases A-D completas: loop de rodada → camada experimental (runner/CoT/
composições) → avaliação automática (embeddings + export CAT) → painel CAT +
validação. 53 testes no backend; frontend buildando limpo.
