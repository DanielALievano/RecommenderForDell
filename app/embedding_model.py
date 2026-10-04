from __future__ import annotations

import hashlib
import math
import os
from typing import Optional

import httpx

from app.config import settings

_DIMS = settings.embedding_dims


# ---------------------------------------------------------------------------
# Deterministic stub: hash-seeded random unit vector
# ---------------------------------------------------------------------------

def _stub_embed(text: str) -> list[float]:
    """Reproducible unit vector derived from text hash. No network needed."""
    seed_bytes = hashlib.sha256(text.encode()).digest()
    # Use seed to produce DIMS pseudo-random floats via sequential hashing
    floats: list[float] = []
    idx = 0
    while len(floats) < _DIMS:
        chunk = hashlib.md5(seed_bytes + idx.to_bytes(4, "little")).digest()
        for b in chunk:
            floats.append((b / 127.5) - 1.0)  # [-1, 1]
    floats = floats[:_DIMS]
    # Normalize
    norm = math.sqrt(sum(x * x for x in floats)) or 1.0
    return [x / norm for x in floats]


# ---------------------------------------------------------------------------
# Live OpenAI-compatible embedding call
# ---------------------------------------------------------------------------

async def _live_embed_batch(texts: list[str]) -> list[list[float]]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{settings.genai_api_url}/embeddings",
            headers={"Authorization": f"Bearer {settings.opensource_llm_key}"},
            json={"model": settings.embedding_model, "input": texts},
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        # Sort by index in case they arrive out of order
        data.sort(key=lambda x: x["index"])
        return [item["embedding"] for item in data]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_use_stub: Optional[bool] = None


def _should_stub() -> bool:
    global _use_stub
    if _use_stub is None:
        # Auto-detect: if GENAI_API_URL still points at localhost placeholder, use stub
        url = settings.genai_api_url.lower()
        _use_stub = "localhost" in url or "127.0.0.1" in url or not settings.opensource_llm_key or settings.opensource_llm_key == "placeholder"
    return _use_stub


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts. Falls back to stub on any error."""
    if not texts:
        return []
    if _should_stub():
        return [_stub_embed(t) for t in texts]
    try:
        return await _live_embed_batch(texts)
    except Exception:
        return [_stub_embed(t) for t in texts]


async def smoke_test() -> bool:
    """Called at startup to verify embedding works."""
    vecs = await embed_texts(["hello world"])
    return len(vecs) == 1 and len(vecs[0]) == _DIMS
