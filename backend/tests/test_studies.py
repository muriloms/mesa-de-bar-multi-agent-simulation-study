"""Testes do runner experimental: loader de estudos + atribuição balanceada."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))


def _patch_data(tmp_path, monkeypatch):
    from core import config
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "SESSIONS_DIR", tmp_path / "sessions")


def test_list_studies_includes_main():
    from studies.loader import list_studies
    ids = [s["id"] for s in list_studies()]
    assert "main" in ids
    assert "cot_homogeneizacao" in ids


def test_load_main_study():
    from studies.loader import load_study
    s = load_study("main")
    assert s.arms == ["default", "jogador_avanca"]
    assert len(s.topics) == 6
    assert "pessoas_comuns_brasil" in s.compositions
    assert s.assignment == "balanced"
    assert s.blind_condition is True


def test_balanced_assignment_spreads_across_arms(tmp_path, monkeypatch):
    _patch_data(tmp_path, monkeypatch)
    from domain.study import Study
    from services import assignment as asg

    study = Study(id="t1", arms=["A", "B", "C"], topics=["x", "y"],
                  compositions=[], assignment="balanced")
    # 9 atribuições → 3 por braço (round-robin balanceado)
    arms = [asg.assign(study).arm for _ in range(9)]
    counts = {a: arms.count(a) for a in ["A", "B", "C"]}
    assert counts == {"A": 3, "B": 3, "C": 3}, counts


def test_balanced_nesting_topic_within_arm(tmp_path, monkeypatch):
    _patch_data(tmp_path, monkeypatch)
    from domain.study import Study
    from services import assignment as asg

    study = Study(id="t2", arms=["A", "B"], topics=["x", "y"],
                  compositions=[], assignment="balanced")
    # 8 atribuições → cada (arm,topic) deve aparecer 2x
    cells = {}
    for _ in range(8):
        a = asg.assign(study)
        key = (a.arm, a.topic)
        cells[key] = cells.get(key, 0) + 1
    assert all(v == 2 for v in cells.values()), cells
    assert len(cells) == 4  # 2 arms × 2 topics


def test_balance_report(tmp_path, monkeypatch):
    _patch_data(tmp_path, monkeypatch)
    from domain.study import Study
    from services import assignment as asg

    study = Study(id="t3", arms=["A", "B"], topics=[], compositions=[],
                  assignment="balanced")
    for _ in range(4):
        asg.assign(study)
    rep = asg.balance_report(study)
    assert rep["total"] == 4
    assert rep["by_arm"] == {"A": 2, "B": 2}
