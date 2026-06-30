"""LLMCall — representa uma chamada feita ao LLM.

Toda chamada vira uma linha em llm_calls.jsonl, com prompt versionado,
parâmetros, resposta crua, latência. É a caixa-preta da IA, fundamental
para reprodutibilidade.
"""
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class LLMCallContext(BaseModel):
    phase: Optional[str] = None
    round: Optional[int] = None
    actor_role: Optional[str] = None  # "persona" | "waiter" | "owner" | "lab" | "persona_generator"
    actor_id: Optional[str] = None    # ex: "ai_3", "user", "waiter"


class LLMParams(BaseModel):
    temperature: float = 0.7
    max_tokens: int = 300
    seed: Optional[int] = None


class LLMCall(BaseModel):
    call_id: str
    session_id: str
    timestamp: str
    context: LLMCallContext = Field(default_factory=LLMCallContext)
    provider: str
    model: str
    prompt_id: str
    prompt_version: str
    prompt_hash: str
    rendered_prompt: str
    params: LLMParams
    response_raw: Optional[str] = None
    response_parsed: Optional[Any] = None
    parse_status: str = "ok"  # ok | fenced | extracted | extracted_invalid | failed
    tokens: Dict[str, int] = Field(default_factory=dict)
    latency_ms: Optional[int] = None
    error: Optional[str] = None
