"""Parser JSON tolerante a respostas "sujas" de LLM.

Tenta, em ordem:
  1. Parse direto.
  2. Remover fences ```json ... ``` ou ``` ... ```.
  3. Extrair primeiro objeto/array no texto.

Devolve (data, status). Se nada funcionar, (None, "failed").
"""
import json
import re
from typing import Any, Optional, Tuple


def parse_json_lenient(raw: str) -> Tuple[Optional[Any], str]:
    s = (raw or "").strip()
    if not s:
        return None, "failed"

    # 1) Tentativa direta
    try:
        return json.loads(s), "ok"
    except json.JSONDecodeError:
        pass

    # 2) Remover fences ```json ... ``` ou ``` ... ```
    fence = re.search(r"```(?:json)?\s*(.+?)\s*```", s, re.DOTALL | re.IGNORECASE)
    if fence:
        try:
            return json.loads(fence.group(1)), "fenced"
        except json.JSONDecodeError:
            pass

    # 3) Extrair primeiro objeto/array do texto
    m = re.search(r"(\{.*\}|\[.*\])", s, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1)), "extracted"
        except json.JSONDecodeError:
            pass

    return None, "failed"
