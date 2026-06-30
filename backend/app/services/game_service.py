"""Camada de serviços do jogo — v2.

Novo loop de rodada (sem economia/aposta):
  1. Jogador escreve a ideia (cego às ideias de IA da rodada).
  2. Todas as personas IA propõem em paralelo (sem subconjunto sorteado).
  3. Ideias reveladas ANÔNIMAS; jogador escolhe a melhor.
  4. Juiz IA escolhe a melhor (cego à escolha do jogador).
  5. Revela autoria + escolhas; se divergem, jogador avalia.
  6. Avança a ideia conforme `quem_avanca` (juiz_ia | jogador).

Eventos novos: round.choices_revealed, player.picked, judge.picked,
round.choices_compared, player.judged, round.idea_advanced.
"""
import asyncio
import json
import random as _stdlib_random
from datetime import datetime, timezone
from typing import Dict, List, Optional

from core import ids, time as core_time, config
from core.exceptions import SessionNotFoundError

from domain.event import Event
from domain.exports import LabIdea
from domain.llm_call import LLMParams
from domain.persona import AIPersonaSetup
from domain.player import Player
from domain.protocol import Protocol
from domain.round import (
    AuthoredOption, ChatMessage, ChoiceOption, IdeaProposal, RoundReveal,
)
from domain.session import GameState, SetupPayload

from persistence import event_log, paths, session_store
from protocols import loader as protocol_loader
from prompts import registry as prompt_registry

from llm import tasks as llm_tasks
from llm.manager import LLMManager

from game.randomization import SessionRNG
from game.phase_engine import PhaseEngine


# Estado in-memory
game_sessions: Dict[str, GameState] = {}
session_starts: Dict[str, datetime] = {}
session_rngs: Dict[str, SessionRNG] = {}
session_protocols: Dict[str, Protocol] = {}
session_engines: Dict[str, PhaseEngine] = {}
session_internal_personas: Dict[str, Dict[int, "AIPersonaSetup"]] = {}

# Working set da rodada corrente (NÃO vai pro frontend durante a escolha):
session_proposals: Dict[str, List[IdeaProposal]] = {}     # propostas com autoria
session_choice_maps: Dict[str, Dict[str, int]] = {}       # ref anônimo → player_id
session_player_pick: Dict[str, str] = {}                  # ref escolhido pelo jogador


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _emit(session_id, event_type, *, actor="system", phase=None,
          round_num=None, payload=None) -> None:
    start = session_starts.get(session_id)
    elapsed = core_time.elapsed_ms(start) if start else 0
    event = Event(
        event_id=ids.event_id(), session_id=session_id,
        timestamp=core_time.iso_now(), elapsed_ms=elapsed,
        type=event_type, actor=actor, phase=phase, round=round_num,
        payload=payload or {},
    )
    event_log.append(session_id, event)


def _resolve_seed(protocol: Protocol) -> int:
    if protocol.randomization_seed is not None:
        return protocol.randomization_seed
    strategy = protocol.llm_seed_strategy or "random_logged"
    if strategy.startswith("fixed:"):
        return int(strategy.split(":", 1)[1])
    return _stdlib_random.randint(0, 2**31 - 1)


def _sync_state_with_engine(state: GameState, engine: PhaseEngine) -> None:
    state.phase_name = engine.current_phase_name
    state.round = engine.global_round
    state.total_rounds = engine.total_rounds


def _player_with_real_persona(session_id, player):
    internal = session_internal_personas.get(session_id, {}).get(player.id)
    if internal is None:
        return player
    return player.model_copy(update={"persona": internal})


def _make_manager(state: GameState, persona: Optional[AIPersonaSetup] = None) -> LLMManager:
    override = persona.llmOverride if persona else None
    if override and override.provider:
        provider = override.provider
        model = override.model or state.global_llm_config.model
        api_key = override.apiKey or state.global_llm_config.apiKey
    else:
        provider = state.global_llm_config.provider
        model = state.global_llm_config.model
        api_key = state.global_llm_config.apiKey
    return LLMManager(provider=provider, model=model, api_key=api_key)


