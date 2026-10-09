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

        # Attach a personalized reason to each product
        use_case = signals.get("use_case", "everyday")
        seen_names = seen[:2]  # up to 2 products the user browsed
        browsed_context = (
            f"you've been looking at {' and '.join(seen_names)}"
            if seen_names else "your recent browsing"
        )

        uc_phrases = {
            "gaming":      "gaming setup",
            "creator":     "creative workflow",
            "business":    "work needs",
            "student":     "studies",
            "workstation": "professional workloads",
            "everyday":    "everyday use",
        }
        uc_phrase = uc_phrases.get(use_case, "browsing interests")

        products_with_reasons = []
        for p in recs:
            p = dict(p)  # don't mutate catalog entry
            tier = p.get("tier", "mid")
            family = p.get("family", "")

            if tier == "flagship":
                reason = f"Since {browsed_context}, this is the top-tier upgrade you haven't seen yet."
            elif tier == "premium":
                reason = f"A strong match for your {uc_phrase} — not yet on your radar."
            elif tier == "budget":
                reason = f"Best value option for your {uc_phrase} that you haven't explored."
            else:
                reason = f"Complements what you've browsed — a fresh pick for your {uc_phrase}."

            p["reason"] = reason
            products_with_reasons.append(p)

        return {
            "products": products_with_reasons,
            "message": message,
            "action_type": action_type,
            "signals": signals,
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
