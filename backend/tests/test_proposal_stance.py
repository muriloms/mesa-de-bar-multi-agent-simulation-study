"""Tests da extração de stance/refers_to em generate_proposal e do juiz (v2).

generate_proposal não tem mais aposta. Adiciona teste do judge_choose.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))


class _FakePersona:
    name = "Tesla"
    role = "Inventor"
    goal = "Inovar"
    description = "Inventor visionário"
    instructions = "Pense grande"


class _FakeAi:
    id = 2
    persona = _FakePersona()


class _FakeResponse:
    def __init__(self, text):
        self.text = text
        self.tokens_in = 100
        self.tokens_out = 50


class _MockManager:
    def __init__(self, response_text):
        self._text = response_text
        self.provider = "mock"
        self.model = "mock"

    def complete(self, prompt, params):
        return _FakeResponse(self._text), 100


def _patch_paths(tmp_path, monkeypatch, sid):
    from core import config
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "SESSIONS_DIR", tmp_path / "sessions")
    (tmp_path / "sessions" / sid).mkdir(parents=True)


def test_parser_extrai_stance_e_refers_to(tmp_path, monkeypatch):
    _patch_paths(tmp_path, monkeypatch, "s1")
    from llm import tasks
    from domain.llm_call import LLMParams

    mock = _MockManager(
        '{"stance": "counter", "refers_to": "Sócrates", '
        '"idea": "Discordo que conhecer-se basta sem agir."}'
    )
    result = tasks.generate_proposal(
        session_id="s1", manager=mock, ai_player=_FakeAi(), topic="Cidade ideal",
        conversation_history=[], params=LLMParams(temperature=0.7, max_tokens=400, seed=42),
        round_num=1, memo="", phase="discussion", language="pt",
    )
    assert result["stance"] == "counter"
    assert result["refers_to"] == "Sócrates"
    assert "Discordo" in result["idea"]
    assert "bid" not in result  # aposta removida na v2


def test_parser_stance_invalido_vira_null(tmp_path, monkeypatch):
    _patch_paths(tmp_path, monkeypatch, "s2")
    from llm import tasks
    from domain.llm_call import LLMParams

    mock = _MockManager('{"stance": "agree", "idea": "X"}')
    result = tasks.generate_proposal(
        session_id="s2", manager=mock, ai_player=_FakeAi(), topic="X",
        conversation_history=[], params=LLMParams(temperature=0.7, max_tokens=400, seed=42),
        round_num=1, memo="", phase="discussion",
    )
    assert result["stance"] is None


def test_parser_clamp_idea_muito_longa(tmp_path, monkeypatch):
    _patch_paths(tmp_path, monkeypatch, "s3")
    from llm import tasks
    from domain.llm_call import LLMParams

    longa = "palavra " * 80
    mock = _MockManager(f'{{"stance": "complement", "idea": "{longa.strip()}"}}')
    result = tasks.generate_proposal(
        session_id="s3", manager=mock, ai_player=_FakeAi(), topic="X",
        conversation_history=[], params=LLMParams(temperature=0.7, max_tokens=400, seed=42),
        round_num=1, memo="", phase="discussion",
    )
    assert len(result["idea"]) <= 325
    assert result["idea"].endswith("...")


def test_parser_idea_vazia_devolve_fallback(tmp_path, monkeypatch):
    _patch_paths(tmp_path, monkeypatch, "s4")
    from llm import tasks
    from domain.llm_call import LLMParams

    mock = _MockManager('lixo sem JSON nenhum')
    result = tasks.generate_proposal(
        session_id="s4", manager=mock, ai_player=_FakeAi(), topic="X",
        conversation_history=[], params=LLMParams(temperature=0.7, max_tokens=400, seed=42),
        round_num=1, memo="", phase="discussion",
    )
    assert "idea" in result
    assert result["stance"] is None
    assert result["refers_to"] is None


def test_judge_choose_picks_valid_index(tmp_path, monkeypatch):
    _patch_paths(tmp_path, monkeypatch, "s5")
    from llm import tasks
    from domain.llm_call import LLMParams
    from domain.round import IdeaProposal

    proposals = [
        IdeaProposal(player_id=1, player_name="Você", idea_text="Ideia humana"),
        IdeaProposal(player_id=2, player_name="Tesla", idea_text="Ideia Tesla"),
        IdeaProposal(player_id=3, player_name="Sócrates", idea_text="Ideia Sócrates"),
    ]
    # Juiz responde "2" → segunda ideia → player_id 2
    mock = _MockManager("2")
    res = tasks.judge_choose(
        session_id="s5", manager=mock, proposals=proposals, topic="X",
        params=LLMParams(temperature=0.7, max_tokens=10, seed=42), round_num=1,
        criterion="originalidade",
    )
    assert res["index"] == 2
    assert res["player_id"] == 2


def test_judge_choose_invalid_falls_back(tmp_path, monkeypatch):
    _patch_paths(tmp_path, monkeypatch, "s6")
    from llm import tasks
    from domain.llm_call import LLMParams
    from domain.round import IdeaProposal

    proposals = [
        IdeaProposal(player_id=1, player_name="Você", idea_text="A"),
        IdeaProposal(player_id=2, player_name="Tesla", idea_text="B"),
    ]
    mock = _MockManager("sem numero valido aqui")  # sem dígito → fallback idx 1
    res = tasks.judge_choose(
        session_id="s6", manager=mock, proposals=proposals, topic="X",
        params=LLMParams(temperature=0.7, max_tokens=10, seed=42), round_num=1,
    )
    assert res["index"] == 1
    assert res["player_id"] == 1


def test_proposal_cot_captures_reasoning(tmp_path, monkeypatch):
    _patch_paths(tmp_path, monkeypatch, "s7")
    from llm import tasks
    from domain.llm_call import LLMParams

    mock = _MockManager(
        '{"stance":"redirect","refers_to":null,'
        '"reasoning":"A mesa repetiu mobilidade; vou puxar pro lado social.",'
        '"idea":"E se o transporte virasse ponto de encontro, não só deslocamento?"}'
    )
    result = tasks.generate_proposal(
        session_id="s7", manager=mock, ai_player=_FakeAi(), topic="X",
        conversation_history=[], params=LLMParams(temperature=0.7, max_tokens=400, seed=42),
        round_num=1, memo="", phase="discussion", reasoning_mode="cot",
    )
    assert result["reasoning"] is not None
    assert "social" in result["reasoning"]
    # a fala não deve conter o raciocínio
    assert "vou puxar" not in result["idea"]


def test_proposal_direct_has_no_reasoning(tmp_path, monkeypatch):
    _patch_paths(tmp_path, monkeypatch, "s8")
    from llm import tasks
    from domain.llm_call import LLMParams

    mock = _MockManager('{"stance":"complement","refers_to":null,"idea":"Ideia direta."}')
    result = tasks.generate_proposal(
        session_id="s8", manager=mock, ai_player=_FakeAi(), topic="X",
        conversation_history=[], params=LLMParams(temperature=0.7, max_tokens=400, seed=42),
        round_num=1, memo="", phase="discussion", reasoning_mode="direct",
    )
    assert result["reasoning"] is None