def _player_by_id(state: GameState, pid: int) -> Optional[Player]:
    return next((p for p in state.players if p.id == pid), None)


# ---------------------------------------------------------------------------
# Criação da sessão
# ---------------------------------------------------------------------------
def create_game_session(session_id: str, payload: SetupPayload,
                        dynamics_override: Optional[dict] = None) -> GameState:
    protocol_id = payload.protocol_id or "default"
    protocol = protocol_loader.load_protocol(protocol_id)
    # Overrides da plataforma (research_settings/plataforma.yaml): rodadas e
    # dinâmicas do jogo passam a ser controladas por esse arquivo central.
    try:
        from plataforma.loader import load_plataforma, BEST_IDEA_TO_QUEM_AVANCA
        _plat = load_plataforma()
        protocol.rounds = _plat.rounds
        protocol.quem_avanca = BEST_IDEA_TO_QUEM_AVANCA.get(
            _plat.dynamics.best_idea, protocol.quem_avanca)
        protocol.judge.criterion = _plat.dynamics.judge_criterion
        protocol.judge.blind_to_source = _plat.dynamics.judge_blind_to_source
        protocol.source_blind_on_choice = _plat.dynamics.source_blind_on_choice
        protocol.owner.bias = _plat.dynamics.owner_bias
    except Exception:
        pass
    # Override por sessão (usado pela simulação, para a célula da matriz).
    if dynamics_override:
        try:
            if "rounds" in dynamics_override:
                protocol.rounds = int(dynamics_override["rounds"])
            if "quem_avanca" in dynamics_override:
                protocol.quem_avanca = dynamics_override["quem_avanca"]
            if "judge_criterion" in dynamics_override:
                protocol.judge.criterion = dynamics_override["judge_criterion"]
            if "judge_blind_to_source" in dynamics_override:
                protocol.judge.blind_to_source = bool(dynamics_override["judge_blind_to_source"])
            if "source_blind_on_choice" in dynamics_override:
                protocol.source_blind_on_choice = bool(dynamics_override["source_blind_on_choice"])
        except Exception:
            pass
    seed = _resolve_seed(protocol)
    rng = SessionRNG(seed)
    engine = PhaseEngine(protocol.rounds)

    session_store.create(session_id)
    prompts_snapshot = [
        {"id": pid, "version": ver} for pid, ver in prompt_registry.all_known()
    ]
    composition_meta = None
    if payload.composition_id:
        try:
            from composicao_mesa.loader import load_table
            comp = load_table(payload.composition_id)
            composition_meta = {
                "id": comp.id, "title": comp.title,
                "description": comp.description, "tags": comp.tags,
            }
        except Exception:
            composition_meta = None

    manifest = {
        "session_id": session_id,
        "started_at": core_time.iso_now(),
        "status": "in_progress",
        "engine": "v2_n_rounds",
        "protocol_id": protocol.id,
        "protocol_version": protocol.version,
        "language": protocol.language,
        "rounds": protocol.rounds,
        "quem_avanca": protocol.quem_avanca,
        "source_blind_on_choice": protocol.source_blind_on_choice,
        "judge_criterion": protocol.judge.criterion,
        "reasoning_mode": protocol.reasoning_mode,
        "pre_session_instrument": protocol.instruments.pre_session,
        "post_session_instrument": protocol.instruments.post_session,
        "seed": seed,
        "llm": {
            "provider": payload.global_llm_config.provider,
            "model": payload.global_llm_config.model,
        },
        "user_name": payload.user_name,
        "topic": payload.idea_topic,
        "personas": [p.name for p in payload.ai_personas],
        "personas_detail": [p.model_dump() for p in payload.ai_personas],
        "composition": composition_meta,
        "prompts": prompts_snapshot,
    }
    session_store.write_manifest(session_id, manifest)
    session_store.write_protocol(session_id, protocol)

    players: List[Player] = []
    user_persona = AIPersonaSetup(
        name=payload.user_name, description="O idealizador da conversa.",
        role="Iniciador", goal="Apresentar e defender a ideia inicial.",
        instructions="Seja claro e aberto a feedback.",
    )
    players.append(Player(id=1, name=payload.user_name, persona=user_persona, is_ai=False))

    ai_personas = [] if protocol.display.solo_baseline else payload.ai_personas
    internal_personas: Dict[int, AIPersonaSetup] = {}

    for i, ai_persona in enumerate(ai_personas, start=2):
        if protocol.display.blind_personas:
            display_name = f"Persona {chr(64 + i - 1)}"
            exposed = ai_persona.model_copy(deep=True)
            exposed.name = display_name
            exposed.role = "—"
            exposed.description = "—"
            player = Player(id=i, name=display_name, persona=exposed, is_ai=True)
            internal_personas[i] = ai_persona
        else:
            player = Player(id=i, name=ai_persona.name, persona=ai_persona, is_ai=True)
        players.append(player)

    initial_message = ChatMessage(
        player_id=0, player_name="Dono do Bar",
        message=(f"A pauta da noite é: '{payload.idea_topic}'. "
                 f"{payload.user_name}, faça sua proposta."),
    )

    state = GameState(
        session_id=session_id, topic=payload.idea_topic, players=players,
        global_llm_config=payload.global_llm_config, conversation=[initial_message],
        seed=seed,
        pre_session_instrument=protocol.instruments.pre_session,
        post_session_instrument=protocol.instruments.post_session,
        game_phase="proposing",
    )
    _sync_state_with_engine(state, engine)

    game_sessions[session_id] = state
    session_starts[session_id] = datetime.now(timezone.utc)
    session_rngs[session_id] = rng
    session_protocols[session_id] = protocol
    session_engines[session_id] = engine
    session_internal_personas[session_id] = internal_personas
    session_proposals[session_id] = []
    session_choice_maps[session_id] = {}

    _emit(session_id, "session.created", payload={
        "user_name": payload.user_name, "topic": payload.idea_topic,
        "num_personas": len(payload.ai_personas),
        "personas": [p.name for p in payload.ai_personas],
        "llm_provider": payload.global_llm_config.provider,
        "llm_model": payload.global_llm_config.model,
        "seed": seed, "language": protocol.language,
        "rounds": protocol.rounds, "quem_avanca": protocol.quem_avanca,
        "source_blind_on_choice": protocol.source_blind_on_choice,
        "judge_criterion": protocol.judge.criterion,
    })
    _emit(session_id, "round.started", phase=engine.current_phase_name,
          round_num=engine.global_round,
          payload={"global_round": engine.global_round,
                   "total_rounds": engine.total_rounds})

    session_store.write_transcript(session_id, state)
    return state


