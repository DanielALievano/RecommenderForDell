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
# Mock implementation
# ---------------------------------------------------------------------------

_MOCK_PRODUCTS: dict[str, dict[str, Any]] = {
    "Dell XPS 15": {
        "id": "xps-15-9530",
        "name": "Dell XPS 15 9530",
        "price": "$1,499",
        "image": "https://i.dell.com/is/image/DellContent/content/dam/images/products/laptops/xps/xps-15-9530.png",
        "badge": "Best Seller",
        "specs": "13th Gen Intel Core i7, 16GB RAM, 512GB SSD",
        "url": "https://www.dell.com/en-us/shop/dell-laptops/xps-15-laptop/spd/xps-15-9530-laptop",
    },
    "Dell Inspiron 16 Plus": {
        "id": "inspiron-16-plus-7630",
        "name": "Dell Inspiron 16 Plus 7630",
        "price": "$999",
        "image": "https://i.dell.com/is/image/DellContent/content/dam/images/products/laptops/inspiron/inspiron-16-plus.png",
        "badge": "Great Value",
        "specs": "13th Gen Intel Core i5, 16GB RAM, 512GB SSD",
        "url": "https://www.dell.com/en-us/shop/dell-laptops/inspiron-16-plus-laptop/spd/inspiron-16-7630-laptop",
    },
    "Dell Precision 5680": {
        "id": "precision-5680",
        "name": "Dell Precision 5680",
        "price": "$2,199",
        "image": "https://i.dell.com/is/image/DellContent/content/dam/images/products/workstations/precision/precision-5680.png",
        "badge": "Workstation Power",
        "specs": "13th Gen Intel Core i9, 32GB RAM, 1TB SSD",
        "url": "https://www.dell.com/en-us/shop/workstations/precision-5680-workstation/spd/precision-15-5680-workstation",
    },
}

_DEFAULT_PRODUCT_KEYS = ["Dell XPS 15", "Dell Inspiron 16 Plus"]


def _make_dynamic_card(name: str) -> dict[str, Any]:
    """Generate a product card for any product name, even ones not in the mock catalog."""
    slug = name.lower().replace(" ", "-").replace("/", "-")
    return {
        "id": slug,
        "name": name,
        "price": "See pricing",
        "image": "",
        "badge": "Viewed by you",
        "specs": "Click to view full specifications",
        "url": f"https://www.dell.com/en-us/search/results?q={name.replace(' ', '+')}",
    }


class MockDiscoveryClient(DiscoveryClient):
    async def fetch(self, insight: SessionInsight) -> dict[str, Any]:
        action_type = insight.recommended_action.type if insight.recommended_action else "show_comparison"

        # Build product cards — first try catalog, then generate dynamic cards
        products = []
        for key in (insight.products_of_interest or _DEFAULT_PRODUCT_KEYS):
            # Try exact match first
            if key in _MOCK_PRODUCTS:
                products.append(_MOCK_PRODUCTS[key])
            else:
                # Fuzzy match against catalog
                match = next(
                    (v for k, v in _MOCK_PRODUCTS.items() if k.lower() in key.lower() or key.lower() in k.lower()),
                    None,
                )
                products.append(match if match else _make_dynamic_card(key))

        if not products:
            products = [_MOCK_PRODUCTS[k] for k in _DEFAULT_PRODUCT_KEYS]

        message = insight.recommended_action.message if insight.recommended_action else ""
        if not message:
            if len(products) >= 2:
                message = f"Based on your browsing — compare {products[0]['name']} and {products[1]['name']}."
            else:
                message = f"You've been looking at {products[0]['name']} — here's what to know."

        return {
            "products": products[:3],
            "message": message,
            "action_type": action_type,
        }


# ---------------------------------------------------------------------------
# Live implementation (stub — implement when ProductDiscovery agent is ready)
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
