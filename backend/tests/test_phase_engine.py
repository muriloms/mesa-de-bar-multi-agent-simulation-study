"""Smoke test do PhaseEngine (v2: contador linear de N rodadas)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))


def test_engine_initial_state():
    from game.phase_engine import PhaseEngine
    e = PhaseEngine(4)
    assert e.current_phase_name == "discussion"
    assert e.global_round == 1
    assert e.total_rounds == 4
    assert not e.finished


def test_engine_full_run():
    """Roda 4 rodadas e termina em closing."""
    from game.phase_engine import PhaseEngine
    e = PhaseEngine(4)

    # rodadas 1→2, 2→3, 3→4 (sem mudança de fase)
    for _ in range(3):
        f, t = e.advance_round()
        assert f is None and t is None
        assert e.current_phase_name == "discussion"
        assert not e.finished

    # 4ª rodada concluída → closing
    f, t = e.advance_round()
    assert f == "discussion"
    assert t == "closing"
    assert e.finished
    assert e.is_closing
    assert e.current_phase_name == "closing"


def test_engine_single_round():
    from game.phase_engine import PhaseEngine
    e = PhaseEngine(1)
    f, t = e.advance_round()
    assert f == "discussion" and t == "closing"
    assert e.finished


def test_engine_round_floor():
    """rounds < 1 é normalizado pra 1."""
    from game.phase_engine import PhaseEngine
    e = PhaseEngine(0)
    assert e.total_rounds == 1