# ---------------------------------------------------------------------------
# Runner experimental — cria sessão a partir de um estudo (atribuição balanceada)
# ---------------------------------------------------------------------------
def create_session_from_study(study_id: str, user_name: str,
                              global_llm_config,
                              chosen_topic: Optional[str] = None,
                              chosen_composition: Optional[str] = None) -> GameState:
    """Atribui braço × tópico × composição e cria a sessão.

    Respeita research_settings/plataforma.yaml: fonte da chave de API, e os
    modos de escolha de tema (random/choose/write) e de composição
    (random/choose). Quando o modo é 'random', sorteia.
    """
    from studies.loader import load_study
    from services import assignment as assignment_service
    from composicao_mesa import loader as comp_mesa_loader
    from temas import loader as temas_loader
    from plataforma.loader import load_plataforma
    import random as _rnd

    plat = load_plataforma()
    study = load_study(study_id)
    session_id = ids.session_id()
    asg = assignment_service.assign(study, session_id=session_id)  # braço: model-led × human-led

    # Chave da API: se a plataforma fornece a chave, usa a do arquivo.
    if not plat.api.user_provides_key and plat.api.key:
        try:
            global_llm_config = global_llm_config.model_copy(update={
                "provider": plat.api.provider, "model": plat.api.model, "apiKey": plat.api.key,
            })
        except Exception:
            pass

    # --- Composição da mesa: sorteia ou usa a escolha do usuário ---
    if plat.table.mode == "choose" and chosen_composition:
        try:
            comp = comp_mesa_loader.load_table(chosen_composition)
            pool = list(comp.personas)
            chosen = pool if len(pool) <= config.TABLE_SIZE else _rnd.sample(pool, config.TABLE_SIZE)
            table_draw = {"theme_id": comp.id, "theme_title": comp.title, "personas": chosen}
        except Exception:
            table_draw = comp_mesa_loader.draw_table(n_personas=config.TABLE_SIZE)
    else:
        table_draw = comp_mesa_loader.draw_table(n_personas=config.TABLE_SIZE)
    ai_personas = [AIPersonaSetup(**p.model_dump()) for p in table_draw["personas"]]

    # --- Assunto da mesa: sorteia, escolhe da lista, ou usa texto livre ---
    if plat.theme.mode in ("choose", "write") and chosen_topic and chosen_topic.strip():
        topic = chosen_topic.strip()
        topic_draw = {
            "area_id": "user_choice" if plat.theme.mode == "choose" else "user_written",
            "area_title": "Escolhido pelo usuário" if plat.theme.mode == "choose" else "Escrito pelo usuário",
            "subtema": topic,
        }
    else:
        topic_draw = temas_loader.draw_topic()
        topic = topic_draw["subtema"]

    payload = SetupPayload(
        user_name=user_name, idea_topic=topic, ai_personas=ai_personas,
        global_llm_config=global_llm_config, protocol_id=asg.arm,
        composition_id=table_draw["theme_id"],
    )
    state = create_game_session(session_id, payload)

    # Anota a condição no manifest (auditoria; participante não vê)
    try:
        manifest = session_store.read_manifest(session_id)
        manifest["study"] = {
            "study_id": study.id, "assignment_id": asg.assignment_id,
            "arm": asg.arm, "topic": asg.topic, "composition": asg.composition,
            "cell": asg.cell, "strategy": asg.strategy,
            "blind_condition": study.blind_condition,
        }
        # Sorteio efetivamente usado nesta sessão (fonte da verdade do que rodou).
        manifest["draw"] = {
            "table_theme_id": table_draw["theme_id"],
            "table_theme_title": table_draw["theme_title"],
            "personas": [p.name for p in table_draw["personas"]],
            "topic_area_id": topic_draw["area_id"],
            "topic_area_title": topic_draw["area_title"],
            "topic_subtema": topic_draw["subtema"],
        }
        session_store.write_manifest(session_id, manifest)
    except Exception:
        pass

    _emit(session_id, "study.assigned", payload={
        "study_id": study.id, "assignment_id": asg.assignment_id,
        "arm": asg.arm, "topic": asg.topic, "composition": asg.composition,
        "cell": asg.cell, "strategy": asg.strategy,
        "table_theme": table_draw["theme_id"],
        "topic_area": topic_draw["area_id"],
        "topic_subtema": topic_draw["subtema"],
    })
    return state


