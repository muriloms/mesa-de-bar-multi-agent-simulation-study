"""Smoke test do parser JSON tolerante."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))


def test_parse_clean_json():
    from llm.parsers import parse_json_lenient
    data, status = parse_json_lenient('{"idea": "foo", "bid": 5}')
    assert status == "ok"
    assert data == {"idea": "foo", "bid": 5}


def test_parse_fenced_json():
    from llm.parsers import parse_json_lenient
    raw = '```json\n{"idea": "foo", "bid": 5}\n```'
    data, status = parse_json_lenient(raw)
    assert status == "fenced"
    assert data["idea"] == "foo"


def test_parse_fenced_no_lang():
    from llm.parsers import parse_json_lenient
    raw = '```\n{"x": 1}\n```'
    data, status = parse_json_lenient(raw)
    assert status == "fenced"
    assert data == {"x": 1}


def test_parse_extracted_from_chatter():
    from llm.parsers import parse_json_lenient
    raw = 'Claro, aqui está: {"idea": "lol", "bid": 10}. Espero ter ajudado!'
    data, status = parse_json_lenient(raw)
    assert status == "extracted"
    assert data["bid"] == 10


def test_parse_failed():
    from llm.parsers import parse_json_lenient
    data, status = parse_json_lenient("isso aqui não tem JSON algum")
    assert status == "failed"
    assert data is None


def test_parse_empty():
    from llm.parsers import parse_json_lenient
    data, status = parse_json_lenient("")
    assert status == "failed"
    assert data is None
