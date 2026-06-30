"""Orquestra a análise: embeddings → métricas por ideia/sessão → agregação por braço."""
from collections import defaultdict
from typing import Dict, List, Optional

from analysis import dataset, metrics
from analysis.embeddings import EmbeddingProvider


def _group_by(rows, key):
    g = defaultdict(list)
    for r in rows:
        g[r.get(key)].append(r)
    return g


def analyze(session_ids: Optional[List[str]] = None,
            study_id: Optional[str] = None,
            backend: Optional[str] = None) -> dict:
    sessions = dataset.load_all(session_ids)
    if study_id:
        sessions = [s for s in sessions if s["condition"].get("study_id") == study_id]

    ideas = dataset.flatten_ideas(sessions)
    finals = dataset.final_ideas(sessions)

    emb = EmbeddingProvider(backend=backend)

    # --- embeddings ---
    for it in ideas:
        it["_vec"] = emb.embed(it["idea_text"])
    topic_vecs: Dict[str, List[float]] = {}
    for it in ideas:
        tp = it.get("topic") or ""
        if tp and tp not in topic_vecs:
            topic_vecs[tp] = emb.embed(tp)
    for fr in finals:
        fr["_vec"] = emb.embed(fr["final_text"])

    # --- originalidade por ideia (vs pool da rodada/sessão e vs tópico) ---
    by_session_round = _group_by(ideas, "session_id")
    pools: Dict[tuple, List[dict]] = defaultdict(list)
    for it in ideas:
        pools[(it["session_id"], it["round"])].append(it)
    for it in ideas:
        pool = pools[(it["session_id"], it["round"])]
        others = [o["_vec"] for o in pool if o is not it]
        it["orig_vs_pool"] = metrics.originality_vs_pool(it["_vec"], others)
        it["orig_vs_topic"] = metrics.originality_vs_topic(
            it["_vec"], topic_vecs.get(it.get("topic") or ""))

    # --- diversidade por sessão (flexibilidade do pool de propostas) ---
    session_diversity: Dict[str, Optional[float]] = {}
    session_arm: Dict[str, Optional[str]] = {}
    for sid, group in by_session_round.items():
        session_diversity[sid] = metrics.diversity([g["_vec"] for g in group])
        session_arm[sid] = group[0].get("arm") if group else None

    # --- distintividade da ideia final (distância ao centroide do mesmo tópico) ---
    finals_by_topic = _group_by(finals, "topic")
    for fr in finals:
        same_topic = [f["_vec"] for f in finals_by_topic[fr.get("topic")]]
        fr["distinctiveness"] = metrics.centroid_distance(fr["_vec"], same_topic)

    # --- agregação por braço ---
    arms = sorted({it.get("arm") for it in ideas if it.get("arm")})
    by_arm = {}
    for arm in arms:
        arm_ideas = [it for it in ideas if it.get("arm") == arm]
        arm_sessions = [sid for sid, a in session_arm.items() if a == arm]
        arm_finals = [f for f in finals if f.get("arm") == arm]
        # concordância juiz × jogador (entre rodadas com comparação registrada)
        matches = [it["judge_match"] for it in arm_ideas
                   if it["judge_match"] is not None and it["picked_by_player"]]
        # human originality vs persona originality (no pool)
        human = [it["orig_vs_pool"] for it in arm_ideas if it["author_type"] == "human"]
        persona = [it["orig_vs_pool"] for it in arm_ideas if it["author_type"] == "persona"]
        by_arm[arm] = {
            "n_sessions": len(set(it["session_id"] for it in arm_ideas)),
            "n_ideas": len(arm_ideas),
            "originality_pool_mean": metrics.mean([it["orig_vs_pool"] for it in arm_ideas]),
            "originality_topic_mean": metrics.mean([it["orig_vs_topic"] for it in arm_ideas]),
            "diversity_mean": metrics.mean([session_diversity[s] for s in arm_sessions]),
            "diversity_sd": metrics.stdev([session_diversity[s] for s in arm_sessions]),
            "final_distinctiveness_mean": metrics.mean([f.get("distinctiveness") for f in arm_finals]),
            "human_originality_mean": metrics.mean(human),
            "persona_originality_mean": metrics.mean(persona),
            "judge_player_match_rate": metrics.mean([1.0 if m else 0.0 for m in matches]),
        }

    return {
        "backend": emb.backend,
        "n_sessions": len(sessions),
        "n_ideas": len(ideas),
        "n_finals": len(finals),
        "arms": arms,
        "by_arm": by_arm,
        "session_diversity": session_diversity,
        "ideas": ideas,
        "finals": finals,
    }


def to_markdown(report: dict) -> str:
    lines = ["# Relatório de análise — Mesa de Bar (Fase C)", ""]
    lines.append(f"- Backend de embedding: `{report['backend']}`")
    lines.append(f"- Sessões: {report['n_sessions']} · Ideias: {report['n_ideas']} · Ideias finais: {report['n_finals']}")
    lines.append("")
    lines.append("## Por braço (condição)")
    lines.append("")
    lines.append("| Braço | N sess | Originalidade (pool) | Diversidade (↓=homogêneo) | Distintividade final | Concord. juiz×jogador |")
    lines.append("|---|---|---|---|---|---|")
    def fmt(x): return f"{x:.3f}" if isinstance(x, (int, float)) else "—"
    for arm in report["arms"]:
        a = report["by_arm"][arm]
        lines.append(f"| {arm} | {a['n_sessions']} | {fmt(a['originality_pool_mean'])} | "
                     f"{fmt(a['diversity_mean'])} | {fmt(a['final_distinctiveness_mean'])} | "
                     f"{fmt(a['judge_player_match_rate'])} |")
    lines.append("")
    lines.append("> Diversidade = distância semântica média par-a-par no pool de propostas "
                 "(flexibilidade). Valores menores indicam homogeneização (H2). "
                 "Originalidade = distância média de cada ideia às demais do mesmo pool.")
    return "\n".join(lines)