# ---------------------------------------------------------------------------
# Telemetria comportamental do humano
# ---------------------------------------------------------------------------
def store_telemetry(session_id: str, kind: str, events: list, metrics: dict) -> dict:
    if session_id not in game_sessions:
        raise SessionNotFoundError(session_id)
    engine = session_engines[session_id]
    protocol = session_protocols[session_id]

    if not protocol.telemetry.capture_keystrokes and not protocol.telemetry.aggregate_metrics:
        return {"stored": False}

    payload = {"kind": kind, "metrics": metrics}
    if protocol.telemetry.capture_keystrokes:
        payload["events"] = events

    _emit(session_id, "input.keystroke_log", actor="user",
          round_num=engine.global_round, phase=engine.current_phase_name,
          payload=payload)
    return {"stored": True, "events_count": len(events)}


# ---------------------------------------------------------------------------
# Rodada das IAs (paralelo): reflexão (opcional) + proposta. Temperatura fixa.
# ---------------------------------------------------------------------------
async def _run_ai_round_parallel(session_id, state, protocol, engine,
                                 participating: List) -> List[IdeaProposal]:
    temp = protocol.llm_temperature

    if protocol.memory.mode == "reflected_summary":
        async def _reflect_one(ai):
            manager = _make_manager(state, ai.persona)
            reflect_params = LLMParams(temperature=temp, max_tokens=120, seed=state.seed)
            previous_memo = state.persona_memos.get(ai.id, "")
            new_memo = await asyncio.to_thread(
                llm_tasks.reflect_persona,
                session_id=session_id, manager=manager,
                ai_player=_player_with_real_persona(session_id, ai),
                topic=state.topic, conversation_history=state.conversation,
                previous_memo=previous_memo, params=reflect_params,
                round_num=engine.global_round, phase=engine.current_phase_name,
                language=protocol.language,
            )
            return ai, new_memo

        reflect_results = await asyncio.gather(*[_reflect_one(ai) for ai in participating])
        for ai, new_memo in reflect_results:
            state.persona_memos[ai.id] = new_memo
            _emit(session_id, "persona.reflected", actor=f"ai_{ai.id}",
                  round_num=engine.global_round, phase=engine.current_phase_name,
                  payload={"player_id": ai.id, "memo": new_memo,
                           "memo_chars": len(new_memo or "")})

    async def _propose_one(ai):
        manager = _make_manager(state, ai.persona)
        params = LLMParams(temperature=temp, max_tokens=400, seed=state.seed)
        memo = state.persona_memos.get(ai.id, "")
        result = await asyncio.to_thread(
            llm_tasks.generate_proposal,
            session_id=session_id, manager=manager,
            ai_player=_player_with_real_persona(session_id, ai),
            topic=state.topic, conversation_history=state.conversation,
            params=params, round_num=engine.global_round, memo=memo,
            phase=engine.current_phase_name, reasoning_mode=protocol.reasoning_mode,
            language=protocol.language,
        )
        return ai, result

    propose_results = await asyncio.gather(*[_propose_one(ai) for ai in participating])

    name_to_id = {p.name.lower(): p.id for p in state.players}
    proposals: List[IdeaProposal] = []
    for ai, result in propose_results:
        refers_to_name = result.get("refers_to")
        refers_to_player_id = None
        if refers_to_name:
            refers_to_player_id = name_to_id.get(str(refers_to_name).strip().lower())
        proposals.append(IdeaProposal(
            player_id=ai.id, player_name=ai.name,
            idea_text=result.get("idea", ""), stance=result.get("stance"),
            refers_to_player_id=refers_to_player_id,
        ))
        _emit(session_id, "round.proposal_submitted", actor=f"ai_{ai.id}",
              round_num=engine.global_round, phase=engine.current_phase_name,
              payload={"player_id": ai.id, "idea_text": result.get("idea"),
                       "stance": result.get("stance"),
                       "refers_to_name": refers_to_name,
                       "refers_to_player_id": refers_to_player_id,
                       "reasoning_mode": protocol.reasoning_mode,
                       "reasoning": result.get("reasoning"),
                       "idea_chars": len(str(result.get("idea") or ""))})
    return proposals


