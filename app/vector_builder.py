from __future__ import annotations

from app.embedding_model import embed_texts
from app.models import NarrativeSignal
from app.vector_math import l2_normalize

# Event-type weights
_WEIGHTS: dict[str, float] = {
    "search_query":    3.0,
    "config_change":   2.5,
    "text_copy":       2.5,
    "filter_applied":  2.5,
    "compare_add":     2.0,
    "click":           2.0,
    "input_change":    2.0,
    "text_select":     1.8,
    "multi_pass":      1.5,
    # dwell types handled separately (use dwell_seconds)
    "dwell":           1.0,
    "viewport_dwell":  1.0,
    "touch_hold":      1.0,
}


def _signal_weight(sig: NarrativeSignal) -> float:
    if sig.event_type in ("dwell", "viewport_dwell", "touch_hold"):
        return max(sig.dwell_seconds, 0.5) * sig.confidence
    base = _WEIGHTS.get(sig.event_type, 1.0)
    return base * sig.confidence


async def build_chunk_vector(signals: list[NarrativeSignal]) -> list[float] | None:
    """
    Batch-embed all contributor texts in ONE call, weighted average, L2-normalize.
    Returns None if no usable signals.
    """
    if not signals:
        return None

    texts = [sig.content_text for sig in signals]
    weights = [_signal_weight(sig) for sig in signals]

    embeddings = await embed_texts(texts)
    if not embeddings:
        return None

    dims = len(embeddings[0])
    agg = [0.0] * dims
    total_weight = 0.0

    for emb, w in zip(embeddings, weights):
        for i in range(dims):
            agg[i] += emb[i] * w
        total_weight += w

    if total_weight == 0:
        return None

    avg = [x / total_weight for x in agg]
    return l2_normalize(avg)
