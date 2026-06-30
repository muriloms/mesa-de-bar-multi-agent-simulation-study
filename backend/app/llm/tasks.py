"""Tarefas de LLM: render prompt + chamada + parse + log."""
import re
from typing import Any, Dict, List, Optional

from core import ids, time as core_time
from domain.llm_call import LLMCall, LLMCallContext, LLMParams
from domain.round import IdeaProposal
from persistence import llm_log
from prompts import renderer

from .manager import LLMManager
from .parsers import parse_json_lenient


def _log(*, session_id, prompt_id, info, rendered, params, response, latency_ms,
         parse_status, response_parsed, context, provider, model, error=None):
    if not session_id:
        return
    call = LLMCall(
        call_id=ids.call_id(),
        session_id=session_id,
        timestamp=core_time.iso_now(),
        context=context,
        provider=provider,
        model=model,
        prompt_id=prompt_id,
        prompt_version=info.version,
        prompt_hash=info.sha256,
        rendered_prompt=rendered,
        params=params,
        response_raw=response.text if response else None,
        response_parsed=response_parsed,
        parse_status=parse_status,
        tokens={"in": response.tokens_in, "out": response.tokens_out} if response else {},
        latency_ms=latency_ms,
        error=error,
    )
    llm_log.append(session_id, call)


# ---------------------------------------------------------------------------
# Reflexão privada da persona — gera o "memo" interno antes da proposta
# ---------------------------------------------------------------------------
def reflect_persona(*, session_id, manager, ai_player, topic,
                    conversation_history, previous_memo: str,
                    params: LLMParams, round_num: int, phase: str, language: str = "pt") -> str:
    """Pede à persona pra escrever uma reflexão curta (1ª pessoa, ~150 chars).

    Devolve o texto cru. Caso de erro, devolve o memo anterior (não regride).
    """
    rendered, info = renderer.render(
        "persona_reflect", "v1", language=language,
        topic=topic,
        persona=ai_player.persona,
        history=conversation_history,  # histórico inteiro — sem truncar
        previous_memo=previous_memo,
    )
    context = LLMCallContext(
        phase=phase, round=round_num,
        actor_role="persona_reflect",
        actor_id=f"ai_{ai_player.id}",
    )

    response = None
    parsed: Optional[str] = None
    parse_status = "ok"
    error: Optional[str] = None
    latency_ms = 0
    text = previous_memo or ""

    try:
        response, latency_ms = manager.complete(rendered, params)
        raw = (response.text or "").strip()
        # Limita a ~200 chars como salvaguarda contra LLM verboso
        if len(raw) > 220:
            raw = raw[:217].rstrip() + "..."
        if raw:
            text = raw
            parsed = raw
        else:
            parse_status = "failed"
    except Exception as e:
        error = str(e)
        parse_status = "failed"

    _log(
        session_id=session_id, prompt_id="persona_reflect", info=info, rendered=rendered,
        params=params, response=response, latency_ms=latency_ms,
        parse_status=parse_status, response_parsed=parsed, context=context,
        provider=manager.provider, model=manager.model, error=error,
    )
    return text


