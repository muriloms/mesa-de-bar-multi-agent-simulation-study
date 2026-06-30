"""Testes da camada de análise (Fase C). Backend de embedding = hash (offline)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))


def _patch_data(tmp_path, monkeypatch):
    from core import config
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "SESSIONS_DIR", tmp_path / "sessions")
    monkeypatch.setenv("MDB_EMBED_BACKEND", "hash")


# ---- métricas ----
def test_cosine_and_diversity():
    from analysis import metrics
    a = [1.0, 0.0]; b = [1.0, 0.0]; c = [0.0, 1.0]
    assert abs(metrics.cosine_sim(a, b) - 1.0) < 1e-9
    assert abs(metrics.cosine_dist(a, c) - 1.0) < 1e-9
    # diversidade de {a,b} (iguais) = 0; de {a,c} (ortogonais) = 1
    assert abs(metrics.diversity([a, b]) - 0.0) < 1e-9
    assert abs(metrics.diversity([a, c]) - 1.0) < 1e-9
    assert metrics.diversity([a]) is None  # < 2 itens


def test_originality_vs_pool():
    from analysis import metrics
    a = [1.0, 0.0]; b = [1.0, 0.0]; c = [0.0, 1.0]
    # 'c' é ortogonal aos outros dois → originalidade alta (~1.0)
    assert abs(metrics.originality_vs_pool(c, [a, b]) - 1.0) < 1e-9
    # 'a' é igual a 'b' e ortogonal a 'c' → média = 0.5
    assert abs(metrics.originality_vs_pool(a, [b, c]) - 0.5) < 1e-9


def test_hash_embedding_deterministic(tmp_path, monkeypatch):
    _patch_data(tmp_path, monkeypatch)
    from analysis.embeddings import EmbeddingProvider
    e = EmbeddingProvider(backend="hash")
    v1 = e.embed("uma ideia qualquer")
    v2 = e.embed("uma ideia qualquer")
    assert v1 == v2
    assert len(v1) == 64
    assert e.embed("outra ideia") != v1


def _make_session(root, sid, arm, topic, comp, ideas_by_round, final_text,
                  advanced_pid_by_round, study_id="main"):
    d = root / "sessions" / sid
    d.mkdir(parents=True)
    manifest = {
        "session_id": sid, "protocol_id": arm, "topic": topic,
        "personas": ["Tesla", "Sócrates"], "user_name": "Mateus",
        "quem_avanca": "juiz_ia", "source_blind_on_choice": True,
        "judge_criterion": "originalidade",
        "study": {"study_id": study_id, "arm": arm, "topic": topic,
                  "composition": comp, "cell": f"{arm}|{topic}|{comp}"},
    }
    (d / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    events = []
    eid = 0
    for rnd, ideas in ideas_by_round.items():
        for pid, (text, actor) in ideas.items():
            eid += 1
            events.append({"event_id": f"e{eid}", "type": "round.proposal_submitted",
                           "actor": actor, "round": rnd,
                           "payload": {"player_id": pid, "idea_text": text,
                                       "reasoning_mode": "direct"}})
        adv = advanced_pid_by_round.get(rnd)
        events.append({"event_id": f"a{rnd}", "type": "judge.picked", "round": rnd,
                       "payload": {"player_id": adv}})
        events.append({"event_id": f"p{rnd}", "type": "player.picked", "round": rnd,
                       "actor": "user", "payload": {"player_id": adv}})
        events.append({"event_id": f"c{rnd}", "type": "round.choices_compared", "round": rnd,
                       "payload": {"match": True}})
        events.append({"event_id": f"ad{rnd}", "type": "round.idea_advanced", "round": rnd,
                       "payload": {"advanced_player_id": adv}})
    (d / "events.jsonl").write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")
    (d / "final_idea.json").write_text(
        json.dumps({"summary": final_text, "lab_idea": None}), encoding="utf-8")


def test_end_to_end_report_and_cat(tmp_path, monkeypatch):
    _patch_data(tmp_path, monkeypatch)
    from analysis import report as rep_mod
    from analysis.cat_export import build_cat_bundle

    root = tmp_path
    _make_session(root, "s1", "default", "Transporte", "pioneiros_ia",
                  {1: {1: ("ideia humana A", "user"), 2: ("ideia tesla A", "ai_2"), 3: ("ideia socrates A", "ai_3")},
                   2: {1: ("ideia humana B", "user"), 2: ("ideia tesla B", "ai_2"), 3: ("ideia socrates B", "ai_3")}},
                  "Sintese final da sessao 1", {1: 2, 2: 2})
    _make_session(root, "s2", "jogador_avanca", "Transporte", "pioneiros_ia",
                  {1: {1: ("ideia humana C", "user"), 2: ("ideia tesla C", "ai_2"), 3: ("ideia socrates C", "ai_3")}},
                  "Sintese final da sessao 2", {1: 1})

    report = rep_mod.analyze(backend="hash")
    assert report["n_sessions"] == 2
    assert report["n_ideas"] == 9
    assert report["n_finals"] == 2
    assert set(report["arms"]) == {"default", "jogador_avanca"}
    # cada braço tem métricas
    for arm in report["arms"]:
        a = report["by_arm"][arm]
        assert a["n_sessions"] >= 1
        assert a["originality_pool_mean"] is not None
    # markdown gera sem erro
    md = rep_mod.to_markdown(report)
    assert "Relatório de análise" in md

    # CAT bundle: cego, embaralhado, sem vazar condição
    finals = [{k: v for k, v in f.items() if not k.startswith("_")} for f in report["finals"]]
    bundle = build_cat_bundle(finals, seed=7)
    assert bundle["n_items"] == 2
    for item in bundle["items"]:
        # item cego não pode conter arm/topic/session_id
        assert "arm" not in item and "topic" not in item and "session_id" not in item
        assert "item_id" in item and "text" in item
        assert item["novelty"] == "" and item["quality"] == "" and item["refinement"] == ""
    # a chave (separada) preserva a condição
    key_arms = {k["arm"] for k in bundle["key"]}
    assert key_arms == {"default", "jogador_avanca"}
