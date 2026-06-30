"""RNG por sessão, com seed registrado.

Toda decisão aleatória do jogo (subset de IAs que participa, ordem de
apresentação etc) passa por aqui. Garante reprodutibilidade quando a
sessão é replicada com o mesmo seed.
"""
import random
from typing import Optional, Sequence, TypeVar

T = TypeVar("T")


class SessionRNG:
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed if seed is not None else random.randint(0, 2**31 - 1)
        self._rng = random.Random(self.seed)

    def randint(self, a: int, b: int) -> int:
        return self._rng.randint(a, b)

    def sample(self, population: Sequence[T], k: int) -> list:
        return self._rng.sample(list(population), k)

    def random(self) -> float:
        return self._rng.random()
