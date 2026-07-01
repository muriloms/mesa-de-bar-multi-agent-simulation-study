"""Runner headless da simulação: varre a matriz e roda o loop inteiro.

Suporta: model_pairing (modelo por papel), acoplamento da cegueira do juiz à
cegueira da escolha, sementes pareadas (yoked) entre fatores, persona do juiz
por simulação, e cruzamento persona × temperatura.
"""
import asyncio
import hashlib
import json
import random as _rnd
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

from core import config, ids
from domain.session import SetupPayload, GlobalLlmConfig
from domain.persona import AIPersonaSetup, LlmOverride
from persistence import session_store, paths
from services import game_service
from llm.manager import LLMManager
from plataforma.loader import load_plataforma
from composicao_mesa import loader as comp_mesa_loader
from temas import loader as temas_loader
from juiz.loader import load_juiz
from simulacao.loader import Simulacao, expand_players
from simulacao.matrix import expand_cells, plan
from simulacao import agent as player_agent
from simulacao import progress


def _output_dir(sim: Simulacao, run_id: str) -> Path:
    base = Path(sim.output_dir)
    if not base.is_absolute() and config.DATA_DIR.name == "data":
        base = config.DATA_DIR.parent / sim.output_dir
    return base / run_id


def _global_llm() -> GlobalLlmConfig:
    plat = load_plataforma()
    return GlobalLlmConfig(provider=plat.api.provider, model=plat.api.model, apiKey=plat.api.key)


def _topic_for(cell, rng) -> str:
    if cell["tema"] == "random":
        return temas_loader.draw_topic(rng)["subtema"]
    return cell["tema"]


def _personas_for(cell, rng):
    if cell["composicao"] == "random":
        d = comp_mesa_loader.draw_table(n_personas=config.TABLE_SIZE, rng=rng)
        return d["theme_id"], d["personas"]
    comp = comp_mesa_loader.load_table(cell["composicao"])
    pool = list(comp.personas)
    chosen = pool if len(pool) <= config.TABLE_SIZE else rng.sample(pool, config.TABLE_SIZE)
    return comp.id, chosen


def _resolve_pairing(sim: Simulacao, cell, key: str):
    """Retorna os overrides de modelo por papel para a célula, ou None."""
    rm = sim.model_map.get(cell.get("model_pairing")) if sim.model_map else None
    if not rm:
        return None
    mk = lambda role: LlmOverride(provider=role.provider, model=role.model, apiKey=key)
    return {"personas": mk(rm.personas), "judge": mk(rm.judge), "player": mk(rm.player)}


def _yoke(sim: Simulacao, cell, jogador, game_idx: int, run_id: str):
    """RNG determinístico que IGNORA os fatores yoked → células que diferem só
    nesses fatores compartilham tema + personas (e semente de LLM best-effort)."""
    yoked = set(sim.yoked_seeds or [])
    dims = {k: v for k, v in cell.items() if k not in yoked and k != "quem_avanca"}
    keyparts = (run_id, sim.seed, jogador.id, game_idx,
                tuple(sorted((k, str(v)) for k, v in dims.items())))
    rep = repr(keyparts)
    rng = _rnd.Random(rep)
    llm_seed = int(hashlib.sha256(rep.encode()).hexdigest(), 16) % (2**31)
    return rng, llm_seed


async def run_one_game(cell, jogador, run_id: str, mark: bool, sim: Simulacao,
                       juiz_id: Optional[str], game_idx: int,
                       out_dir: Optional[Path] = None) -> str:
    global_llm = _global_llm()
    key = global_llm.apiKey
    pairing = _resolve_pairing(sim, cell, key)

    # Sorteio pareável (yoked) de tema + personas + semente de LLM
    draw_rng, llm_seed = _yoke(sim, cell, jogador, game_idx, run_id)
    topic = _topic_for(cell, draw_rng)
    comp_id, personas = _personas_for(cell, draw_rng)

    ai_personas = [AIPersonaSetup(**p.model_dump()) for p in personas]
    if pairing:                                   # modelo das PERSONAS da mesa
        for ap in ai_personas:
            ap.llmOverride = pairing["personas"]

    session_id = ids.session_id()
    payload = SetupPayload(
        user_name=jogador.name, idea_topic=topic, ai_personas=ai_personas,
        global_llm_config=global_llm, protocol_id="default", composition_id=comp_id,
    )
    dyn = {
        "rounds": cell["rounds"],
        "quem_avanca": cell["quem_avanca"],
        "judge_criterion": cell["judge_criterion"],
        "source_blind_on_choice": cell["source_blind_on_choice"],
    }
    # Acoplamento do Fator C: cegueira do JUIZ segue a cegueira da ESCOLHA
    if sim.judge_blind_follows_choice:
        dyn["judge_blind_to_source"] = cell["source_blind_on_choice"]

    state = game_service.create_game_session(session_id, payload, dynamics_override=dyn)

    if pairing:                                   # modelo do JUIZ
        state.judge_llm_override = pairing["judge"]

    # Manager do JOGADOR-agente (modelo próprio se houver pareamento)
    if pairing:
        pm = pairing["player"]
        manager = LLMManager(provider=pm.provider, model=pm.model or global_llm.model,
                             api_key=pm.apiKey or key)
    else:
        manager = game_service._make_manager(state)

    human = next((p for p in state.players if not p.is_ai), None)
    human_id = human.id if human else 0
    decide_rng = _rnd.Random(f"{run_id}:{session_id}:advance")

    guard = 0
    round_i = 0
    while guard < cell["rounds"] + 2:
        guard += 1
        seed_r = (llm_seed + round_i) % (2**31) if sim.yoked_seeds else None
        idea = player_agent.propose(manager, jogador, state.topic, seed=seed_r,
                                    session_id=session_id, round_num=round_i + 1)
        state = await game_service.submit_user_idea(session_id, human_id, idea)
        ref = player_agent.pick(manager, jogador, state.topic, state.choice_options or [],
                                session_id=session_id, round_num=round_i + 1)
        if ref:
            state = await game_service.submit_player_pick(session_id, ref)
        agree = player_agent.decide_advance(jogador, decide_rng)
        state = await game_service.advance_round_after_reveal(session_id, agree_judge=agree)
        round_i += 1
        if getattr(state, "phase_name", "") == "closing" or getattr(state, "game_phase", "") == "finished":
            state = await game_service.end_game_session(session_id)
            break

    if mark:
        try:
            m = session_store.read_manifest(session_id)
            m["simulated"] = True
            m["sim_run_id"] = run_id
            m["player_persona"] = jogador.id
            m["player_temperature"] = jogador.llm.temperature
            m["sim_cell"] = cell
            m["judge_persona"] = juiz_id
            m["model_pairing"] = cell.get("model_pairing")
            session_store.write_manifest(session_id, m)
        except Exception:
            pass

    if out_dir is not None:
        try:
            src = paths.session_dir(session_id)
            if src.exists():
                dst_root = out_dir / "sessions"
                dst_root.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst_root / session_id))
        except Exception:
            pass
    return session_id


