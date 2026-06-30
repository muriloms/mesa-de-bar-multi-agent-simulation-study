"""Rotas HTTP da API (v2). Camada fina — só roteia para o services.game_service."""
from typing import List

from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse
import io

from pydantic import BaseModel

from core import ids
from domain.instrument import Instrument
from domain.payloads import (
    AdvancePayload, PassPayload, PlayerPickPayload,
    SessionOnlyPayload, StudyStartPayload, TelemetryPayload, UserIdeaPayload,
)
from domain.persona import AIPersonaSetup
from domain.session import GameState, SetupPayload

from instruments.loader import list_instruments
from protocols.loader import list_protocols_with_metadata
from composicao_mesa.loader import list_tables
from studies.loader import list_studies

from services import game_service
from services.costs import compute_session_costs
from services.export import export_session_zip, list_sessions
from services.stats import compute_session_stats
from services.idea_export import load_idea, idea_to_markdown
from services import instrument_service

router = APIRouter()

USER_ID = 1


class GeneratePersonaPayload(BaseModel):
    theme: str
    provider: str
    model: str | None = None
    api_key: str | None = None


@router.get("/")
async def read_root():
    return {"message": "Bem-vindo à API Mesa de Bar!"}


@router.get("/catalog")
async def get_catalog():
    """Estrutura viva de temas e composições lida no deploy.

    Reflete os arquivos de `temas/` e `composicao_mesa/`: contagens de áreas,
    subtemas, temas de mesa e personas, além de avisos/erros de validação.
    Útil para conferir, após um deploy, que a plataforma 'enxergou' as mudanças.
    """
    from catalog.catalog import build_catalog
    return build_catalog()


@router.get("/platform-config")
async def platform_config():
    """Configuração da plataforma para o frontend (o que está aberto/ativo).

    Inclui as listas de temas e composições quando o usuário pode escolher,
    para montar os seletores na tela inicial.
    """
    from plataforma.loader import load_plataforma
    from temas.loader import load_areas
    from composicao_mesa.loader import list_tables

    plat = load_plataforma()
    out = {
        "mode": plat.mode,
        "api": {"user_provides_key": plat.api.user_provides_key},
        "theme": {"mode": plat.theme.mode},
        "table": {"mode": plat.table.mode, "size": plat.table.size},
        "rounds": plat.rounds,
        "dynamics": {"best_idea": plat.dynamics.best_idea},
        "forms": {
            "pre_session_enabled": plat.forms.pre_session_enabled,
            "post_session_enabled": plat.forms.post_session_enabled,
        },
    }
    # Lista de temas (para mode=choose)
    if plat.theme.mode == "choose":
        try:
            out["theme"]["areas"] = [
                {"id": a.get("id"), "title": a.get("title"), "subtemas": a.get("subtemas", [])}
                for a in load_areas()
            ]
        except Exception:
            out["theme"]["areas"] = []
    # Lista de composições + personas (para mode=choose)
    if plat.table.mode == "choose":
        try:
            out["table"]["compositions"] = [
                {
                    "id": c.id, "title": c.title, "description": c.description,
                    "personas": [
                        {"name": p.name, "role": p.role, "description": p.description}
                        for p in c.personas
                    ],
                }
                for c in list_tables()
            ]
        except Exception:
            out["table"]["compositions"] = []
    return out


# --- Simulação (jogador = agente LLM) --------------------------------------
@router.get("/simulation/config")
async def simulation_config():
    """Parâmetros da simulação + personas-jogador + plano (contagens/custo)."""
    from simulacao.loader import load_simulacao, selected_jogadores, expand_players, list_jogadores
    from simulacao.matrix import plan
    from core import config as _cfg
    sim = load_simulacao()
    jg = expand_players(sim)
    return {
        "params": sim.model_dump(),
        "jogadores_disponiveis": [
            {"id": j.id, "name": j.name, "description": j.description,
             "temperature": j.llm.temperature, "traits": j.traits}
            for j in list_jogadores()
        ],
        "plan": {k: v for k, v in plan(sim, jg, table_size=_cfg.TABLE_SIZE).items() if k != "matrix"},
    }


@router.post("/simulation/start")
async def simulation_start(overrides: dict = Body(default={})):
    """Inicia uma execução de simulação (em background). Retorna o run_id.

    `overrides` pode trazer campos editados na tela (n_games, condicoes,
    jogadores, dry_run, ...), que são mesclados sobre o simulacao.yaml.
    """
    import asyncio
    from datetime import datetime
    from simulacao.loader import load_simulacao, Simulacao, expand_players
    from simulacao.matrix import plan
    from simulacao.runner import run_simulation
    from simulacao import progress
    from core import config as _cfg

    base = load_simulacao().model_dump()
    if overrides:
        base.update({k: v for k, v in overrides.items() if v is not None})
    sim = Simulacao(**base)

    run_id = sim.run_id or datetime.now().strftime("sim_%Y%m%d_%H%M%S")
    the_plan = plan(sim, expand_players(sim), table_size=_cfg.TABLE_SIZE)
    progress.init_run(run_id, the_plan)
    asyncio.create_task(run_simulation(sim, run_id=run_id))
    return {"run_id": run_id, "plan": {k: v for k, v in the_plan.items() if k != "matrix"}}


