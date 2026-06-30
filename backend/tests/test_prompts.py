"""Smoke test do registry e renderer de prompts (v2)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))


def test_registry_finds_known_prompts():
    from prompts import registry
    registry.clear_cache()
    known = registry.all_known()
    expected = [
        ("proposal", "v1"),
        ("judge_choose", "v1"),
        ("persona_generation", "v1"),
        ("owner_summary_neutral", "v1"),
        ("lab_structure", "v1"),
    ]
    for k in expected:
        assert k in known, f"Prompt {k} não encontrado em {known}"


def test_render_proposal_v1():
    from prompts import renderer

    class _FakePersona:
        name = "Tesla"
        role = "Inventor"
        goal = "Inovar"
        description = "Inventor visionário"
        instructions = "Pense grande"

    rendered, info = renderer.render(
        "proposal", "v1",
        topic="cidade do futuro",
        persona=_FakePersona(), history=[], memo="", phase="discussion",
    )
    assert "cidade do futuro" in rendered
    assert "Tesla" in rendered
    assert "aposta" not in rendered.lower()  # v2: sem aposta
    assert "bid" not in rendered.lower()
    assert info.prompt_id == "proposal"
    assert info.version == "v1"
    assert len(info.sha256) == 64


def test_render_judge_choose_anonymous():
    """O juiz vê ideias numeradas e anônimas, com critério."""
    from prompts import renderer
    from domain.round import IdeaProposal

    proposals = [
        IdeaProposal(player_id=1, player_name="Você", idea_text="Ideia A"),
        IdeaProposal(player_id=2, player_name="Tesla", idea_text="Ideia B"),
    ]
    rendered, info = renderer.render(
        "judge_choose", "v1", topic="X", proposals=proposals,
        criterion="originalidade",
    )
    assert "Ideia A" in rendered and "Ideia B" in rendered
    assert "originalidade" in rendered
    # Anônimo: não cita os nomes dos autores
    assert "Tesla" not in rendered
    assert info.prompt_id == "judge_choose"


def test_prompt_not_found_raises():
    from prompts import registry
    from core.exceptions import PromptNotFoundError
    import pytest
    with pytest.raises(PromptNotFoundError):
        registry.get("prompt_que_nao_existe", "v999")
