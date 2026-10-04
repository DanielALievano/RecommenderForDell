from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from app.config import settings
from app.models import RecommendedAction, SessionInsight

_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```")


def _strip_fences(text: str) -> str:
    m = _FENCE.search(text)
    return m.group(1) if m else text.strip()


def _parse_insight_json(raw: str) -> Optional[dict[str, Any]]:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        cleaned = _strip_fences(raw)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None


def _build_prompt(
    meta: dict[str, Any],
    prior_insight: Optional[SessionInsight],
    recent_chunks: list[Any],
    delta: float,
) -> tuple[str, str]:
    """Returns (system_prompt, user_prompt)."""
    system = (
        "You are a real-time session intelligence engine. "
        "Analyze browser behavioral signals and return ONLY valid JSON — "
        "no markdown, no prose, no code fences."
    )

    prior_text = (
        json.dumps(prior_insight.model_dump(exclude={"vector_baseline"}), indent=2)
        if prior_insight and prior_insight.intent
        else "None"
    )

    chunks_text = "\n\n".join(
        c.get("text", "") if isinstance(c, dict) else str(c)
        for c in recent_chunks
    )

    user = f"""## SESSION CONTEXT
page_url: {meta.get('page_url', '')}
page_title: {meta.get('page_title', '')}
visit_number: {meta.get('visit_number', 1)}
total_chunks: {meta.get('total_events', 0)}
intent_shift_magnitude: {delta:.3f}

## PREVIOUS UNDERSTANDING
{prior_text}

## NEW BEHAVIORAL EVIDENCE
{chunks_text}

## OUTPUT SCHEMA (return ONLY this JSON, no wrapper)
{{
  "intent": "<one-sentence summary>",
  "confidence": <0.0-1.0>,
  "decision_stage": "<browsing|exploring|evaluating|deciding>",
  "friction_point": "<empty string if none>",
  "products_of_interest": ["<product name>"],
  "recommended_action": {{
    "type": "<show_comparison|highlight_deal|suggest_config|offer_chat|none>",
    "message": "<user-facing message>",
    "trigger": "<what triggered this>"
  }} | null
}}"""
    return system, user


async def _call_llm(system: str, user: str) -> str:
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{settings.genai_api_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.opensource_llm_key}"},
            json={
                "model": settings.genai_llm_model,
                "temperature": 0.2,
                "max_tokens": 400,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


def _dict_to_insight(d: dict[str, Any], prior: Optional[SessionInsight]) -> SessionInsight:
    action_raw = d.get("recommended_action")
    action = None
    if isinstance(action_raw, dict) and action_raw.get("type") not in (None, "none", "null"):
        action = RecommendedAction(
            type=action_raw.get("type", "none"),
            message=action_raw.get("message", ""),
            trigger=action_raw.get("trigger", ""),
        )
    return SessionInsight(
        intent=d.get("intent", ""),
        confidence=float(d.get("confidence", 0.0)),
        decision_stage=d.get("decision_stage", "browsing"),
        friction_point=d.get("friction_point", ""),
        products_of_interest=d.get("products_of_interest", []),
        recommended_action=action,
        # bookkeeping preserved from prior
        vector_baseline=prior.vector_baseline if prior else None,
        chunks_seen=prior.chunks_seen if prior else 0,
        llm_call_count=prior.llm_call_count if prior else 0,
    )


_STUB_INSIGHT = SessionInsight(
    intent="User is browsing Dell laptops with interest in performance specs",
    confidence=0.72,
    decision_stage="evaluating",
    friction_point="",
    products_of_interest=["Dell XPS 15", "Dell Inspiron 16 Plus"],
    recommended_action=RecommendedAction(
        type="show_comparison",
        message="Compare the XPS 15 and Inspiron 16 Plus side-by-side",
        trigger="multi_pass high interest",
    ),
)


async def run_inference(
    meta: dict[str, Any],
    prior_insight: Optional[SessionInsight],
    recent_chunks: list[Any],
    delta: float,
) -> SessionInsight:
    """Call the LLM and return a SessionInsight. Falls back to stub on error."""
    if settings.genai_api_url.lower().startswith("http://localhost") or \
       settings.opensource_llm_key in ("placeholder", ""):
        # Offline stub
        stub = _STUB_INSIGHT.model_copy()
        stub.llm_call_count = (prior_insight.llm_call_count + 1) if prior_insight else 1
        stub.chunks_seen = meta.get("total_events", 0)
        stub.updated_at = datetime.now(timezone.utc).isoformat()
        return stub

    system, user = _build_prompt(meta, prior_insight, recent_chunks, delta)
    raw = await _call_llm(system, user)
    parsed = _parse_insight_json(raw)

    if parsed is None:
        # Retry once with explicit reminder
        raw2 = await _call_llm(system, user + "\n\nRemember: return ONLY valid JSON.")
        parsed = _parse_insight_json(raw2)

    if parsed is None:
        return prior_insight or SessionInsight()

    insight = _dict_to_insight(parsed, prior_insight)
    insight.llm_call_count = (prior_insight.llm_call_count + 1) if prior_insight else 1
    insight.chunks_seen = meta.get("total_events", 0)
    insight.updated_at = datetime.now(timezone.utc).isoformat()
    return insight
