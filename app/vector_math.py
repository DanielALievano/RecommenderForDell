from __future__ import annotations

import math
from typing import Optional

from app.config import settings


def l2_normalize(v: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / norm for x in v]


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def cosine_distance(a: list[float], b: list[float]) -> float:
    """Returns 1 - cosine_similarity. Assumes unit vectors."""
    return 1.0 - dot(a, b)


def ema_update(
    prev: Optional[list[float]],
    chunk: list[float],
    alpha: float = settings.vector_ema_alpha,
) -> list[float]:
    """
    EMA: new = prev*(1-alpha) + chunk*alpha, then re-normalize.
    If prev is None, return chunk as-is (already normalized by caller).
    """
    if prev is None:
        return chunk
    dims = len(chunk)
    result = [prev[i] * (1.0 - alpha) + chunk[i] * alpha for i in range(dims)]
    return l2_normalize(result)


def should_act(
    session_vector: list[float],
    baseline: Optional[list[float]],
    threshold: float = settings.cosine_delta_threshold,
) -> tuple[bool, float]:
    """
    Returns (acted, delta).
    delta = cosine distance between session_vector and baseline.
    If baseline is None -> delta = 1.0 (always act on first insight).
    """
    if baseline is None:
        return True, 1.0
    delta = cosine_distance(session_vector, baseline)
    return delta >= threshold, delta
