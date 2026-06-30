"""Agente-jogador: substitui o humano nos 3 pontos de decisão do loop.

Usa a persona-jogador (perfil + temperatura) para gerar a proposta, escolher a
melhor ideia e decidir o avanço. Tem fallback determinístico (nunca trava o
loop se o LLM falhar).
"""
import random as _rnd
from typing import List, Optional

from llm.client_base import LLMParams


def _text(resp) -> str:
    for attr in ("text", "content", "output_text"):
        v = getattr(resp, attr, None)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return str(resp).strip()


def propose(manager, persona, topic: str, history: Optional[str] = None,
            seed: Optional[int] = None) -> str:
    """Gera a proposta do jogador para a rodada."""
    prompt = (
        f"Você é um participante humano numa mesa de debate criativo.\n"
        f"Seu perfil: {persona.profile or persona.description or persona.name}\n"
        f"Tema da mesa: {topic}\n"
        + (f"Resumo até agora: {history}\n" if history else "")
        + "Proponha UMA ideia, em 1-2 frases, em primeira pessoa. Só a ideia, sem rótulos."
    )
    params = LLMParams(temperature=persona.llm.temperature, max_tokens=160, seed=seed)
    try:
        resp, _ = manager.complete(prompt, params)
        idea = _text(resp)
        return idea or f"Uma ideia simples sobre: {topic}"
    except Exception:
        return f"Uma ideia simples sobre: {topic}"


def pick(manager, persona, topic: str, options) -> str:
    """Escolhe a melhor ideia entre as opções (anônimas). Retorna o ref."""
    refs = [o.ref for o in options]
    if not refs:
        return ""
    listing = "\n".join(f"{o.ref}: {o.idea_text}" for o in options)
    prompt = (
        f"Você é um participante com este perfil: {persona.profile or persona.name}\n"
        f"Tema: {topic}\nEscolha a MELHOR ideia abaixo.\n{listing}\n"
        f"Responda APENAS com o identificador (ex.: {refs[0]})."
    )
    params = LLMParams(temperature=0.2, max_tokens=10)
    try:
        resp, _ = manager.complete(prompt, params)
        ans = _text(resp).lower()
        for r in refs:
            if r.lower() in ans:
                return r
    except Exception:
        pass
    return _rnd.choice(refs)  # fallback


def decide_advance(persona, rng: _rnd.Random) -> bool:
    """Decide se concorda com o juiz (heurística pela deferência declarada)."""
    defer = (persona.traits or {}).get("deferencia_ia", "media")
    p_agree = {"alta": 0.8, "media": 0.5, "baixa": 0.2}.get(defer, 0.5)
    return rng.random() < p_agree
