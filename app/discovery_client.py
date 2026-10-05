from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.config import settings
from app.models import SessionInsight

# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------

class DiscoveryClient(ABC):
    @abstractmethod
    async def fetch(self, insight: SessionInsight) -> dict[str, Any]:
        """Return a display payload: {products: [...], message: str}."""
        ...


# ---------------------------------------------------------------------------
# Catalog-backed mock — recommends products the user has NOT seen
# ---------------------------------------------------------------------------

class MockDiscoveryClient(DiscoveryClient):
    async def fetch(self, insight: SessionInsight) -> dict[str, Any]:
        from app.catalog import extract_intent_signals, recommend

        seen = insight.products_of_interest or []
        signals = extract_intent_signals(insight.model_dump(), seen)
        recs = recommend(products_seen=seen, intent_signals=signals, n=3)

        action_type = insight.recommended_action.type if insight.recommended_action else "show_comparison"

        # Build message from the recommendation context
        if recs:
            if signals["use_case"] == "gaming":
                intro = "Based on your gaming interest"
            elif signals["use_case"] == "creator":
                intro = "For your creative work"
            elif signals["use_case"] == "business":
                intro = "For your business needs"
            elif signals["use_case"] == "student":
                intro = "Great picks for students"
            else:
                intro = "Based on your browsing"

            if len(recs) >= 2:
                message = f"{intro} — you haven't seen {recs[0]['name']} or {recs[1]['name']} yet. Worth a look."
            else:
                message = f"{intro} — the {recs[0]['name']} might be exactly what you're looking for."
        else:
            message = insight.recommended_action.message if insight.recommended_action else "Here are some options you haven't explored yet."

        return {
            "products": recs,
            "message": message,
            "action_type": action_type,
            "signals": signals,  # passed through for debug panel
        }


# ---------------------------------------------------------------------------
# Live implementation
# ---------------------------------------------------------------------------

class LiveDiscoveryClient(DiscoveryClient):
    async def fetch(self, insight: SessionInsight) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{settings.discovery_api_url}/recommend",
                headers={"Authorization": f"Bearer {settings.discovery_api_key}"},
                json={
                    "intent": insight.intent,
                    "products_of_interest": insight.products_of_interest,
                    "decision_stage": insight.decision_stage,
                },
            )
            resp.raise_for_status()
            return resp.json()


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_discovery_client() -> DiscoveryClient:
    if settings.discovery_mode == "live":
        return LiveDiscoveryClient()
    return MockDiscoveryClient()
