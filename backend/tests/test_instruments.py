"""Tests do loader e do service de instrumentos."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))


def test_load_pre_session_instrument():
    from instruments.loader import load_instrument
    inst = load_instrument("pre_session_cocreation_v1")
    assert inst.id == "pre_session_cocreation_v1"
    assert inst.moment == "pre_session"
    assert len(inst.sections) >= 1
    # Deve ter pelo menos um item likert
    types_seen = set()
    for s in inst.sections:
        for it in s.items:
            types_seen.add(it.type)
    assert "likert" in types_seen
    assert "single_select" in types_seen
    assert "slider" in types_seen


def test_load_post_session_instrument():
    from instruments.loader import load_instrument
    inst = load_instrument("post_session_cocreation_v1")
    assert inst.id == "post_session_cocreation_v1"
    assert inst.moment == "post_session"
    # Deve ter ranking
    types_seen = set()
    for s in inst.sections:
        for it in s.items:
            types_seen.add(it.type)
    assert "ranking" in types_seen


def test_instrument_not_found():
    from instruments.loader import load_instrument, InstrumentNotFoundError
    import pytest
    with pytest.raises(InstrumentNotFoundError):
        load_instrument("nao_existe_jamais_v99")


def test_list_instruments_includes_examples():
    from instruments.loader import list_instruments
    names = list_instruments()
    assert "pre_session_cocreation_v1" in names
    assert "post_session_cocreation_v1" in names


def test_submit_instrument_response(tmp_path, monkeypatch):
    from core import config
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "SESSIONS_DIR", tmp_path / "sessions")

    # Cria pasta de sessão fake
    sid = "test_session_001"
    session_dir = tmp_path / "sessions" / sid
    session_dir.mkdir(parents=True)

    from services.instrument_service import submit_instrument_response

    result = submit_instrument_response(
        session_id=sid,
        instrument_id="pre_session_cocreation_v1",
        started_at="2025-01-01T00:00:00.000Z",
        submitted_at="2025-01-01T00:05:00.000Z",
        duration_ms=300000,
        responses=[
            {"item_id": "age_range", "value": "25-34"},
            {"item_id": "ai_familiarity", "value": 4},
            {"item_id": "expectation_creativity", "value": 75},
            # item id inválido — deve ser ignorado, não crashar
            {"item_id": "nao_existe", "value": "foo"},
        ],
        response_order=["age_range", "ai_familiarity", "expectation_creativity"],
    )

    assert result["ok"] is True
    assert result["responses_count"] == 3  # o "nao_existe" foi descartado

    # Verifica que arquivo foi gravado
    output = session_dir / "instruments" / "pre_session_cocreation_v1.json"
    assert output.exists()
    data = json.loads(output.read_text())
    assert data["instrument_id"] == "pre_session_cocreation_v1"
    assert len(data["responses"]) == 3