# ---------------------------------------------------------------------------
# Proposta de IA — agora ciente de fase e bidding_enabled
# ---------------------------------------------------------------------------
def generate_proposal(*, session_id, manager, ai_player, topic,
                     conversation_history, params, round_num,
                     memo: str = "", phase: str = "discussion",
                     reasoning_mode: str = "direct", language: str = "pt") -> Dict[str, Any]:
    """Persona IA gera uma ideia (sem aposta na v2). reasoning_mode=cot pede
    um raciocínio privado antes da fala (capturado, não exibido)."""
    rendered, info = renderer.render(
        "proposal", "v1", language=language,
        topic=topic,
        persona=ai_player.persona, history=conversation_history,
        memo=memo, phase=phase, reasoning_mode=reasoning_mode,
    )
    context = LLMCallContext(
        phase=phase, round=round_num,
        actor_role="persona", actor_id=f"ai_{ai_player.id}",
    )

    response = None
    parsed: Any = None
    parse_status = "failed"
    error: Optional[str] = None
    latency_ms = 0

    try:
        response, latency_ms = manager.complete(rendered, params)
        parsed, parse_status = parse_json_lenient(response.text)
    except Exception as e:
        error = str(e)

    _log(session_id=session_id, prompt_id="proposal", info=info, rendered=rendered,
         params=params, response=response, latency_ms=latency_ms,
         parse_status=parse_status, response_parsed=parsed, context=context,
         provider=manager.provider, model=manager.model, error=error)

    if not parsed or not isinstance(parsed, dict) or "idea" not in parsed:
        return {
            "idea": "Fiquei pensativo e não consegui formular bem minha ideia.",
            "stance": None,
            "refers_to": None,
            "reasoning": None,
        }

    # Stance — valida que está nos valores aceitos, senão null
    raw_stance = parsed.get("stance")
    stance = raw_stance if raw_stance in ("complement", "counter", "redirect") else None

    # refers_to — pode vir como string (nome) ou null
    refers_to_raw = parsed.get("refers_to")
    refers_to_name = refers_to_raw if isinstance(refers_to_raw, str) and refers_to_raw.strip() else None

    # reasoning — só em modo cot; capturado pra log, nunca exibido na mesa
    reasoning_raw = parsed.get("reasoning")
    reasoning = reasoning_raw.strip() if isinstance(reasoning_raw, str) and reasoning_raw.strip() else None

    # Clamp de tamanho da idea — proteção de hard limit caso LLM ignore.
    idea_text = str(parsed["idea"]).strip()
    MAX_IDEA_CHARS = 320
    if len(idea_text) > MAX_IDEA_CHARS:
        cut = idea_text[:MAX_IDEA_CHARS].rsplit(" ", 1)[0]
        idea_text = cut.rstrip(".,;:!?") + "..."

    return {
        "idea": idea_text,
        "stance": stance,
        "refers_to": refers_to_name,
        "reasoning": reasoning,
    }


def judge_choose(*, session_id, manager, proposals: List[IdeaProposal], topic,
                 params: LLMParams, round_num: int,
                 criterion: str = "originalidade",
                 language: str = "pt") -> Dict[str, Any]:
    """Juiz IA escolhe a melhor ideia da rodada, ANÔNIMA, por um critério.

    As propostas são apresentadas numeradas (1..N) sem autoria. O modelo
    devolve um número; mapeamos de volta pro player_id.
    Retorna {"player_id": int, "index": int, "rationale": str|None}.
    """
    rendered, info = renderer.render(
        "judge_choose", "v1", language=language,
        topic=topic, proposals=proposals, criterion=criterion,
    )
    context = LLMCallContext(phase="discussion", round=round_num,
                             actor_role="judge", actor_id="judge")
    fallback_idx = 1
    fallback_id = proposals[0].player_id

    response = None
    chosen_idx: Optional[int] = None
    parse_status = "ok"
    error: Optional[str] = None
    latency_ms = 0

    try:
        response, latency_ms = manager.complete(rendered, params)
        m = re.search(r"\d+", response.text or "")
        if m:
            idx = int(m.group())
            if 1 <= idx <= len(proposals):
                chosen_idx = idx
                parse_status = "ok"
            else:
                chosen_idx = fallback_idx
                parse_status = "extracted_invalid"
        else:
            chosen_idx = fallback_idx
            parse_status = "failed"
    except Exception as e:
        error = str(e)
        chosen_idx = fallback_idx
        parse_status = "failed"

    chosen_idx = chosen_idx or fallback_idx
    player_id = proposals[chosen_idx - 1].player_id

    _log(session_id=session_id, prompt_id="judge_choose", info=info, rendered=rendered,
         params=params, response=response, latency_ms=latency_ms,
         parse_status=parse_status, response_parsed=player_id, context=context,
         provider=manager.provider, model=manager.model, error=error)

    return {"player_id": player_id, "index": chosen_idx,
            "rationale": (response.text.strip() if response and response.text else None)}


