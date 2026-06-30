"""Métricas de criatividade por distância semântica.

Foco em ORIGINALIDADE e FLEXIBILIDADE (a literatura alerta que fluência/
elaboração são manipuláveis com LLM no circuito). Tudo derivado de cosseno
entre embeddings.

- cosine_sim / cosine_dist: similaridade/distância entre dois vetores.
- originality_vs_pool: distância média de uma ideia às demais do mesmo pool
  (rodada/sessão). Quanto maior, mais original em relação ao pool.
- originality_vs_topic: distância da ideia ao embedding do tópico.
- diversity (spread): distância média par-a-par de um conjunto — mede
  flexibilidade do pool. Baixo = homogeneizado.
- centroid_distance: distância de um vetor ao centroide de um conjunto.
"""
import math
from typing import List, Optional


def _dot(a, b): return sum(x * y for x, y in zip(a, b))
def _norm(a): return math.sqrt(sum(x * x for x in a))


def cosine_sim(a: List[float], b: List[float]) -> float:
    na, nb = _norm(a), _norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return _dot(a, b) / (na * nb)


def cosine_dist(a: List[float], b: List[float]) -> float:
    return 1.0 - cosine_sim(a, b)


def centroid(vecs: List[List[float]]) -> List[float]:
    if not vecs:
        return []
    dim = len(vecs[0])
    c = [0.0] * dim
    for v in vecs:
        for i in range(dim):
            c[i] += v[i]
    return [x / len(vecs) for x in c]


def centroid_distance(vec: List[float], pool: List[List[float]]) -> Optional[float]:
    pool = [v for v in pool if v]
    if not vec or not pool:
        return None
    return cosine_dist(vec, centroid(pool))


def originality_vs_pool(vec: List[float], others: List[List[float]]) -> Optional[float]:
    """Distância média da ideia às demais ideias do pool (exclui ela mesma)."""
    others = [v for v in others if v]
    if not vec or not others:
        return None
    return sum(cosine_dist(vec, o) for o in others) / len(others)


def originality_vs_topic(vec: List[float], topic_vec: List[float]) -> Optional[float]:
    if not vec or not topic_vec:
        return None
    return cosine_dist(vec, topic_vec)


def diversity(vecs: List[List[float]]) -> Optional[float]:
    """Flexibilidade/spread: distância média de TODOS os pares do conjunto.

    Baixo => pool homogeneizado (ideias parecidas). É a medida central de H2.
    """
    vecs = [v for v in vecs if v]
    n = len(vecs)
    if n < 2:
        return None
    total = 0.0
    pairs = 0
    for i in range(n):
        for j in range(i + 1, n):
            total += cosine_dist(vecs[i], vecs[j])
            pairs += 1
    return total / pairs if pairs else None


def mean(xs: List[float]) -> Optional[float]:
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def stdev(xs: List[float]) -> Optional[float]:
    xs = [x for x in xs if x is not None]
    if len(xs) < 2:
        return None
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))
