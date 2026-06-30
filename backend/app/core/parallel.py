"""Helpers pra rodar trabalho em paralelo dentro de handlers FastAPI.

Estratégia: cada chamada LLM (síncrona) roda em um thread separado via
`asyncio.to_thread()`, e `asyncio.gather()` espera todas terminarem.

Por que threads e não asyncio nativo:
  - LLM managers (google-generativeai, openai) ainda fazem IO bloqueante
    em muitos paths. Threads contornam isso sem mudar o LLMManager.
  - O GIL não atrapalha — IO de rede libera o GIL.

Limite de concorrência: até 8 tarefas simultâneas por chamada. Mais que
isso costuma estourar rate limits dos provedores.
"""
import asyncio
from typing import Awaitable, Callable, List, TypeVar

T = TypeVar("T")

DEFAULT_MAX_CONCURRENCY = 8


async def run_parallel(funcs: List[Callable[[], T]],
                       max_concurrency: int = DEFAULT_MAX_CONCURRENCY) -> List[T]:
    """Executa uma lista de funções síncronas em paralelo via thread pool.

    Cada função é chamada sem argumentos (use closures/partials pra passar args).
    Devolve os resultados na MESMA ORDEM da lista de entrada.

    Em caso de exceção numa das funções, a exceção é re-lançada após todas
    as outras terminarem (return_exceptions=True interno).
    """
    if not funcs:
        return []

    semaphore = asyncio.Semaphore(max_concurrency)

    async def _run(fn: Callable[[], T]) -> T:
        async with semaphore:
            return await asyncio.to_thread(fn)

    results = await asyncio.gather(
        *[_run(fn) for fn in funcs],
        return_exceptions=False,  # propaga primeira exception
    )
    return list(results)
