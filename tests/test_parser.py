from __future__ import annotations

import pytest

from app.narrative_parser import is_vector_contributor, parse_narrative
from app.models import NarrativeSignal

SAMPLE_NARRATIVE = """\
[10s] [T1 0.85] DWELL 8s on "Spring Sale Savings Up to $650 Off" (promo_banner)
[2s] [T2 0.7] CURSOR THRASH — hesitation/confusion
[44s] [T2 0.75] MULTI-PASS #2 on "DELL 14 PLUS LAPTOP" — HIGH INTEREST
[36s] [T3 0.5] CLICK "Next slide" (pagination)
[15s] [T1 0.80] SELECT "13th Gen Intel Core i5-1334U"
[90s] [T2 0.75] IDLE START — thinking pause (active: 84s)
[5s] [T1 0.90] SEARCH "dell xps 15 i7"
[20s] [T2 0.60] FILTER APPLIED "16GB RAM" (memory)
[8s] [T1 0.88] COMPARE ADD "Dell XPS 15"
[12s] [T3 0.35] SCROLL DEPTH 45%
[3s] [T2 0.55] RAGE CLICK on "Add to Cart" (checkout)
"""


def test_parse_sample_returns_signals():
    result = parse_narrative(SAMPLE_NARRATIVE)
    assert len(result.signals) >= 8


def test_thrash_counted():
    result = parse_narrative(SAMPLE_NARRATIVE)
    assert result.thrash_count == 1


def test_frustration_counted():
    result = parse_narrative(SAMPLE_NARRATIVE)
    assert result.frustration_count == 1  # rage_click


def test_idle_detected():
    result = parse_narrative(SAMPLE_NARRATIVE)
    assert result.idle_detected is True


def test_search_queries_captured():
    result = parse_narrative(SAMPLE_NARRATIVE)
    assert "dell xps 15 i7" in result.search_queries


def test_scroll_depth_captured():
    result = parse_narrative(SAMPLE_NARRATIVE)
    assert result.max_scroll_depth == pytest.approx(45.0)


def test_vector_signals_non_empty():
    result = parse_narrative(SAMPLE_NARRATIVE)
    assert len(result.vector_signals) > 0


def test_dwell_parsed_correctly():
    result = parse_narrative(SAMPLE_NARRATIVE)
    dwell_sigs = [s for s in result.signals if s.event_type == "dwell"]
    assert len(dwell_sigs) >= 1
    assert dwell_sigs[0].dwell_seconds == pytest.approx(8.0)


def test_compare_add_parsed():
    result = parse_narrative(SAMPLE_NARRATIVE)
    compare = [s for s in result.signals if s.event_type == "compare_add"]
    assert len(compare) == 1
    assert compare[0].content_text == "Dell XPS 15"


# ---------------------------------------------------------------------------
# Noise filter tests
# ---------------------------------------------------------------------------

def _sig(event_type="click", tier=2, confidence=0.6, context_type="", content_text="Buy now"):
    return NarrativeSignal(
        event_type=event_type,
        tier=tier,
        confidence=confidence,
        context_type=context_type,
        content_text=content_text,
    )


def test_navigation_context_excluded():
    assert is_vector_contributor(_sig(context_type="navigation")) is False


def test_pagination_excluded():
    assert is_vector_contributor(_sig(context_type="pagination")) is False


def test_tier3_low_conf_excluded():
    assert is_vector_contributor(_sig(tier=3, confidence=0.30)) is False


def test_tier3_high_conf_included():
    assert is_vector_contributor(_sig(tier=3, confidence=0.45)) is True


def test_skip_to_main_excluded():
    assert is_vector_contributor(_sig(content_text="skip to main content")) is False


def test_rage_click_excluded_from_vector():
    assert is_vector_contributor(_sig(event_type="rage_click")) is False


def test_cursor_thrash_excluded_from_vector():
    assert is_vector_contributor(_sig(event_type="cursor_thrash")) is False


def test_scroll_excluded_from_vector():
    assert is_vector_contributor(_sig(event_type="scroll_depth")) is False


def test_normal_click_included():
    assert is_vector_contributor(_sig(event_type="click", context_type="product_card")) is True


def test_empty_content_excluded():
    assert is_vector_contributor(_sig(content_text="")) is False
