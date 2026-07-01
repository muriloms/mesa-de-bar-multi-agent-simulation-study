"""Testa o módulo de simulação (matriz, plano, dry-run)."""
import sys, asyncio, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))

from simulacao.loader import load_simulacao, selected_jogadores  # noqa: E402
from simulacao.matrix import expand_cells, plan                  # noqa: E402
from simulacao.runner import run_simulation                      # noqa: E402
from simulacao import progress                                   # noqa: E402


def test_matriz_expande_produto_cartesiano():
    sim = load_simulacao()
    cells = expand_cells(sim)
    c = sim.condicoes
    esperado = (len(c.best_idea) * len(c.composicao) * len(c.tema) * len(c.rounds)
                * len(c.source_blind_on_choice) * len(c.judge_criterion) * len(c.model_pairing))
    assert len(cells) == esperado
    assert all("quem_avanca" in x and "model_pairing" in x for x in cells)


def test_plano_conta_sessoes_e_custo():
    sim = load_simulacao()
    p = plan(sim, selected_jogadores(sim), table_size=4)
    assert p["total_sessions"] == p["cells"] * p["jogadores"] * p["n_games"]
    assert p["approx_llm_calls"] > 0


def test_dry_run_gera_parametros(tmp_path):
    sim = load_simulacao().model_copy(update={"dry_run": True, "n_games": 2,
                                              "output_dir": str(tmp_path)})
    progress.init_run("t1", {"total_sessions": 0, "cells": 0})
    res = asyncio.run(run_simulation(sim, run_id="t1"))
    assert res["dry_run"] is True
    out = tmp_path / "t1"
    assert (out / "parametros.yaml").exists()
    assert (out / "run_manifest.json").exists()


def test_expand_players_cruza_temperaturas():
    from simulacao.loader import load_simulacao, expand_players
    sim = load_simulacao().model_copy(update={
        "jogadores": ["cauteloso", "ousado"], "temperaturas": [0.4, 1.0]})
    pl = expand_players(sim)
    ids = {p.id for p in pl}
    assert ids == {"cauteloso_t04", "cauteloso_t10", "ousado_t04", "ousado_t10"}
    temps = {p.id: p.llm.temperature for p in pl}
    assert temps["cauteloso_t04"] == 0.4 and temps["ousado_t10"] == 1.0


def test_model_pairing_entra_na_matriz():
    from simulacao.loader import load_simulacao
    from simulacao.matrix import expand_cells
    sim = load_simulacao().model_copy(update={"temperaturas": []})
    base = len(expand_cells(sim.model_copy(update={
        "condicoes": sim.condicoes.model_copy(update={"model_pairing": ["same_model"]})})))
    dobro = len(expand_cells(sim.model_copy(update={
        "condicoes": sim.condicoes.model_copy(update={"model_pairing": ["same_model", "cross_model"]})})))
    assert dobro == 2 * base


def test_novos_campos_carregam():
    from simulacao.loader import load_simulacao
    sim = load_simulacao()
    assert isinstance(sim.judge_blind_follows_choice, bool)
    assert isinstance(sim.yoked_seeds, list)
    # model_map valida estrutura por papel
    if sim.model_map:
        rm = next(iter(sim.model_map.values()))
        assert rm.personas.model and rm.judge.model and rm.player.model


def test_chamada_do_jogador_e_logada_e_entra_nos_custos():
    """As chamadas do jogador-agente vão para llm_calls.jsonl (actor_role=player)
    e entram no breakdown de custo, como personas/juiz/dono."""
    from services import game_service as G
    from domain.session import GlobalLlmConfig
    from persistence import paths
    from simulacao import agent
    from simulacao.loader import JogadorPersona, JogadorLLM
    from llm.client_base import LLMResponse
    from services.costs import compute_session_costs
    import json

    class FakeMgr:
        provider = "openai"; model = "gpt-4o-mini"
        def complete(self, prompt, params):
            return LLMResponse("ideia", tokens_in=50, tokens_out=10), 99

    st = G.create_session_from_study(
        "main", "T", GlobalLlmConfig(provider="openai", model="gpt-4o-mini", apiKey="k"))
    sid = st.session_id
    jog = JogadorPersona(id="cauteloso_t04", name="C", llm=JogadorLLM(temperature=0.4))
    agent.propose(FakeMgr(), jog, st.topic, session_id=sid, round_num=1)

    lines = paths.llm_log_path(sid).read_text(encoding="utf-8").splitlines()
    players = [json.loads(l) for l in lines
               if json.loads(l)["context"].get("actor_role") == "player"]
    assert len(players) == 1
    assert players[0]["tokens"] == {"in": 50, "out": 10}
    assert players[0]["latency_ms"] == 99
    assert players[0]["prompt_id"] == "sim_player_propose"

    cb = compute_session_costs(sid)
    assert any(k.startswith("player:") for k in cb["by_actor"])
