"""Agente-jogador: substitui o humano nos 3 pontos de decisão do loop.

Usa a persona-jogador (perfil + temperatura) para gerar a proposta, escolher a
melhor ideia e decidir o avanço. Tem fallback determinístico (nunca trava o
loop se o LLM falhar).

As chamadas de LLM do jogador (propor/escolher) são registradas em
llm_calls.jsonl com actor_role="player" — assim tokens, custo e latência do
jogador-agente entram na análise igual às de personas, juiz e dono.
"""
import hashlib
import random as _rnd
from typing import List, Optional

from llm.client_base import LLMParams
from core import ids, time as core_time
from domain.llm_call import LLMCall, LLMCallContext
from persistence import llm_log


def _log_player_call(*, session_id, prompt_id, prompt, params, resp, latency_ms,
                     provider, model, persona_id, round_num, phase,
                     parsed=None, error=None) -> None:
    """Grava a chamada do jogador em llm_calls.jsonl (mesmo formato dos demais)."""
    if not session_id:
        return
    try:
        call = LLMCall(
            call_id=ids.call_id(),
            session_id=session_id,
            timestamp=core_time.iso_now(),
            context=LLMCallContext(phase=phase, round=round_num,
                                   actor_role="player", actor_id=persona_id),
            provider=provider, model=model,
            prompt_id=prompt_id, prompt_version="inline",
            prompt_hash=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            rendered_prompt=prompt, params=params,
            response_raw=resp.text if resp else None,
            response_parsed=parsed,
            parse_status="ok" if resp else "failed",
            tokens={"in": resp.tokens_in, "out": resp.tokens_out} if resp else {},
            latency_ms=latency_ms, error=error,
        )
        llm_log.append(session_id, call)
    except Exception:
        pass


def _text(resp) -> str:
    for attr in ("text", "content", "output_text"):
        v = getattr(resp, attr, None)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return str(resp).strip()


def propose(manager, persona, topic: str, history: Optional[str] = None,
            seed: Optional[int] = None, session_id: Optional[str] = None,
            round_num: Optional[int] = None) -> str:
    """Gera a proposta do jogador para a rodada (e registra a chamada)."""
    prompt = (
        f"Você é um participante humano numa mesa de debate criativo.\n"
        f"Seu perfil: {persona.profile or persona.description or persona.name}\n"
        f"Tema da mesa: {topic}\n"
        + (f"Resumo até agora: {history}\n" if history else "")
        + "Proponha UMA ideia, em 1-2 frases, em primeira pessoa. Só a ideia, sem rótulos."
    )
    params = LLMParams(temperature=persona.llm.temperature, max_tokens=160, seed=seed)
    try:
        resp, latency = manager.complete(prompt, params)
        idea = _text(resp) or f"Uma ideia simples sobre: {topic}"
        _log_player_call(session_id=session_id, prompt_id="sim_player_propose",
                         prompt=prompt, params=params, resp=resp, latency_ms=latency,
                         provider=manager.provider, model=manager.model,
                         persona_id=persona.id, round_num=round_num, phase="proposing",
                         parsed=idea)
        return idea
    except Exception as e:
        _log_player_call(session_id=session_id, prompt_id="sim_player_propose",
                         prompt=prompt, params=params, resp=None, latency_ms=None,
                         provider=manager.provider, model=manager.model,
                         persona_id=persona.id, round_num=round_num, phase="proposing",
                         error=str(e))
        return f"Uma ideia simples sobre: {topic}"


def pick(manager, persona, topic: str, options, session_id: Optional[str] = None,
         round_num: Optional[int] = None) -> str:
    """Escolhe a melhor ideia entre as opções (anônimas). Retorna o ref (e registra)."""
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
        resp, latency = manager.complete(prompt, params)
        ans = _text(resp).lower()
        chosen = next((r for r in refs if r.lower() in ans), None)
        _log_player_call(session_id=session_id, prompt_id="sim_player_pick",
                         prompt=prompt, params=params, resp=resp, latency_ms=latency,
                         provider=manager.provider, model=manager.model,
                         persona_id=persona.id, round_num=round_num, phase="choosing",
                         parsed=chosen)
        if chosen:
            return chosen
    except Exception as e:
        _log_player_call(session_id=session_id, prompt_id="sim_player_pick",
                         prompt=prompt, params=params, resp=None, latency_ms=None,
                         provider=manager.provider, model=manager.model,
                         persona_id=persona.id, round_num=round_num, phase="choosing",
                         error=str(e))
    return _rnd.choice(refs)  # fallback


def decide_advance(persona, rng: _rnd.Random) -> bool:
    """Decide se concorda com o juiz (heurística pela deferência declarada)."""
    defer = (persona.traits or {}).get("deferencia_ia", "media")
    p_agree = {"alta": 0.8, "media": 0.5, "baixa": 0.2}.get(defer, 0.5)
    return rng.random() < p_agree
