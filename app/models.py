from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Inbound
# ---------------------------------------------------------------------------

class ClickstreamPayload(BaseModel):
    session_id: str
    visit_number: int = 1
    page_url: str = ""
    page_title: str = ""
    referrer: str = ""
    active_seconds: int = 0
    total_events: int = 0
    trigger: str = ""
    narrative: str


# ---------------------------------------------------------------------------
# Parser output
# ---------------------------------------------------------------------------

class NarrativeSignal(BaseModel):
    timestamp_s: int = 0
    tier: int = 3
    confidence: float = 0.5
    event_type: str
    content_text: str = ""
    context_type: str = ""
    dwell_seconds: float = 0.0
    is_high_interest: bool = False


class ParsedNarrative(BaseModel):
    signals: list[NarrativeSignal] = Field(default_factory=list)
    vector_signals: list[NarrativeSignal] = Field(default_factory=list)
    thrash_count: int = 0
    frustration_count: int = 0
    max_scroll_depth: float = 0.0
    idle_detected: bool = False
    search_queries: list[str] = Field(default_factory=list)
    copied_texts: list[str] = Field(default_factory=list)
    applied_filters: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Session intelligence
# ---------------------------------------------------------------------------

class RecommendedAction(BaseModel):
    type: str
    message: str
    trigger: str = ""


class SessionInsight(BaseModel):
    intent: str = ""
    confidence: float = 0.0
    decision_stage: str = "browsing"   # browsing|exploring|evaluating|deciding
    friction_point: str = ""
    products_of_interest: list[str] = Field(default_factory=list)
    recommended_action: Optional[RecommendedAction] = None
    # Internal bookkeeping
    vector_baseline: Optional[list[float]] = None
    chunks_seen: int = 0
    llm_call_count: int = 0
    updated_at: str = ""


# ---------------------------------------------------------------------------
# API responses
# ---------------------------------------------------------------------------

class IngestResponse(BaseModel):
    acted: bool
    delta: float
    signal_count: int
    chunks_stored: int


# ---------------------------------------------------------------------------
# SSE push payload
# ---------------------------------------------------------------------------

class NudgePayload(BaseModel):
    action_type: str
    message: str
    products: list[dict[str, Any]] = Field(default_factory=list)
    trigger: str = ""
    confidence: float = 0.0
