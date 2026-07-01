"""Agente-jogador: substitui o humano nos 3 pontos de decisão do loop.

Propõe, escolhe e decide o avanço usando a persona-jogador. As chamadas de LLM
(propor/escolher) são registradas em llm_calls.jsonl com actor_role="player".

INTEGRIDADE: NÃO há mais fallback silencioso. Se a chamada falhar (após retries)
ou vier vazia/não-parseável, levantamos PlayerCallError — o runner exclui a
sessão em vez de gravar ideia-fake/escolha-aleatória (que contaminam os dados).
"""
import hashlib
import random as _rnd
import time as _time
from typing import List, Optional

from llm.client_base import LLMParams
from core import ids, time as core_time
from domain.llm_call import LLMCall, LLMCallContext
from persistence import llm_log


class PlayerCallError(Exception):
    """Falha irrecuperável numa chamada do jogador-agente (após retries)."""


def _complete_with_retry(manager, prompt, params, attempts: int = 3,
                         base_delay: float = 0.6):
    """Chama o LLM com retry + backoff exponencial (+ jitter). Retorna
    (resp, latency_ms, tentativas_usadas). Levanta a última exceção se esgotar."""
    last = None
    for i in range(max(1, attempts)):
        try:
            resp, latency = manager.complete(prompt, params)
            return resp, latency, i + 1
        except Exception as e:            # timeout, rate limit, conexão, etc.
            last = e
            if i < attempts - 1:
                _time.sleep(base_delay * (2 ** i) + _rnd.random() * 0.3)
    raise PlayerCallError(f"{type(last).__name__}: {last}")


def _log_player_call(*, session_id, prompt_id, prompt, params, resp, latency_ms,
                     provider, model, persona_id, round_num, phase,
                     parse_status: str, parsed=None, error=None) -> None:
    """Grava a chamada do jogador. tokens reais quando há resposta (mesmo que o
    parse falhe) — distingue 'API respondeu mas não parseou' de 'chamada falhou'."""
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
            parse_status=parse_status,
            tokens=({"in": resp.tokens_in, "out": resp.tokens_out} if resp else {}),
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
            round_num: Optional[int] = None, attempts: int = 3) -> str:
    """Proposta do jogador. Levanta PlayerCallError se falhar/vier vazia."""
    prompt = (
        f"Você é um participante humano numa mesa de debate criativo.\n"
        f"Seu perfil: {persona.profile or persona.description or persona.name}\n"
        f"Tema da mesa: {topic}\n"
        + (f"Resumo até agora: {history}\n" if history else "")
        + "Proponha UMA ideia, em 1-2 frases, em primeira pessoa. Só a ideia, sem rótulos."
    )
    params = LLMParams(temperature=persona.llm.temperature, max_tokens=160, seed=seed)
    common = dict(session_id=session_id, prompt_id="sim_player_propose", prompt=prompt,
                  params=params, provider=manager.provider, model=manager.model,
                  persona_id=persona.id, round_num=round_num, phase="proposing")
    try:
        resp, latency, _ = _complete_with_retry(manager, prompt, params, attempts)
    except PlayerCallError as e:
        _log_player_call(resp=None, latency_ms=None, parse_status="failed",
                         error=str(e), **common)
        raise
    idea = _text(resp)
    if not idea:
        _log_player_call(resp=resp, latency_ms=latency, parse_status="empty",
                         error="resposta vazia", **common)
        raise PlayerCallError("proposta vazia")
    _log_player_call(resp=resp, latency_ms=latency, parse_status="ok",
                     parsed=idea, **common)
    return idea


def pick(manager, persona, topic: str, options, session_id: Optional[str] = None,
         round_num: Optional[int] = None, attempts: int = 3) -> str:
    """Escolha do jogador. Levanta PlayerCallError se falhar/não-parseável
    (sem escolha aleatória de fallback)."""
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
    common = dict(session_id=session_id, prompt_id="sim_player_pick", prompt=prompt,
                  params=params, provider=manager.provider, model=manager.model,
                  persona_id=persona.id, round_num=round_num, phase="choosing")
    try:
        resp, latency, _ = _complete_with_retry(manager, prompt, params, attempts)
    except PlayerCallError as e:
        _log_player_call(resp=None, latency_ms=None, parse_status="failed",
                         error=str(e), **common)
        raise
    ans = _text(resp).lower()
    chosen = next((r for r in refs if r.lower() in ans), None)
    _log_player_call(resp=resp, latency_ms=latency,
                     parse_status="ok" if chosen else "unparsed",
                     parsed=chosen, error=None if chosen else f"sem ref em {ans!r}",
                     **common)
    if not chosen:
        raise PlayerCallError(f"escolha não-parseável: {ans!r}")
    return chosen


def decide_advance(persona, rng: _rnd.Random) -> bool:
    """Decide se concorda com o juiz (heurística pela deferência declarada)."""
    defer = (persona.traits or {}).get("deferencia_ia", "media")
    p_agree = {"alta": 0.8, "media": 0.5, "baixa": 0.2}.get(defer, 0.5)
    return rng.random() < p_agree
