# Estudos (desenhos experimentais)

Cada `studies/<id>.yaml` define um estudo: braços (protocolos), banco de
tópicos padronizado e composições de mesa. O runner (`POST /api/study/start`)
atribui cada participante a uma célula **braço × tópico × composição** de forma
balanceada (round-robin aninhado, empate pela ordem listada), registrando no
ledger append-only `data/studies/<id>/assignments.jsonl`.

- `assignment: balanced` — menos-preenchido primeiro (reprodutível).
- `blind_condition: true` — participante não vê/escolhe a condição.
- Balanceamento e contagens: `GET /api/studies/<id>/balance`.

Sandbox livre: para testes sem estudo, use o setup normal (tópico/personas
livres) — fora de qualquer estudo.