def _build_choice_options(session_id, state, protocol, proposals: List[IdeaProposal]):
    """Monta as opções (anônimas se source_blind_on_choice) e o mapa ref→id."""
    rng = session_rngs[session_id]
    order = list(range(len(proposals)))
    if protocol.source_blind_on_choice:
        rng._rng.shuffle(order)  # embaralha pra não vazar autoria pela ordem
    options: List[ChoiceOption] = []
    ref_map: Dict[str, int] = {}
    for slot, idx in enumerate(order, start=1):
        ref = f"opt_{slot}"
        prop = proposals[idx]
        options.append(ChoiceOption(ref=ref, idea_text=prop.idea_text))
        ref_map[ref] = prop.player_id
    return options, ref_map


def _enter_choosing(session_id, state, protocol, engine, proposals):
    session_proposals[session_id] = proposals
    options, ref_map = _build_choice_options(session_id, state, protocol, proposals)
    session_choice_maps[session_id] = ref_map
    state.choice_options = options
    state.current_proposals = []          # não vaza autoria pro frontend
    state.round_reveal = None
    state.game_phase = "choosing"
    _emit(session_id, "round.choices_revealed", phase=engine.current_phase_name,
          round_num=engine.global_round,
          payload={"num_options": len(options),
                   "anonymous": protocol.source_blind_on_choice,
                   "refs": [o.ref for o in options]})
    session_store.write_transcript(session_id, state)


