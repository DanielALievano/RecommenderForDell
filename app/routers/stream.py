from __future__ import annotations

import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.sse import format_sse, register, unregister

router = APIRouter(prefix="/api/session", tags=["session"])

_KEEPALIVE_INTERVAL = 15  # seconds


@router.get("/stream/{session_id}")
async def stream(session_id: str, request: Request) -> StreamingResponse:
    async def event_generator():
        q = register(session_id)
        try:
            # Initial connection ack
            yield format_sse({"status": "connected", "session_id": session_id}, event="connected")

            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(q.get(), timeout=_KEEPALIVE_INTERVAL)
                    yield format_sse(payload, event="nudge")
                except asyncio.TimeoutError:
                    # Keepalive comment
                    yield ": keepalive\n\n"
        finally:
            unregister(session_id, q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
