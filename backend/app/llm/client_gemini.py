"""Cliente Google Gemini."""
import os
from typing import Optional

import google.generativeai as genai
from dotenv import load_dotenv

from domain.llm_call import LLMParams
from .client_base import LLMResponse

load_dotenv()


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.getenv("GOOGLE_API_KEY")
        if key:
            genai.configure(api_key=key)
        # Se não houver chave, configure não falha agora; falha será visível
        # no momento da primeira chamada (e fica no llm_calls.jsonl como erro).

    def complete(self, prompt: str, model: str, params: LLMParams) -> LLMResponse:
        gen_config = {"temperature": params.temperature}
        if params.max_tokens:
            gen_config["max_output_tokens"] = params.max_tokens
        # Nota: a API generativa do Gemini ainda não aceita seed; logamos
        # mesmo assim para rastreabilidade.

        model_obj = genai.GenerativeModel(model_name=model)
        response = model_obj.generate_content(prompt, generation_config=gen_config)

        text = response.text or ""
        tokens_in = 0
        tokens_out = 0
        meta = getattr(response, "usage_metadata", None)
        if meta:
            tokens_in = getattr(meta, "prompt_token_count", 0) or 0
            tokens_out = getattr(meta, "candidates_token_count", 0) or 0

        return LLMResponse(text=text, tokens_in=tokens_in, tokens_out=tokens_out)