# ---------------------------------------------------------------------------
# 1) Humano submete a ideia da rodada
# ---------------------------------------------------------------------------
async def submit_user_idea(session_id, user_id: int, idea_text: str) -> GameState:
    if session_id not in game_sessions:
        raise SessionNotFoundError(session_id)
    state = game_sessions[session_id]
    protocol = session_protocols[session_id]
    engine = session_engines[session_id]

    user_player = _player_by_id(state, user_id)
    proposals: List[IdeaProposal] = [IdeaProposal(
        player_id=user_id, player_name=user_player.name, idea_text=idea_text,
    )]
    _emit(session_id, "round.proposal_submitted", actor="user",
          round_num=engine.global_round, phase=engine.current_phase_name,
          payload={"player_id": user_id, "idea_text": idea_text,
                   "idea_chars": len(idea_text or "")})

    all_ais = [p for p in state.players if p.is_ai]
    if all_ais:
        ai_proposals = await _run_ai_round_parallel(
            session_id, state, protocol, engine, participating=all_ais)
        proposals.extend(ai_proposals)

    _enter_choosing(session_id, state, protocol, engine, proposals)
    return state


# ---------------------------------------------------------------------------
# 1b) Humano passa a vez (não propõe)
# ---------------------------------------------------------------------------
async def submit_pass(session_id, user_id: int, justification: str = "") -> GameState:
    if session_id not in game_sessions:
        raise SessionNotFoundError(session_id)
    state = game_sessions[session_id]
    protocol = session_protocols[session_id]
    engine = session_engines[session_id]
    user_player = _player_by_id(state, user_id)

    _emit(session_id, "user.passed", actor="user", round_num=engine.global_round,
          phase=engine.current_phase_name,
          payload={"player_id": user_id, "justification": justification or "",
                   "justification_chars": len(justification or "")})
    msg = (f"{user_player.name} passou a vez: \"{justification}\""
           if justification else f"{user_player.name} passou a vez.")
    state.conversation.append(ChatMessage(player_id=0, player_name="Dono do Bar", message=msg))

    all_ais = [p for p in state.players if p.is_ai]
    if not all_ais:
        # solo_baseline + pass: nada a escolher — avança direto.
        return _advance_engine(session_id, state, engine, advanced_player_id=user_id,
                               advanced_name=user_player.name, rule="passou")

    proposals = await _run_ai_round_parallel(
        session_id, state, protocol, engine, participating=all_ais)
    _enter_choosing(session_id, state, protocol, engine, proposals)
    return state