async def run_simulation(sim: Simulacao, run_id: Optional[str] = None,
                         progress_cb=None) -> dict:
    run_id = run_id or sim.run_id or datetime.now().strftime("sim_%Y%m%d_%H%M%S")
    jogadores = expand_players(sim)
    cells = expand_cells(sim)
    the_plan = plan(sim, jogadores, table_size=config.TABLE_SIZE)

    # Diagnóstico: ids realmente carregados dos arquivos vs. o que foi pedido.
    from simulacao.loader import list_jogadores
    disponiveis = [j.id for j in list_jogadores()]
    setup_errors = []
    if not jogadores:
        setup_errors.append(
            "Nenhum jogador-sintético resolvido. "
            f"Ids carregados de jogadores_simulados/: {disponiveis or 'NENHUM (arquivos ausentes/sem campo id)'}. "
            f"Pedido em 'jogadores': {sim.jogadores}. "
            "Use 'jogadores: todos' OU garanta que os ids batem com o campo 'id:' de cada arquivo "
            "(e deixe 'temperaturas: []' se você já criou um arquivo por temperatura).")
    if not cells:
        setup_errors.append("Nenhuma célula de condição — verifique o bloco 'condicoes'.")

    out_dir = _output_dir(sim, run_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    params_doc = {
        "run_id": run_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "seed": sim.seed,
        "n_games": sim.n_games,
        "jogadores": [j.id for j in jogadores],
        "jogadores_disponiveis": disponiveis,
        "temperaturas": sim.temperaturas,
        "condicoes": sim.condicoes.model_dump(),
        "model_map": {k: v.model_dump() for k, v in sim.model_map.items()},
        "juiz": sim.juiz,
        "judge_blind_follows_choice": sim.judge_blind_follows_choice,
        "yoked_seeds": sim.yoked_seeds,
        "formularios": sim.formularios,
        "mark_synthetic": sim.mark_synthetic,
        "dry_run": sim.dry_run,
        "plan": {k: v for k, v in the_plan.items() if k != "matrix"},
    }
    (out_dir / "parametros.yaml").write_text(
        yaml.safe_dump(params_doc, allow_unicode=True, sort_keys=False), encoding="utf-8")

    progress.update(run_id, output_dir=str(out_dir),
                    started_at=datetime.now().isoformat(timespec="seconds"))

    if sim.dry_run:
        (out_dir / "run_manifest.json").write_text(
            json.dumps({"run_id": run_id, "dry_run": True, **params_doc["plan"]},
                       ensure_ascii=False, indent=2), encoding="utf-8")
        progress.update(run_id, status="done", current="dry-run (sem execução)",
                        finished_at=datetime.now().isoformat(timespec="seconds"))
        return {"run_id": run_id, "dry_run": True, "plan": the_plan}

    # juiz da simulação (valida e carrega; criterion vem das condicoes/cell)
    juiz_id = sim.juiz
    if juiz_id:
        try:
            load_juiz(juiz_id)
        except Exception:
            juiz_id = None

    _rnd.seed(sim.seed)
    sessions, errors = [], []
    for ci, cell in enumerate(cells):
        for jogador in jogadores:
            for g in range(sim.n_games):
                desc = (f"célula {ci+1}/{len(cells)} · {jogador.id} · jogo {g+1}/{sim.n_games} "
                        f"· best_idea={cell['best_idea']} · pairing={cell.get('model_pairing')}")
                progress.update(run_id, current=desc)
                try:
                    sid = await run_one_game(cell, jogador, run_id, sim.mark_synthetic,
                                             sim, juiz_id, g, out_dir=out_dir)
                    sessions.append({"session_id": sid, "cell": ci, "persona": jogador.id})
                except Exception as e:
                    errors.append(str(e))
                progress.tick(run_id, current=desc)
                if progress_cb:
                    progress_cb(run_id)

    manifest = {
        "run_id": run_id,
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "total_sessions": len(sessions),
        "errors": errors,
        "sessions": sessions,
        **params_doc,
    }
    (out_dir / "run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    progress.update(run_id, status="error" if errors and not sessions else "done",
                    errors=errors[:20],
                    finished_at=datetime.now().isoformat(timespec="seconds"))
    return {"run_id": run_id, "sessions": len(sessions), "errors": len(errors),
            "output_dir": str(out_dir)}
