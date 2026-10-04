from __future__ import annotations

import pytest

from app.models import RecommendedAction, SessionInsight
from app.routers.clickstream import _should_push


def _insight(conf=0.80, action_type="show_comparison", prior_type=None):
    action = RecommendedAction(type=action_type, message="test", trigger="test")
    prior = None
    if prior_type is not None:
        prior = SessionInsight(
            confidence=0.75,
            recommended_action=RecommendedAction(type=prior_type, message="old", trigger="old"),
        )
    ins = SessionInsight(confidence=conf, recommended_action=action)
    return ins, prior


def test_push_passes_new_action():
    ins, prior = _insight(conf=0.80, action_type="show_comparison", prior_type="highlight_deal")
    assert _should_push(ins, prior) is True


def test_push_blocked_low_confidence():
    ins, prior = _insight(conf=0.50, action_type="show_comparison", prior_type=None)
    assert _should_push(ins, prior) is False


def test_push_blocked_same_action_type():
    ins, prior = _insight(conf=0.85, action_type="show_comparison", prior_type="show_comparison")
    assert _should_push(ins, prior) is False


def test_push_blocked_no_action():
    ins = SessionInsight(confidence=0.85, recommended_action=None)
    assert _should_push(ins, None) is False


def test_push_blocked_action_type_none():
    ins, _ = _insight(conf=0.90, action_type="none")
    assert _should_push(ins, None) is False


def test_push_passes_first_time():
    ins, _ = _insight(conf=0.75, action_type="highlight_deal", prior_type=None)
    # prior has no action
    prior = SessionInsight(confidence=0.0)
    assert _should_push(ins, prior) is True