# ---------------------------------------------------------------------------
# 2) Humano escolhe a melhor ideia (anônima) → roda juiz → revela
# ---------------------------------------------------------------------------
async def submit_player_pick(session_id, pick_ref: str) -> GameState:
    if session_id not in game_sessions:
        raise SessionNotFoundError(session_id)
    state = game_sessions[session_id]
    protocol = session_protocols[session_id]
    engine = session_engines[session_id]

    ref_map = session_choice_maps.get(session_id, {})
    proposals = session_proposals.get(session_id, [])
    if pick_ref not in ref_map:
        raise ValueError(f"Referência de escolha inválida: {pick_ref}")

    player_pick_id = ref_map[pick_ref]
    session_player_pick[session_id] = pick_ref
    player_pick_player = _player_by_id(state, player_pick_id)
    _emit(session_id, "player.picked", actor="user", round_num=engine.global_round,
          phase=engine.current_phase_name,
          payload={"pick_ref": pick_ref, "player_id": player_pick_id,
                   "player_name": player_pick_player.name,
                   "is_ai": player_pick_player.is_ai})

    # Juiz IA escolhe (cego à autoria e à escolha do jogador)
    jov = getattr(state, "judge_llm_override", None)
    if jov and jov.provider:
        manager = LLMManager(provider=jov.provider,
                             model=jov.model or state.global_llm_config.model,
                             api_key=jov.apiKey or state.global_llm_config.apiKey)
    else:
        manager = _make_manager(state)
    params = LLMParams(temperature=protocol.llm_temperature, max_tokens=10, seed=state.seed)
    judge_result = await asyncio.to_thread(
        llm_tasks.judge_choose,
        session_id=session_id, manager=manager, proposals=proposals,
        topic=state.topic, params=params, round_num=engine.global_round,
        criterion=protocol.judge.criterion, language=protocol.language,
    )
    judge_pick_id = judge_result["player_id"]
    judge_pick_player = _player_by_id(state, judge_pick_id)
    _emit(session_id, "judge.picked", actor="judge", round_num=engine.global_round,
          phase=engine.current_phase_name,
          payload={"player_id": judge_pick_id, "player_name": judge_pick_player.name,
                   "criterion": protocol.judge.criterion,
                   "rationale": judge_result.get("rationale")})

    match = (player_pick_id == judge_pick_id)
    _emit(session_id, "round.choices_compared", round_num=engine.global_round,
          phase=engine.current_phase_name,
          payload={"player_pick_id": player_pick_id, "judge_pick_id": judge_pick_id,
                   "match": match})

    # Monta autoria revelada (na ordem das opções anônimas mostradas)
    id_to_prop = {p.player_id: p for p in proposals}
    authored: List[AuthoredOption] = []
    for opt in state.choice_options:
        pid = ref_map.get(opt.ref)
        player = _player_by_id(state, pid)
        authored.append(AuthoredOption(
            ref=opt.ref, player_id=pid, player_name=player.name,
            idea_text=id_to_prop[pid].idea_text, is_ai=player.is_ai))

    reveal = RoundReveal(
        options=authored, player_pick_ref=pick_ref,
        player_pick_player_id=player_pick_id, player_pick_name=player_pick_player.name,
        judge_pick_player_id=judge_pick_id, judge_pick_name=judge_pick_player.name,
        judge_rationale=judge_result.get("rationale"), match=match,
    )
    state.round_reveal = reveal
    state.game_phase = "revealing"
    session_store.write_transcript(session_id, state)
    return state


# ---------------------------------------------------------------------------
# 3) Avança a rodada após revelação (registra julgamento no mismatch)
# ---------------------------------------------------------------------------
async def advance_round_after_reveal(session_id, agree_judge: Optional[bool] = None) -> GameState:
    if session_id not in game_sessions:
        raise SessionNotFoundError(session_id)
    state = game_sessions[session_id]
    protocol = session_protocols[session_id]
    engine = session_engines[session_id]
    reveal = state.round_reveal
    if reveal is None:
        raise ValueError("Não há revelação pendente para avançar.")

    # Julgamento do jogador no caso de divergência
    if not reveal.match:
        _emit(session_id, "player.judged", actor="user", round_num=engine.global_round,
              phase=engine.current_phase_name,
              payload={"agree_judge": bool(agree_judge),
                       "player_pick_id": reveal.player_pick_player_id,
                       "judge_pick_id": reveal.judge_pick_player_id})

    # Determina qual ideia avança
    if protocol.quem_avanca == "jogador":
        advanced_id = reveal.player_pick_player_id
        rule = "jogador"
    else:
        advanced_id = reveal.judge_pick_player_id
        rule = "juiz_ia"
    advanced_player = _player_by_id(state, advanced_id)

    # Anexa a ideia que avança à conversa (a trajetória da mesa)
    proposals = session_proposals.get(session_id, [])
    advanced_prop = next((p for p in proposals if p.player_id == advanced_id), None)
    if advanced_prop is not None:
        state.conversation.append(ChatMessage(
            player_id=advanced_player.id, player_name=advanced_player.name,
            message=advanced_prop.idea_text))

    reveal.advanced_player_id = advanced_id
    reveal.advanced_name = advanced_player.name
    reveal.advanced_rule = rule
    _emit(session_id, "round.idea_advanced", round_num=engine.global_round,
          phase=engine.current_phase_name,
          payload={"advanced_player_id": advanced_id,
                   "advanced_name": advanced_player.name, "rule": rule})

    return _advance_engine(session_id, state, engine,
                           advanced_player_id=advanced_id,
                           advanced_name=advanced_player.name, rule=rule)