def choose_best_idea(*, session_id, manager, proposals: List[IdeaProposal], topic,
                    params: LLMParams, round_num: int,
                    prompt_id: str = "waiter_choose",
                    language: str = "pt") -> int:
    """Garçom escolhe vencedor.

    `prompt_id` permite trocar entre 'waiter_choose' (modo padrão) e
    'waiter_tiebreak' (modo desempate explicito).
    """
    rendered, info = renderer.render(prompt_id, "v1", language=language, topic=topic, proposals=proposals)
    context = LLMCallContext(phase="discussion", round=round_num,
                             actor_role="waiter", actor_id="waiter")
    fallback = proposals[0].player_id

    response = None
    parsed: Optional[int] = None
    parse_status = "ok"
    error: Optional[str] = None
    latency_ms = 0

    try:
        response, latency_ms = manager.complete(rendered, params)
        m = re.search(r"\d+", response.text or "")
        if m:
            winner_id = int(m.group())
            valid_ids = [p.player_id for p in proposals]
            if winner_id in valid_ids:
                parsed = winner_id
                parse_status = "ok"
            else:
                parsed = fallback
                parse_status = "extracted_invalid"
        else:
            parsed = fallback
            parse_status = "failed"
    except Exception as e:
        error = str(e)
        parsed = fallback
        parse_status = "failed"

    _log(session_id=session_id, prompt_id=prompt_id, info=info, rendered=rendered,
         params=params, response=response, latency_ms=latency_ms,
         parse_status=parse_status, response_parsed=parsed, context=context,
         provider=manager.provider, model=manager.model, error=error)

    return parsed if parsed is not None else fallback


def waiter_summarize(*, session_id, manager, topic, conversation_history,
                     params: LLMParams, round_num: int, phase: str, language: str = "pt") -> str:
    """Resumo parcial do Garçom — chamado pelo botão 'Resumo parcial'."""
    rendered, info = renderer.render(
        "waiter_summarize", "v1", language=language,
        topic=topic, history=conversation_history, round=round_num, phase=phase,
    )
    context = LLMCallContext(phase=phase, round=round_num,
                             actor_role="waiter", actor_id="waiter")
    response = None
    parsed: Optional[str] = None
    parse_status = "ok"
    error: Optional[str] = None
    latency_ms = 0
    text = "Não consegui ouvir bem agora — peçam de novo."

    try:
        response, latency_ms = manager.complete(rendered, params)
        text = (response.text or "").strip() or text
        parsed = text
    except Exception as e:
        error = str(e)
        parse_status = "failed"

    _log(session_id=session_id, prompt_id="waiter_summarize", info=info, rendered=rendered,
         params=params, response=response, latency_ms=latency_ms,
         parse_status=parse_status, response_parsed=parsed, context=context,
         provider=manager.provider, model=manager.model, error=error)
    return text


def waiter_provoke(*, session_id, manager, topic, conversation_history,
                   params: LLMParams, round_num: int, phase: str, language: str = "pt") -> str:
    """Provocação curta — uma pergunta afiada."""
    rendered, info = renderer.render(
        "waiter_provoke", "v1", language=language,
        topic=topic, history=conversation_history,
    )
    context = LLMCallContext(phase=phase, round=round_num,
                             actor_role="waiter", actor_id="waiter")
    response = None
    parsed: Optional[str] = None
    parse_status = "ok"
    error: Optional[str] = None
    latency_ms = 0
    text = "Vocês estão muito de acordo. Não tem nada incomodando ninguém aqui?"

    try:
        response, latency_ms = manager.complete(rendered, params)
        raw = (response.text or "").strip()
        if raw and len(raw) < 300:
            text = raw
        parsed = text
    except Exception as e:
        error = str(e)
        parse_status = "failed"

    _log(session_id=session_id, prompt_id="waiter_provoke", info=info, rendered=rendered,
         params=params, response=response, latency_ms=latency_ms,
         parse_status=parse_status, response_parsed=parsed, context=context,
         provider=manager.provider, model=manager.model, error=error)
    return text


