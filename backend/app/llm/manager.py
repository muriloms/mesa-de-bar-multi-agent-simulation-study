"""LLMManager: roteador entre provedores, com interface explícita.

Substitui o __getattr__ mágico anterior por chamadas tipadas.
"""
import time
from typing import Optional, Tuple

from core.exceptions import LLMError
from domain.llm_call import LLMParams
from .client_base import LLMResponse
from .client_gemini import GeminiClient
from .client_openai import OpenAIClient


PROVIDERS = {
    "google": GeminiClient,
    "openai": OpenAIClient,
}


class LLMManager:
    def __init__(self, provider: str, model: str, api_key: Optional[str] = None):
        if provider not in PROVIDERS:
            raise LLMError(f"Provedor desconhecido: {provider}. Conhecidos: {list(PROVIDERS)}")
        self.provider = provider
        self.model = model
        self.client = PROVIDERS[provider](api_key)

    def complete(self, prompt: str, params: LLMParams) -> Tuple[LLMResponse, int]:
        """Devolve (response, latency_ms)."""
        start = time.monotonic()
        response = self.client.complete(prompt, self.model, params)
        latency_ms = int((time.monotonic() - start) * 1000)
        return response, latency_ms