def _advance_engine(session_id, state, engine, *, advanced_player_id,
                    advanced_name, rule) -> GameState:
    """Limpa o working set, avança a rodada/encerramento e prepara a próxima."""
    session_proposals[session_id] = []
    session_choice_maps[session_id] = {}
    session_player_pick.pop(session_id, None)
    state.choice_options = []

    engine.advance_round()
    _sync_state_with_engine(state, engine)

    if engine.finished:
        state.game_phase = "proposing"   # bloqueado no front; aguarda /end
        state.round_reveal = None
        _emit(session_id, "phase.entered", phase="closing",
              round_num=engine.global_round, payload={"phase": "closing"})
    else:
        state.game_phase = "proposing"
        state.round_reveal = None
        _emit(session_id, "round.started", phase=engine.current_phase_name,
              round_num=engine.global_round,
              payload={"global_round": engine.global_round,
                       "total_rounds": engine.total_rounds})

    session_store.write_transcript(session_id, state)
    return state


# ---------------------------------------------------------------------------
# Encerramento + síntese (Dono do Bar)
# ---------------------------------------------------------------------------
async def end_game_session(session_id: str) -> GameState:
    if session_id not in game_sessions:
        raise SessionNotFoundError(session_id)
    state = game_sessions[session_id]
    protocol = session_protocols[session_id]

    _emit(session_id, "phase.entered", phase="closing", payload={"phase": "closing"})

    manager = _make_manager(state)
    params = LLMParams(temperature=protocol.llm_temperature, max_tokens=700, seed=state.seed)
    summary = await asyncio.to_thread(
        llm_tasks.summarize_conversation,
        session_id=session_id, manager=manager, topic=state.topic,
        conversation_history=state.conversation, params=params,
        owner_bias=protocol.owner.bias, players=state.players,
        language=protocol.language,
    )

    state.final_summary = summary
    state.game_phase = "finished"
    _emit(session_id, "session.summary_generated", phase="closing",
          payload={"summary_length": len(summary or ""),
                   "owner_bias": protocol.owner.bias,
                   "had_summary": bool(summary and summary.strip())})

    manifest = session_store.read_manifest(session_id)
    manifest["status"] = "summary_ready"
    manifest["finished_at"] = core_time.iso_now()
    session_store.write_manifest(session_id, manifest)

    session_store.write_transcript(session_id, state)
    paths.final_idea_path(session_id).write_text(
        json.dumps({"summary": summary, "lab_idea": None}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    return state


# ---------------------------------------------------------------------------
# Estruturação da ideia (para stats/export) — mantido da v1
# ---------------------------------------------------------------------------
async def process_summary_for_lab(session_id: str) -> LabIdea:
    if session_id not in game_sessions:
        raise SessionNotFoundError(session_id)
    state = game_sessions[session_id]
    protocol = session_protocols[session_id]

    if not state.final_summary:
        await end_game_session(session_id)
    if not state.final_summary:
        raise ValueError("Resumo final não pôde ser gerado para esta sessão.")

    manager = _make_manager(state)
    params = LLMParams(temperature=protocol.llm_temperature, max_tokens=700, seed=state.seed)
    structured = await asyncio.to_thread(
        llm_tasks.structure_for_lab,
        session_id=session_id, manager=manager, summary=state.final_summary,
        params=params, language=protocol.language,
    )
    paths.final_idea_path(session_id).write_text(
        json.dumps({"summary": state.final_summary, "lab_idea": structured},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    _emit(session_id, "lab.structured", phase="closing",
          payload={"title": structured.get("title", "")})
    return LabIdea(**structured)


# ---------------------------------------------------------------------------
# Geração de personas
# ---------------------------------------------------------------------------
def generate_personas_for_theme(theme, provider, model, api_key) -> List[dict]:
    manager = LLMManager(provider=provider, model=model, api_key=api_key)
    params = LLMParams(temperature=0.5, max_tokens=500)
    return llm_tasks.generate_personas(manager=manager, theme=theme, params=params)
