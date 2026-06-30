"""Smoke test do protocol loader (v2)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))


def test_load_default_protocol():
    from protocols import loader
    p = loader.load_protocol("default")
    assert p.id == "default"
    assert p.version == "3.0.0"
    assert p.llm_default_provider == "google"
    assert isinstance(p.llm_temperature, float)
    assert p.language == "pt"
    # v2: N rodadas + manipulações centrais
    assert p.rounds == 4
    assert p.quem_avanca == "juiz_ia"
    assert p.source_blind_on_choice is True
    assert p.judge.criterion == "originalidade"
    assert p.owner.bias == "neutral"
    assert p.memory.mode == "reflected_summary"
    assert p.telemetry.capture_keystrokes is True


def test_experimental_arms_load():
    from protocols import loader
    jog = loader.load_protocol("jogador_avanca")
    assert jog.quem_avanca == "jogador"
    fonte = loader.load_protocol("fonte_revelada")
    assert fonte.source_blind_on_choice is False
    blind = loader.load_protocol("blind_personas")
    assert blind.display.blind_personas is True
    solo = loader.load_protocol("solo_baseline")
    assert solo.display.solo_baseline is True


def test_protocol_not_found():
    from protocols import loader
    from core.exceptions import ProtocolError
    import pytest
    with pytest.raises(ProtocolError):
        loader.load_protocol("nao_existe_jamais")


def test_list_protocols_includes_default():
    from protocols import loader
    names = loader.list_protocols()
    assert "default" in names
