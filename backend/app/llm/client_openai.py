"""Cliente OpenAI."""
import os
from typing import Optional

from openai import OpenAI
from dotenv import load_dotenv

from domain.llm_call import LLMParams
from .client_base import LLMResponse

load_dotenv()


class OpenAIClient:
    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.getenv("OPENAI_API_KEY")
        # OpenAI() não exige chave aqui; falha vem na chamada se ausente.
        self.client = OpenAI(api_key=key) if key else OpenAI()

    def complete(self, prompt: str, model: str, params: LLMParams) -> LLMResponse:
        kwargs = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": params.temperature,
        }
        if params.max_tokens:
            kwargs["max_tokens"] = params.max_tokens
        if params.seed is not None:
            kwargs["seed"] = params.seed

        response = self.client.chat.completions.create(**kwargs)
        text = response.choices[0].message.content or ""
        tokens_in = response.usage.prompt_tokens if response.usage else 0
        tokens_out = response.usage.completion_tokens if response.usage else 0
        return LLMResponse(text=text, tokens_in=tokens_in, tokens_out=tokens_out)
