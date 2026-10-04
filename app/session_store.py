from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

from app.config import settings


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------

class SessionStore(ABC):
    """Minimal KV interface used by the ingest pipeline."""

    @abstractmethod
    async def hget_all(self, session_id: str, key: str) -> dict[str, Any]:
        ...

    @abstractmethod
    async def hset(self, session_id: str, key: str, mapping: dict[str, Any]) -> None:
        ...

    @abstractmethod
    async def list_append(self, session_id: str, key: str, value: Any) -> int:
        """Append and return new length."""
        ...

    @abstractmethod
    async def list_get_all(self, session_id: str, key: str) -> list[Any]:
        ...

    @abstractmethod
    async def set_json(self, session_id: str, key: str, value: Any) -> None:
        ...

    @abstractmethod
    async def get_json(self, session_id: str, key: str) -> Optional[Any]:
        ...

    @abstractmethod
    async def reset_ttl(self, session_id: str) -> None:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...


# ---------------------------------------------------------------------------
# In-memory implementation
# ---------------------------------------------------------------------------

class _SessionData:
    __slots__ = ("data", "expires_at")

    def __init__(self, ttl: int):
        self.data: dict[str, Any] = {}
        self.expires_at: float = time.monotonic() + ttl


class InMemoryStore(SessionStore):
    def __init__(self, ttl: int = settings.session_ttl_seconds):
        self._ttl = ttl
        self._sessions: dict[str, _SessionData] = {}

    def _get_or_create(self, session_id: str) -> _SessionData:
        sd = self._sessions.get(session_id)
        if sd is None or time.monotonic() > sd.expires_at:
            sd = _SessionData(self._ttl)
            self._sessions[session_id] = sd
        return sd

    async def hget_all(self, session_id: str, key: str) -> dict[str, Any]:
        sd = self._sessions.get(session_id)
        if sd is None or time.monotonic() > sd.expires_at:
            return {}
        return dict(sd.data.get(key) or {})

    async def hset(self, session_id: str, key: str, mapping: dict[str, Any]) -> None:
        sd = self._get_or_create(session_id)
        existing: dict = sd.data.get(key) or {}
        existing.update(mapping)
        sd.data[key] = existing

    async def list_append(self, session_id: str, key: str, value: Any) -> int:
        sd = self._get_or_create(session_id)
        lst: list = sd.data.get(key) or []
        lst.append(value)
        sd.data[key] = lst
        return len(lst)

    async def list_get_all(self, session_id: str, key: str) -> list[Any]:
        sd = self._sessions.get(session_id)
        if sd is None or time.monotonic() > sd.expires_at:
            return []
        return list(sd.data.get(key) or [])

    async def set_json(self, session_id: str, key: str, value: Any) -> None:
        sd = self._get_or_create(session_id)
        sd.data[key] = value

    async def get_json(self, session_id: str, key: str) -> Optional[Any]:
        sd = self._sessions.get(session_id)
        if sd is None or time.monotonic() > sd.expires_at:
            return None
        return sd.data.get(key)

    async def reset_ttl(self, session_id: str) -> None:
        sd = self._sessions.get(session_id)
        if sd is not None:
            sd.expires_at = time.monotonic() + self._ttl

    async def close(self) -> None:
        self._sessions.clear()


# ---------------------------------------------------------------------------
# Redis implementation
# ---------------------------------------------------------------------------

class RedisStore(SessionStore):
    """Requires `redis[hiredis]` and a running Redis server."""

    def __init__(self, url: str = settings.redis_url, ttl: int = settings.session_ttl_seconds):
        self._url = url
        self._ttl = ttl
        self._client: Any = None  # redis.asyncio.Redis

    async def _ensure(self) -> Any:
        if self._client is None:
            import redis.asyncio as aioredis  # type: ignore
            self._client = aioredis.from_url(
                self._url,
                decode_responses=True,
                ssl=settings.redis_tls,
            )
        return self._client

    def _mk(self, session_id: str, key: str) -> str:
        return f"lss:{session_id}:{key}"

    async def hget_all(self, session_id: str, key: str) -> dict[str, Any]:
        r = await self._ensure()
        raw = await r.hgetall(self._mk(session_id, key))
        return {k: json.loads(v) for k, v in raw.items()}

    async def hset(self, session_id: str, key: str, mapping: dict[str, Any]) -> None:
        r = await self._ensure()
        k = self._mk(session_id, key)
        await r.hset(k, mapping={mk: json.dumps(mv) for mk, mv in mapping.items()})
        await r.expire(k, self._ttl)

    async def list_append(self, session_id: str, key: str, value: Any) -> int:
        r = await self._ensure()
        k = self._mk(session_id, key)
        length = await r.rpush(k, json.dumps(value))
        await r.expire(k, self._ttl)
        return length

    async def list_get_all(self, session_id: str, key: str) -> list[Any]:
        r = await self._ensure()
        raw = await r.lrange(self._mk(session_id, key), 0, -1)
        return [json.loads(v) for v in raw]

    async def set_json(self, session_id: str, key: str, value: Any) -> None:
        r = await self._ensure()
        k = self._mk(session_id, key)
        await r.set(k, json.dumps(value))
        await r.expire(k, self._ttl)

    async def get_json(self, session_id: str, key: str) -> Optional[Any]:
        r = await self._ensure()
        raw = await r.get(self._mk(session_id, key))
        return json.loads(raw) if raw is not None else None

    async def reset_ttl(self, session_id: str) -> None:
        r = await self._ensure()
        for suffix in ("meta", "narrative", "vector", "insight"):
            await r.expire(self._mk(session_id, suffix), self._ttl)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_store() -> SessionStore:
    if settings.store_backend == "redis":
        return RedisStore()
    return InMemoryStore()
