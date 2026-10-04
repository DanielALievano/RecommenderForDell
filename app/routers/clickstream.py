from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, Request

from app.config import settings
from app.discovery_client import DiscoveryClient
from app.llm_inference import run_inference
from app.models import (
    ClickstreamPayload,
    IngestResponse,
    NudgePayload,
    SessionInsight,
)
from app.narrative_parser import parse_narrative
from app.session_store import SessionStore
from app.sse import push_nudge
from app.vector_builder import build_chunk_vector
from app.vector_math import ema_update, should_act

router = APIRouter(prefix="/api/clickstream", tags=["clickstream"])


def _get_store(request: Request) -> SessionStore:
    return request.app.state.store


def _get_discovery(request: Request) -> DiscoveryClient:
    return request.app.state.discovery


@router.post("/ingest", response_model=IngestResponse, status_code=202)
async def ingest(
    payload: ClickstreamPayload,
    background_tasks: BackgroundTasks,
    store: SessionStore = Depends(_get_store),
    discovery: DiscoveryClient = Depends(_get_discovery),
) -> IngestResponse:
    sid = payload.session_id
    now = datetime.now(timezone.utc).isoformat()

    # --- 1. Upsert meta (first_seen + llm_call_count only if absent) ---
    existing_meta = await store.hget_all(sid, "meta")
    meta_update: dict = {
        "session_id": sid,
        "visit_number": payload.visit_number,
        "page_url": payload.page_url,
        "page_title": payload.page_title,
        "referrer": payload.referrer,
        "active_seconds": payload.active_seconds,
        "total_events": payload.total_events,
        "last_seen": now,
        "last_trigger": payload.trigger,
    }
    if not existing_meta:
        meta_update["first_seen"] = now
        meta_update["llm_call_count"] = 0

    await store.hset(sid, "meta", meta_update)

    # --- Append narrative chunk ---
    chunk_obj = {
        "ts": now,
        "trigger": payload.trigger,
        "active_seconds": payload.active_seconds,
        "total_events": payload.total_events,
        "text": payload.narrative,
    }
    chunks_stored = await store.list_append(sid, "narrative", chunk_obj)

    await store.reset_ttl(sid)

    # --- 2. Parse ---
    parsed = parse_narrative(payload.narrative)

    # --- 3. No vector contributors -> stop ---
    if not parsed.vector_signals:
        return IngestResponse(acted=False, delta=0.0, signal_count=0, chunks_stored=chunks_stored)

    # --- 4. Build chunk vector + EMA update ---
    chunk_vec = await build_chunk_vector(parsed.vector_signals)
    if chunk_vec is None:
        return IngestResponse(acted=False, delta=0.0, signal_count=len(parsed.vector_signals), chunks_stored=chunks_stored)

    prev_vec_raw = await store.get_json(sid, "vector")
    prev_vec: list[float] | None = prev_vec_raw if isinstance(prev_vec_raw, list) else None

    session_vec = ema_update(prev_vec, chunk_vec)
    await store.set_json(sid, "vector", session_vec)

    # --- 5. Cosine delta + threshold ---
    insight_raw = await store.get_json(sid, "insight")
    prior_insight: SessionInsight | None = None
    if isinstance(insight_raw, dict):
        prior_insight = SessionInsight.model_validate(insight_raw)

    baseline = prior_insight.vector_baseline if prior_insight else None
    acted, delta = should_act(session_vec, baseline)

    # --- 6. Return 202 immediately ---
    response = IngestResponse(
        acted=acted,
        delta=round(delta, 4),
        signal_count=len(parsed.vector_signals),
        chunks_stored=chunks_stored,
    )

    # --- 7. Background inference if acted ---
    if acted:
        background_tasks.add_task(
            _run_background_inference,
            sid=sid,
            store=store,
            discovery=discovery,
            session_vec=session_vec,
            prior_insight=prior_insight,
            delta=delta,
        )

    return response


async def _run_background_inference(
    sid: str,
    store: SessionStore,
    discovery: DiscoveryClient,
    session_vec: list[float],
    prior_insight: SessionInsight | None,
    delta: float,
) -> None:
    meta = await store.hget_all(sid, "meta")
    all_chunks = await store.list_get_all(sid, "narrative")
    recent_chunks = all_chunks[-settings.recent_raw_chunks:]

    try:
        insight = await run_inference(
            meta=meta,
            prior_insight=prior_insight,
            recent_chunks=recent_chunks,
            delta=delta,
        )
    except Exception:
        insight = prior_insight or SessionInsight()

    # Update baseline & counts
    insight.vector_baseline = session_vec
    insight.chunks_seen = len(all_chunks)
    insight.llm_call_count = (prior_insight.llm_call_count + 1) if prior_insight else 1

    await store.set_json(sid, "insight", insight.model_dump())
    await store.hset(sid, "meta", {"llm_call_count": insight.llm_call_count})
    await store.reset_ttl(sid)

    # Push gate
    if not _should_push(insight, prior_insight):
        return

    display = await discovery.fetch(insight)
    nudge = NudgePayload(
        action_type=insight.recommended_action.type,  # type: ignore[union-attr]
        message=display.get("message", ""),
        products=display.get("products", []),
        trigger=insight.recommended_action.trigger if insight.recommended_action else "",  # type: ignore[union-attr]
        confidence=insight.confidence,
    )
    await push_nudge(sid, nudge)


def _should_push(insight: SessionInsight, prior: SessionInsight | None) -> bool:
    if insight.confidence < settings.push_min_confidence:
        return False
    if not insight.recommended_action:
        return False
    if insight.recommended_action.type in ("none", "null", ""):
        return False
    prior_type = prior.recommended_action.type if (prior and prior.recommended_action) else None
    if insight.recommended_action.type == prior_type:
        return False
    return True
