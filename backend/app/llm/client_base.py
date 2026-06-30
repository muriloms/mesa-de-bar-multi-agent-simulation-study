"""Interface comum dos clientes LLM.

Cada provedor (Gemini, OpenAI, ...) implementa `complete(prompt, model, params)`
que devolve um LLMResponse com texto e contagem de tokens (quando disponível).
"""
from typing import Protocol

from domain.llm_call import LLMParams


class LLMResponse:
    def __init__(self, text: str, tokens_in: int = 0, tokens_out: int = 0):
        self.text = text
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out


class LLMClient(Protocol):
    def complete(self, prompt: str, model: str, params: LLMParams) -> LLMResponse:
        ...
