"""Smoke test do event log."""
import sys
import tempfile
from pathlib import Path

# Adiciona backend/app ao path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))


def test_event_log_append_and_read(tmp_path, monkeypatch):
    # Redireciona DATA_DIR pra tmp
    from core import config
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "SESSIONS_DIR", tmp_path / "sessions")

    from domain.event import Event
    from persistence import event_log

    sid = "test_session_001"
    e1 = Event(
        event_id="evt_001",
        session_id=sid,
        timestamp="2025-01-01T00:00:00.000Z",
        elapsed_ms=0,
        type="session.created",
        actor="system",
        payload={"foo": "bar"},
    )
    e2 = Event(
        event_id="evt_002",
        session_id=sid,
        timestamp="2025-01-01T00:00:01.000Z",
        elapsed_ms=1000,
        type="round.started",
        round=1,
        payload={"round": 1},
    )

    event_log.append(sid, e1)
    event_log.append(sid, e2)

    events = list(event_log.read_all(sid))
    assert len(events) == 2
    assert events[0].event_id == "evt_001"
    assert events[1].type == "round.started"
    assert events[1].payload == {"round": 1}


def test_read_empty_session(tmp_path, monkeypatch):
    from core import config
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "SESSIONS_DIR", tmp_path / "sessions")

    from persistence import event_log

    events = list(event_log.read_all("session_que_nao_existe"))
    assert events == []
