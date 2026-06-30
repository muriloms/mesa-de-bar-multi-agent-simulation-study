"""Event log: append-only JSONL.

A invariante é: linhas só são adicionadas, nunca alteradas. A leitura é
posterior (análise) e tolerante a linhas malformadas (loga e segue).
"""
from typing import Iterator
from domain.event import Event
from . import paths


def append(session_id: str, event: Event) -> None:
    p = paths.events_log_path(session_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(event.model_dump_json() + "\n")


def read_all(session_id: str) -> Iterator[Event]:
    p = paths.events_log_path(session_id)
    if not p.exists():
        return
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield Event.model_validate_json(line)
            except Exception:
                # tolerância: linha malformada não deve quebrar a leitura
                continue
