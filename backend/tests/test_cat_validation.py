"""Testes da Fase D: estatística de validação + fluxo CAT end-to-end."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))


def _patch_data(tmp_path, monkeypatch):
    from core import config
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "SESSIONS_DIR", tmp_path / "sessions")
    monkeypatch.setenv("MDB_EMBED_BACKEND", "hash")


# ---- estatística ----
def test_cronbach_alpha_perfect_agreement():
    from analysis.cat_validation import cronbach_alpha
    # dois juízes idênticos, itens com variância → alpha = 1
    matrix = [[1, 1], [3, 3], [5, 5], [2, 2]]
    a = cronbach_alpha(matrix)
    assert a is not None and abs(a - 1.0) < 1e-9


def test_cronbach_alpha_needs_two_judges():
    from analysis.cat_validation import cronbach_alpha
    assert cronbach_alpha([[1], [2], [3]]) is None


def test_pearson_and_spearman():
    from analysis.cat_validation import pearson, spearman
    xs = [1, 2, 3, 4, 5]; ys = [2, 4, 6, 8, 10]
    assert abs(pearson(xs, ys) - 1.0) < 1e-9
    assert abs(spearman(xs, ys) - 1.0) < 1e-9
    ys2 = [10, 8, 6, 4, 2]
    assert abs(pearson(xs, ys2) + 1.0) < 1e-9


def _make_session_with_proposals(root, sid):
    d = root / "sessions" / sid
    d.mkdir(parents=True)
    manifest = {
        "session_id": sid, "protocol_id": "default", "topic": "T",
        "personas": ["Tesla", "Sokrates"], "user_name": "Mateus",
        "study": {"study_id": "main", "arm": "default", "topic": "T",
                  "composition": "c1"},
    }
    (d / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    events = []
    # 2 rodadas, 3 propostas cada; juiz-IA escolhe player 2 nas duas
    for rnd in (1, 2):
        for pid, actor in [(1, "user"), (2, "ai_2"), (3, "ai_3")]:
            events.append({"type": "round.proposal_submitted", "actor": actor,
                           "round": rnd, "payload": {"player_id": pid,
                           "idea_text": f"r{rnd} ideia do player {pid}"}})
        events.append({"type": "judge.picked", "round": rnd, "payload": {"player_id": 2}})
        events.append({"type": "player.picked", "round": rnd, "actor": "user",
                       "payload": {"player_id": 2}})
        events.append({"type": "round.choices_compared", "round": rnd, "payload": {"match": True}})
        events.append({"type": "round.idea_advanced", "round": rnd, "payload": {"advanced_player_id": 2}})
    (d / "events.jsonl").write_text("\n".join(json.dumps(e) for e in events), encoding="utf-8")
    (d / "final_idea.json").write_text(json.dumps({"summary": "sintese final", "lab_idea": None}), encoding="utf-8")


def test_cat_flow_and_judge_ia_hit_rate(tmp_path, monkeypatch):
    _patch_data(tmp_path, monkeypatch)
    from services import cat_service
    from analysis import cat_validation as cv

    _make_session_with_proposals(tmp_path, "s1")

    # materializa bundle com propostas
    cat_service.materialize_bundle("main", include_proposals=True, refresh=True)
    items = cat_service.get_items("main")
    # itens cegos não vazam condição
    for it in items:
        assert set(it.keys()) == {"item_id", "text"}

    key = {k["item_id"]: k for k in cat_service.get_key("main")}

    # mapeia (round, player_id) -> item_id pras propostas
    prop = {(k["round"], k["player_id"]): iid for iid, k in key.items() if k["kind"] == "proposal"}

    # Ratings de 2 juízes. Round 1: player 2 (=pick do juiz-IA) é o TOP humano.
    # Round 2: player 3 é o top (juiz-IA erra). hit-rate esperado = 0.5
    def rate(scores):  # scores: (round,pid)->composite (usa o mesmo nas 3 dims)
        out = []
        for (rnd, pid), val in scores.items():
            out.append({"item_id": prop[(rnd, pid)], "novelty": val, "quality": val, "refinement": val})
        return out

    scoresJ1 = {(1,1):2,(1,2):5,(1,3):3, (2,1):2,(2,2):3,(2,3):5}
    scoresJ2 = {(1,1):3,(1,2):5,(1,3):2, (2,1):2,(2,2):4,(2,3):5}
    # também avalia o item FINAL (necessário pro CAT por braço)
    final_iid = next(iid for iid, k in key.items() if k["kind"] == "final")
    r1 = rate(scoresJ1) + [{"item_id": final_iid, "novelty": 4, "quality": 4, "refinement": 4}]
    r2 = rate(scoresJ2) + [{"item_id": final_iid, "novelty": 4, "quality": 5, "refinement": 3}]
    cat_service.submit_ratings("main", "juizA", r1)
    cat_service.submit_ratings("main", "juizB", r2)

    rep = cv.validate("main")
    assert rep["n_judges"] == 2
    assert rep["judge_ia_rounds"] == 2
    assert abs(rep["judge_ia_hit_rate"] - 0.5) < 1e-9   # acerta R1, erra R2
    # alpha calculado (composto) — 2 juízes razoavelmente concordantes
    assert rep["irr_cronbach_alpha"]["composite"] is not None
    # CAT humano por braço presente
    assert "default" in rep["human_cat_by_arm"]
    assert rep["human_cat_by_arm"]["default"]["n"] >= 1
