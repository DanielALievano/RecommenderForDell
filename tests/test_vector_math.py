from __future__ import annotations

import math
import pytest

from app.vector_math import (
    cosine_distance,
    dot,
    ema_update,
    l2_normalize,
    should_act,
)


def _unit(values: list[float]) -> list[float]:
    return l2_normalize(values)


def test_l2_normalize_unit_length():
    v = l2_normalize([3.0, 4.0])
    assert math.isclose(math.sqrt(sum(x * x for x in v)), 1.0, abs_tol=1e-9)


def test_dot_product():
    a = _unit([1.0, 0.0])
    b = _unit([0.0, 1.0])
    assert dot(a, b) == pytest.approx(0.0, abs=1e-9)


def test_cosine_distance_identical():
    v = _unit([1.0, 2.0, 3.0])
    assert cosine_distance(v, v) == pytest.approx(0.0, abs=1e-9)


def test_cosine_distance_orthogonal():
    a = _unit([1.0, 0.0])
    b = _unit([0.0, 1.0])
    assert cosine_distance(a, b) == pytest.approx(1.0, abs=1e-9)


def test_ema_no_prev():
    chunk = _unit([1.0, 2.0, 3.0])
    result = ema_update(None, chunk)
    assert result == pytest.approx(chunk, abs=1e-9)


def test_ema_output_is_unit_vector():
    prev = _unit([1.0, 0.0, 0.0])
    chunk = _unit([0.0, 1.0, 0.0])
    result = ema_update(prev, chunk, alpha=0.30)
    norm = math.sqrt(sum(x * x for x in result))
    assert math.isclose(norm, 1.0, abs_tol=1e-9)


def test_ema_blends_correctly():
    prev = _unit([1.0, 0.0])
    chunk = _unit([1.0, 0.0])
    # Same direction -> result should still point the same way
    result = ema_update(prev, chunk, alpha=0.30)
    assert result[0] > 0.99


def test_should_act_no_baseline():
    v = _unit([1.0, 0.0, 0.0])
    acted, delta = should_act(v, None)
    assert acted is True
    assert delta == pytest.approx(1.0)


def test_should_act_identical_vectors():
    v = _unit([1.0, 2.0, 3.0])
    acted, delta = should_act(v, v, threshold=0.20)
    assert acted is False
    assert delta == pytest.approx(0.0, abs=1e-9)


def test_should_act_below_threshold():
    # Slightly rotated — delta < 0.20
    a = _unit([1.0, 0.0, 0.0])
    b = _unit([0.99, 0.14, 0.0])  # ~8 deg
    acted, delta = should_act(a, b, threshold=0.20)
    assert acted is False
    assert delta < 0.20


def test_should_act_above_threshold():
    a = _unit([1.0, 0.0, 0.0])
    b = _unit([0.5, 0.866, 0.0])  # 60 deg -> cos_dist=0.5
    acted, delta = should_act(a, b, threshold=0.20)
    assert acted is True
    assert delta == pytest.approx(0.5, abs=0.01)