@router.get("/simulation/status/{run_id}")
async def simulation_status(run_id: str):
    from simulacao import progress
    st = progress.get(run_id)
    if st is None:
        return {"run_id": run_id, "status": "unknown"}
    return st


@router.post("/setup", response_model=GameState)
async def setup_game(payload: SetupPayload):
    session_id = ids.session_id()
    return game_service.create_game_session(session_id, payload)


@router.post("/generate-personas", response_model=List[AIPersonaSetup])
async def generate_personas(payload: GeneratePersonaPayload):
    return game_service.generate_personas_for_theme(
        theme=payload.theme,
        provider=payload.provider,
        model=payload.model or "gemini-1.5-flash",
        api_key=payload.api_key,
    )


# ---------------------------------------------------------------------------
# Estudos (runner experimental)
# ---------------------------------------------------------------------------
@router.get("/studies")
async def list_all_studies():
    return list_studies()


@router.post("/study/start", response_model=GameState)
async def study_start(payload: StudyStartPayload):
    """Inicia uma sessão sob um estudo — o runner atribui a condição (balanceado)."""
    return game_service.create_session_from_study(
        payload.study_id,
        payload.user_name,
        payload.global_llm_config,
        chosen_topic=payload.chosen_topic,
        chosen_composition=payload.chosen_composition,
    )


@router.get("/studies/{study_id}/balance")
async def study_balance(study_id: str):
    """Relatório de balanceamento do estudo (contagens por braço/célula)."""
    from studies.loader import load_study
    from services import assignment as assignment_service
    study = load_study(study_id)
    return assignment_service.balance_report(study)


# ---------------------------------------------------------------------------
# Análise (Fase C) — avaliação automática + export CAT
# ---------------------------------------------------------------------------
@router.get("/analysis/report")
async def analysis_report(study_id: str | None = None, backend: str | None = None):
    """Relatório de métricas por braço (originalidade, diversidade, etc.).

    Usa embeddings (backend google|local|hash via MDB_EMBED_BACKEND ou ?backend=).
    Pode ser lento/custar (chamadas de embedding) — chamada explícita.
    """
    from analysis import report as report_mod
    rep = report_mod.analyze(study_id=study_id, backend=backend)
    return {k: v for k, v in rep.items() if k not in ("ideas", "finals")}


