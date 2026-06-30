"""Evento — unidade do event log (events.jsonl).

Toda decisão relevante (do humano, da IA ou do sistema) gera um evento.
Append-only: nunca alterar eventos antigos.
"""
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class Event(BaseModel):
    event_id: str
    session_id: str
    timestamp: str        # ISO-8601 UTC
    elapsed_ms: int       # ms desde o início da sessão
    type: str             # ex: "round.proposal_submitted", "vote.resolved"
    actor: str = "system"
    phase: Optional[str] = None
    round: Optional[int] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