def generate_personas(*, manager, theme, params, session_id=None) -> List[Dict[str, Any]]:
    rendered, info = renderer.render("persona_generation", "v1", theme=theme)
    context = LLMCallContext(actor_role="persona_generator")

    response = None
    parsed: Optional[List] = None
    parse_status = "failed"
    error: Optional[str] = None
    latency_ms = 0

    try:
        response, latency_ms = manager.complete(rendered, params)
        data, parse_status = parse_json_lenient(response.text)
        if isinstance(data, dict) and isinstance(data.get("team"), list):
            parsed = data["team"]
    except Exception as e:
        error = str(e)

    if session_id:
        _log(session_id=session_id, prompt_id="persona_generation", info=info,
             rendered=rendered, params=params, response=response, latency_ms=latency_ms,
             parse_status=parse_status, response_parsed=parsed, context=context,
             provider=manager.provider, model=manager.model, error=error)

    return parsed or []


def summarize_conversation(*, session_id, manager, topic, conversation_history,
                          params, owner_bias: str = "neutral", players=None,
                          language: str = "pt") -> str:
    """Síntese do Dono do Bar — escolhe prompt baseado no viés."""
    history_filtered = [m for m in conversation_history if getattr(m, "player_id", 1) != 0]

    prompt_id_map = {
        "neutral": "owner_summary_neutral",
        "pro_winner": "owner_summary_pro_winner",
        "pro_human": "owner_summary_pro_human",
        "pro_bidder": "owner_summary_pro_bidder",
    }
    prompt_id = prompt_id_map.get(owner_bias, "owner_summary_neutral")

    # Tenta o prompt do viés; se não existir ainda, cai pro neutral
    try:
        rendered, info = renderer.render(
            prompt_id, "v1", language=language,
            topic=topic, history=history_filtered, players=players or [],
        )
    except Exception:
        prompt_id = "owner_summary_neutral"
        rendered, info = renderer.render(
            prompt_id, "v1", language=language,
            topic=topic, history=history_filtered, players=players or [],
        )

    context = LLMCallContext(phase="closing", actor_role="owner")

    response = None
    parsed: Optional[str] = None
    parse_status = "ok"
    error: Optional[str] = None
    latency_ms = 0
    text = "A conversa foi boa, mas a ideia final se perdeu no barulho do bar."

    try:
        response, latency_ms = manager.complete(rendered, params)
        text = (response.text or "").strip()
        parsed = text
    except Exception as e:
        error = str(e)
        parse_status = "failed"

    _log(session_id=session_id, prompt_id=prompt_id, info=info, rendered=rendered,
         params=params, response=response, latency_ms=latency_ms,
         parse_status=parse_status, response_parsed=parsed, context=context,
         provider=manager.provider, model=manager.model, error=error)
    return text


def structure_for_lab(*, session_id, manager, summary, params, language: str = "pt") -> Dict[str, Any]:
    rendered, info = renderer.render("lab_structure", "v1", language=language, summary=summary)
    context = LLMCallContext(phase="closing", actor_role="lab")

    response = None
    parsed: Optional[Dict[str, Any]] = None
    parse_status = "failed"
    error: Optional[str] = None
    latency_ms = 0

    try:
        response, latency_ms = manager.complete(rendered, params)
        data, parse_status = parse_json_lenient(response.text)
        if isinstance(data, dict):
            parsed = data
    except Exception as e:
        error = str(e)

    _log(session_id=session_id, prompt_id="lab_structure", info=info, rendered=rendered,
         params=params, response=response, latency_ms=latency_ms,
         parse_status=parse_status, response_parsed=parsed, context=context,
         provider=manager.provider, model=manager.model, error=error)

    if not parsed:
        return {"title": "", "problem_statement": "", "core_solution": "",
                "key_features": [], "target_audience": "",
                "potential_impact": "", "next_steps": ""}

    next_steps = parsed.get("next_steps", "")
    if isinstance(next_steps, list):
        next_steps = "\n".join(str(x) for x in next_steps)

    return {
        "title": parsed.get("title", "") or "",
        "problem_statement": parsed.get("problem_statement", "") or "",
        "core_solution": parsed.get("core_solution", "") or "",
        "key_features": parsed.get("key_features", []) or [],
        "target_audience": parsed.get("target_audience", "") or "",
        "potential_impact": parsed.get("potential_impact", "") or "",
        "next_steps": next_steps or "",
    }
