"""LLM call log: append-only JSONL.

Cada chamada ao LLM (proposta, voto delegado, síntese, lab) gera uma
linha aqui — com prompt versionado, parâmetros, resposta crua.
"""
from typing import Iterator
from domain.llm_call import LLMCall
from . import paths


def append(session_id: str, call: LLMCall) -> None:
    p = paths.llm_log_path(session_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(call.model_dump_json() + "\n")


def read_all(session_id: str) -> Iterator[LLMCall]:
    p = paths.llm_log_path(session_id)
    if not p.exists():
        return
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield LLMCall.model_validate_json(line)
            except Exception:
                continue