@router.get("/studies/{study_id}/cat-export")
async def cat_export(study_id: str, include_proposals: bool = False):
    """Bundle CAT cego (ZIP): itens embaralhados + chave separada + instruções.

    Não usa embeddings — só lê as ideias finais e embaralha (rápido).
    """
    import io
    import zipfile
    from analysis import dataset
    from analysis.cat_export import build_cat_bundle, JUDGE_README

    sessions = dataset.load_all()
    sessions = [s for s in sessions if s["condition"].get("study_id") == study_id]
    finals = dataset.final_ideas(sessions)
    proposals = dataset.flatten_ideas(sessions) if include_proposals else None
    bundle = build_cat_bundle(finals, proposal_records=proposals)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("cat_items.csv", bundle["items_csv"])
        z.writestr("cat_key.csv", bundle["key_csv"])
        z.writestr("cat_README.md", JUDGE_README)
    buf.seek(0)
    filename = f"cat-{study_id}.zip"
    return StreamingResponse(
        buf, media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Painel CAT (Fase D) — coleta cega de notas + validação
# ---------------------------------------------------------------------------
class CatRatingItem(BaseModel):
    item_id: str
    novelty: int | None = None
    quality: int | None = None
    refinement: int | None = None


class CatRatingsPayload(BaseModel):
    judge_id: str
    ratings: List[CatRatingItem]


@router.post("/cat/{study_id}/materialize")
async def cat_materialize(study_id: str, include_proposals: bool = True, refresh: bool = False):
    """Materializa o bundle cego do estudo (operador). Inclui propostas por
    padrão — necessárias pra validar o juiz-IA por rodada."""
    from services import cat_service
    res = cat_service.materialize_bundle(study_id, include_proposals=include_proposals, refresh=refresh)
    return {"materialized": res["materialized"], "n_items": len(res["items"] or [])}


@router.get("/cat/{study_id}/items")
async def cat_items(study_id: str):
    """Itens CEGOS pro juiz (item_id + texto). Sem condição/autoria."""
    from services import cat_service
    return cat_service.get_items(study_id)


@router.post("/cat/{study_id}/ratings")
async def cat_submit_ratings(study_id: str, payload: CatRatingsPayload):
    from services import cat_service
    return cat_service.submit_ratings(
        study_id, payload.judge_id, [r.model_dump() for r in payload.ratings])


@router.get("/cat/{study_id}/validation")
async def cat_validation(study_id: str):
    """Validação: alpha entre juízes, hit-rate do juiz-IA, CAT por braço."""
    from analysis import cat_validation as cv
    return cv.validate(study_id)


# ---------------------------------------------------------------------------
# Loop de rodada (v2)
# ---------------------------------------------------------------------------
@router.post("/idea", response_model=GameState)
async def post_idea(payload: UserIdeaPayload):
    """Humano submete a ideia da rodada → IAs propõem → escolha anônima."""
    return await game_service.submit_user_idea(
        session_id=payload.session_id, user_id=USER_ID, idea_text=payload.idea_text,
    )


@router.post("/pass", response_model=GameState)
async def post_pass(payload: PassPayload):
    """Humano passa a vez (não propõe)."""
    return await game_service.submit_pass(
        session_id=payload.session_id, user_id=USER_ID,
        justification=payload.justification or "",
    )


@router.post("/pick", response_model=GameState)
async def post_pick(payload: PlayerPickPayload):
    """Humano escolhe a melhor ideia (anônima) → juiz IA escolhe → revela."""
    return await game_service.submit_player_pick(
        session_id=payload.session_id, pick_ref=payload.pick_ref,
    )


@router.post("/advance", response_model=GameState)
async def post_advance(payload: AdvancePayload):
    """Avança a rodada após revelação (registra julgamento no mismatch)."""
    return await game_service.advance_round_after_reveal(
        session_id=payload.session_id, agree_judge=payload.agree_judge,
    )


@router.post("/telemetry")
async def post_telemetry(payload: TelemetryPayload):
    return game_service.store_telemetry(
        session_id=payload.session_id, kind=payload.kind,
        events=payload.events, metrics=payload.metrics,
    )


@router.post("/end", response_model=GameState)
async def end_game(payload: SessionOnlyPayload):
    return await game_service.end_game_session(session_id=payload.session_id)


# ---------------------------------------------------------------------------
# Sessões / dados
# ---------------------------------------------------------------------------
@router.get("/sessions")
async def list_all_sessions():
    return list_sessions()


@router.get("/sessions/{session_id}/export")
async def export_session(session_id: str):
    data = export_session_zip(session_id)
    filename = f"mesa-de-bar-{session_id}.zip"
    return StreamingResponse(
        io.BytesIO(data), media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/sessions/{session_id}/costs")
async def get_session_costs(session_id: str):
    return compute_session_costs(session_id)


@router.get("/sessions/{session_id}/stats")
async def get_session_stats(session_id: str):
    return compute_session_stats(session_id)


@router.get("/sessions/{session_id}/idea")
async def get_session_idea(session_id: str):
    """Devolve a ideia estruturada (síntese + lab_idea). Gera se não existir."""
    idea = load_idea(session_id)
    if not idea.get("lab_idea"):
        try:
            await game_service.process_summary_for_lab(session_id=session_id)
            idea = load_idea(session_id)
        except Exception as e:
            idea["error"] = str(e)
    return idea


@router.get("/sessions/{session_id}/idea/markdown")
async def get_session_idea_markdown(session_id: str):
    idea = load_idea(session_id)
    if not idea.get("lab_idea"):
        try:
            await game_service.process_summary_for_lab(session_id=session_id)
            idea = load_idea(session_id)
        except Exception:
            pass
    stats = compute_session_stats(session_id)
    topic = stats.get("topic") or ""
    md = idea_to_markdown(idea, topic=topic)
    filename = f"mesa-de-bar-{session_id}-ideia.md"
    return StreamingResponse(
        io.BytesIO(md.encode("utf-8")), media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Catálogos
# ---------------------------------------------------------------------------
@router.get("/protocols")
async def list_all_protocols():
    return list_protocols_with_metadata()


@router.get("/compositions")
async def list_all_compositions():
    return [c.model_dump() for c in list_tables()]


@router.get("/instruments")
async def list_all_instruments():
    return list_instruments()


@router.get("/instruments/{instrument_id}", response_model=Instrument)
async def get_instrument(instrument_id: str):
    return instrument_service.get_instrument(instrument_id)


class InstrumentResponseSubmission(BaseModel):
    started_at: str
    submitted_at: str
    duration_ms: int
    responses: List[dict]
    response_order: List[str] = []


@router.post("/sessions/{session_id}/instruments/{instrument_id}/responses")
async def submit_instrument_response(
    session_id: str, instrument_id: str, payload: InstrumentResponseSubmission,
):
    return instrument_service.submit_instrument_response(
        session_id=session_id, instrument_id=instrument_id,
        started_at=payload.started_at, submitted_at=payload.submitted_at,
        duration_ms=payload.duration_ms, responses=payload.responses,
        response_order=payload.response_order,
    )
