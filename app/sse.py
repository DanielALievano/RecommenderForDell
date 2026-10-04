from __future__ import annotations

import asyncio
import json
from typing import Any

from app.models import NudgePayload

# session_id -> list of queues (multiple tabs)
_registry: dict[str, list[asyncio.Queue]] = {}


def register(session_id: str) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue(maxsize=32)
    _registry.setdefault(session_id, []).append(q)
    return q


def unregister(session_id: str, q: asyncio.Queue) -> None:
    listeners = _registry.get(session_id, [])
    try:
        listeners.remove(q)
    except ValueError:
        pass
    if not listeners:
        _registry.pop(session_id, None)


async def push_nudge(session_id: str, nudge: NudgePayload) -> int:
    """Push nudge to all listeners for a session. Returns number of listeners notified."""
    listeners = _registry.get(session_id, [])
    payload = nudge.model_dump()
    for q in listeners:
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            pass  # slow consumer — drop
    return len(listeners)


def format_sse(data: Any, event: str | None = None) -> str:
    lines = []
    if event:
        lines.append(f"event: {event}")
    lines.append(f"data: {json.dumps(data)}")
    lines.append("")  # blank line terminates the event
    return "\n".join(lines) + "\n"
