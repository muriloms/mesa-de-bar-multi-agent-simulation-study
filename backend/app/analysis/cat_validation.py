"""Validação do painel CAT: confiabilidade entre juízes + juiz-IA × humano.

- Confiabilidade entre juízes: alpha de Cronbach por dimensão (padrão do CAT).
- Escore CAT humano por item: média das notas entre juízes (composto = média
  das 3 dimensões).
- Validade do juiz-IA: por rodada, a proposta escolhida pelo juiz-IA bate com a
  de maior CAT humano? (hit-rate). Idem pra escolha do jogador.
- CAT humano por braço: responde a RQ-Output (qualidade do output por condição).
- (Opcional) correlação das métricas automáticas com as notas humanas.
"""
import math
from collections import defaultdict
from typing import Dict, List, Optional

DIMS = ("novelty", "quality", "refinement")


# --------------------------- estatística ---------------------------
def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def _var(xs, ddof=1):
    xs = [x for x in xs if x is not None]
    n = len(xs)
    if n < 2:
        return None
    m = sum(xs) / n
    return sum((x - m) ** 2 for x in xs) / (n - ddof)


def pearson(xs, ys):
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    n = len(pairs)
    if n < 3:
        return None
    mx = sum(p[0] for p in pairs) / n
    my = sum(p[1] for p in pairs) / n
    num = sum((x - mx) * (y - my) for x, y in pairs)
    dx = math.sqrt(sum((x - mx) ** 2 for x, _ in pairs))
    dy = math.sqrt(sum((y - my) ** 2 for _, y in pairs))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def _rank(values):
    # ranks médios (lida com empates)
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def spearman(xs, ys):
    pairs = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pairs) < 3:
        return None
    rx = _rank([p[0] for p in pairs])
    ry = _rank([p[1] for p in pairs])
    return pearson(rx, ry)


def cronbach_alpha(matrix: List[List[float]]) -> Optional[float]:
    """matrix: linhas = itens (sujeitos), colunas = juízes (medidas). Listwise."""
    rows = [r for r in matrix if all(v is not None for v in r)]
    if len(rows) < 2 or not rows[0]:
        return None
    k = len(rows[0])
    if k < 2:
        return None
    col_vars = []
    for c in range(k):
        col_vars.append(_var([r[c] for r in rows]) or 0.0)
    totals = [sum(r) for r in rows]
    total_var = _var(totals)
    if not total_var:
        return None
    return (k / (k - 1)) * (1 - sum(col_vars) / total_var)


# --------------------------- validação ---------------------------
def validate(study_id: str, auto_orig_by_item: Optional[Dict[str, float]] = None) -> dict:
    from services import cat_service

    ratings = cat_service.load_ratings(study_id)
    key = {k["item_id"]: k for k in cat_service.get_key(study_id)}

    judges = sorted({r["judge_id"] for r in ratings})
    items = sorted({r["item_id"] for r in ratings})

    # nota por (item, judge, dim)
    by_item_judge: Dict[str, Dict[str, dict]] = defaultdict(dict)
    for r in ratings:
        by_item_judge[r["item_id"]][r["judge_id"]] = r

    # escore humano por item (média entre juízes)
    human: Dict[str, dict] = {}
    for it in items:
        per_dim = {}
        for d in DIMS:
            per_dim[d] = _mean([by_item_judge[it][j].get(d)
                                for j in by_item_judge[it]])
        comp_vals = [per_dim[d] for d in DIMS if per_dim[d] is not None]
        human[it] = {**per_dim,
                     "composite": (sum(comp_vals) / len(comp_vals)) if comp_vals else None,
                     "n_judges": len(by_item_judge[it])}

    # confiabilidade entre juízes (alpha) por dimensão — listwise
    irr = {}
    for d in DIMS:
        matrix = []
        for it in items:
            row = [by_item_judge[it].get(j, {}).get(d) for j in judges]
            matrix.append(row)
        irr[d] = cronbach_alpha(matrix)
    # composto
    comp_matrix = []
    for it in items:
        row = []
        for j in judges:
            rec = by_item_judge[it].get(j)
            if rec:
                vals = [rec.get(d) for d in DIMS if rec.get(d) is not None]
                row.append(sum(vals) / len(vals) if vals else None)
            else:
                row.append(None)
        comp_matrix.append(row)
    irr["composite"] = cronbach_alpha(comp_matrix)

    # validade do juiz-IA: por (sessão, rodada) entre PROPOSTAS
    rounds: Dict[tuple, List[str]] = defaultdict(list)
    for it in items:
        k = key.get(it, {})
        if k.get("kind") == "proposal" and k.get("round") is not None:
            rounds[(k["session_id"], k["round"])].append(it)

    judge_hits = judge_total = player_hits = player_total = 0
    for (sid, rnd), pool in rounds.items():
        scored = [(it, human[it]["composite"]) for it in pool if human[it]["composite"] is not None]
        if len(scored) < 2:
            continue
        human_top = max(scored, key=lambda x: x[1])[0]
        ai_pick = next((it for it in pool if key.get(it, {}).get("picked_by_judge")), None)
        pl_pick = next((it for it in pool if key.get(it, {}).get("picked_by_player")), None)
        if ai_pick is not None:
            judge_total += 1
            if ai_pick == human_top:
                judge_hits += 1
        if pl_pick is not None:
            player_total += 1
            if pl_pick == human_top:
                player_hits += 1

    # CAT humano por braço (finais)
    by_arm_finals: Dict[str, List[float]] = defaultdict(list)
    for it in items:
        k = key.get(it, {})
        if k.get("kind") == "final" and human[it]["composite"] is not None:
            by_arm_finals[k.get("arm")].append(human[it]["composite"])
    arm_cat = {arm: {"mean_composite": _mean(v), "n": len(v)}
               for arm, v in by_arm_finals.items()}

    # correlação métrica automática × novidade humana (opcional)
    auto_corr = None
    if auto_orig_by_item:
        xs, ys = [], []
        for it in items:
            if it in auto_orig_by_item and human[it].get("novelty") is not None:
                xs.append(auto_orig_by_item[it])
                ys.append(human[it]["novelty"])
        auto_corr = {"pearson": pearson(xs, ys), "spearman": spearman(xs, ys), "n": len(xs)}

    return {
        "study_id": study_id,
        "n_judges": len(judges), "judges": judges,
        "n_items_rated": len(items),
        "irr_cronbach_alpha": irr,
        "judge_ia_hit_rate": (judge_hits / judge_total) if judge_total else None,
        "judge_ia_rounds": judge_total,
        "player_hit_rate": (player_hits / player_total) if player_total else None,
        "player_rounds": player_total,
        "human_cat_by_arm": arm_cat,
        "auto_metric_vs_human_novelty": auto_corr,
        "per_item": human,
    }
