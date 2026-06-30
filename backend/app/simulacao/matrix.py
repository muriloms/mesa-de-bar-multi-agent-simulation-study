"""Expansão da matriz de condições e estimativa de custo da simulação."""
import itertools
from typing import Dict, List

from plataforma.loader import BEST_IDEA_TO_QUEM_AVANCA
from simulacao.loader import Simulacao, JogadorPersona


def expand_cells(sim: Simulacao) -> List[Dict]:
    """Produto cartesiano das condições → lista de células (sem jogadores)."""
    c = sim.condicoes
    combos = itertools.product(
        c.best_idea, c.composicao, c.tema, c.rounds,
        c.source_blind_on_choice, c.judge_criterion, c.model_pairing,
    )
    cells = []
    for best_idea, comp, tema, rounds, blind, crit, pairing in combos:
        cells.append({
            "best_idea": best_idea,
            "quem_avanca": BEST_IDEA_TO_QUEM_AVANCA.get(best_idea, "jogador"),
            "composicao": comp,
            "tema": tema,
            "rounds": rounds,
            "source_blind_on_choice": blind,
            "judge_criterion": crit,
            "model_pairing": pairing,
        })
    return cells


def plan(sim: Simulacao, jogadores: List[JogadorPersona], table_size: int = 4) -> Dict:
    """Resumo do plano: nº de células, sessões e estimativa de chamadas LLM."""
    cells = expand_cells(sim)
    n_jog = max(1, len(jogadores))
    total_sessions = len(cells) * n_jog * sim.n_games
    # Estimativa de chamadas LLM por sessão:
    #   por rodada: jogador propõe(1) + N personas propõem(N) + juiz(1)
    #              + jogador escolhe(1) = N+3
    #   + síntese final do dono(1)
    avg_rounds = sum(sim.condicoes.rounds) / max(1, len(sim.condicoes.rounds))
    calls_per_session = avg_rounds * (table_size + 3) + 1
    total_calls = int(total_sessions * calls_per_session)
    return {
        "cells": len(cells),
        "jogadores": n_jog,
        "n_games": sim.n_games,
        "total_sessions": total_sessions,
        "approx_llm_calls": total_calls,
        "matrix": cells,
    }
