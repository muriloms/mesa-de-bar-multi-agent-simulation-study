"""Export para o painel CAT (Consensual Assessment Technique).

Gera um bundle CEGO e EMBARALHADO: os juízes recebem só os textos das ideias
(sem braço, sem autoria, sem sessão) e avaliam novidade/qualidade/refinamento
em Likert-5. A chave de desanonimização fica num arquivo SEPARADO, aberto só
após a coleta das notas (preserva a cegueira do painel).

Padrão: avalia as IDEIAS FINAIS (síntese por sessão) — alvo clássico do CAT.
Opcionalmente inclui as propostas individuais.
"""
import csv
import io
import json
import random
from typing import List, Optional


CAT_RATING_FIELDS = ["novelty", "quality", "refinement"]  # Likert 1-5 (cego)


def build_cat_bundle(final_records: List[dict], *, seed: int = 12345,
                     proposal_records: Optional[List[dict]] = None) -> dict:
    """Monta itens cegos + chave. Retorna dict com csv/json em memória."""
    items_src = []
    for r in final_records:
        items_src.append({"kind": "final", "session_id": r["session_id"],
                          "arm": r.get("arm"), "topic": r.get("topic"),
                          "composition": r.get("composition"),
                          "text": r.get("final_text", "")})
    if proposal_records:
        for r in proposal_records:
            items_src.append({"kind": "proposal", "session_id": r["session_id"],
                              "arm": r.get("arm"), "topic": r.get("topic"),
                              "composition": r.get("composition"),
                              "round": r.get("round"),
                              "player_id": r.get("player_id"),
                              "author_type": r.get("author_type"),
                              "picked_by_judge": r.get("picked_by_judge"),
                              "picked_by_player": r.get("picked_by_player"),
                              "is_advanced": r.get("is_advanced"),
                              "text": r.get("idea_text", "")})

    # Embaralha de forma determinística (quebra qualquer ordem por condição)
    rng = random.Random(seed)
    rng.shuffle(items_src)

    items = []      # cego — vai pros juízes
    key = []        # desanonimização — separado
    for i, src in enumerate(items_src, start=1):
        item_id = f"item_{i:04d}"
        items.append({"item_id": item_id, "text": src["text"],
                      **{f: "" for f in CAT_RATING_FIELDS}})
        key.append({"item_id": item_id, "kind": src["kind"],
                    "session_id": src["session_id"], "arm": src.get("arm"),
                    "topic": src.get("topic"), "composition": src.get("composition"),
                    "round": src.get("round"), "player_id": src.get("player_id"),
                    "author_type": src.get("author_type"),
                    "picked_by_judge": src.get("picked_by_judge"),
                    "picked_by_player": src.get("picked_by_player"),
                    "is_advanced": src.get("is_advanced")})

    return {
        "items": items, "key": key,
        "items_csv": _to_csv(items, ["item_id", "text"] + CAT_RATING_FIELDS),
        "key_csv": _to_csv(key, ["item_id", "kind", "session_id", "arm",
                                 "topic", "composition", "round"]),
        "n_items": len(items),
        "rating_fields": CAT_RATING_FIELDS,
    }


def _to_csv(rows: List[dict], fieldnames: List[str]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    return buf.getvalue()


JUDGE_README = """# Painel CAT — instruções

Você recebeu um conjunto de ideias (coluna `text`), em ordem aleatória e SEM
qualquer informação sobre como foram geradas. Avalie cada ideia de forma
independente, comparando-as entre si (avaliação relativa), em 3 dimensões,
de 1 a 5:

- **novelty** (novidade): quão original/inesperada é a ideia.
- **quality** (qualidade): quão boa/valiosa ela é, no geral.
- **refinement** (refinamento): quão elaborada/bem-formada ela está.

Preencha as colunas `novelty`, `quality`, `refinement` (1 a 5). Não pesquise
as ideias nem tente adivinhar a origem. Confie na sua impressão de especialista.
"""
