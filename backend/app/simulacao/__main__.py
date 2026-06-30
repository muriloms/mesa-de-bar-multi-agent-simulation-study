"""Execução da simulação pelo terminal: `python -m simulacao`.

Lê research_settings/simulacao.yaml, imprime o plano (com estimativa de custo) e
roda. Se dry_run estiver ativo, só mostra o plano e os parâmetros, sem chamar LLM.
"""
import asyncio
import sys
from datetime import datetime

from core import config
from simulacao.loader import load_simulacao, expand_players
from simulacao.matrix import plan
from simulacao.runner import run_simulation
from simulacao import progress


def main() -> int:
    sim = load_simulacao()
    jg = expand_players(sim)
    p = plan(sim, jg, table_size=config.TABLE_SIZE)
    print(f"Plano: {p['cells']} células × {p['jogadores']} jogadores × {p['n_games']} "
          f"jogos = {p['total_sessions']} sessões")
    print(f"~{p['approx_llm_calls']} chamadas LLM estimadas")
    if sim.dry_run:
        print("dry_run ativo — nenhuma sessão será executada.")
    rid = sim.run_id or datetime.now().strftime("sim_%Y%m%d_%H%M%S")
    progress.init_run(rid, p)
    res = asyncio.run(run_simulation(sim, run_id=rid))
    print("Resultado:", res)
    return 0


if __name__ == "__main__":
    sys.exit(main())
