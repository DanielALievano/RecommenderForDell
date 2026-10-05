"""
Dell product catalog — used by the recommendation engine to suggest
products the user has NOT yet seen, based on their behavioral signals.
"""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Tag taxonomy
# ---------------------------------------------------------------------------
# use_case: student, creator, business, gaming, workstation, everyday
# weight:   ultralight (<1.4kg), light (1.4-1.8kg), standard (1.8-2.3kg), heavy (>2.3kg)
# tier:     budget (<$800), mid ($800-1400), premium ($1400-2200), flagship (>$2200)
# screen:   13, 14, 15, 16, 17, 18  (inches)

CATALOG: list[dict[str, Any]] = [

    # ------------------------------------------------------------------ XPS
    {
        "id": "xps-13-9340",
        "name": "Dell XPS 13 9340",
        "family": "XPS",
        "category": "laptop",
        "price_usd": 1099,
        "tier": "premium",
        "screen_in": 13.4,
        "weight_kg": 1.17,
        "weight_class": "ultralight",
        "use_cases": ["everyday", "student", "creator", "business"],
        "highlights": ["Intel Core Ultra 7", "OLED option", "thunderbolt 4", "compact"],
        "specs": "Intel Core Ultra 7 155H, 16GB LPDDR5, 512GB SSD, 13.4\" FHD+",
        "badge": "Most Portable XPS",
        "url": "https://www.dell.com/en-us/shop/dell-laptops/xps-13-laptop/spd/xps-13-9340-laptop",
    },
    {
        "id": "xps-14-9440",
        "name": "Dell XPS 14 9440",
        "family": "XPS",
        "category": "laptop",
        "price_usd": 1499,
        "tier": "premium",
        "screen_in": 14.5,
        "weight_kg": 1.64,
        "weight_class": "light",
        "use_cases": ["creator", "everyday", "student", "business"],
        "highlights": ["OLED display", "NVIDIA GeForce RTX 4050", "Intel Core Ultra", "slim"],
        "specs": "Intel Core Ultra 7 155H, 16GB, 512GB SSD, NVIDIA RTX 4050, 14.5\" OLED",
        "badge": "Best Balance",
        "url": "https://www.dell.com/en-us/shop/dell-laptops/xps-14-laptop/spd/xps-14-9440-laptop",
    },
    {
        "id": "xps-15-9530",
        "name": "Dell XPS 15 9530",
        "family": "XPS",
        "category": "laptop",
        "price_usd": 1699,
        "tier": "premium",
        "screen_in": 15.6,
        "weight_kg": 1.86,
        "weight_class": "standard",
        "use_cases": ["creator", "everyday", "student"],
        "highlights": ["OLED 3.5K display", "NVIDIA RTX 4060", "13th Gen Intel", "InfinityEdge"],
        "specs": "Intel Core i7-13700H, 16GB DDR5, 512GB SSD, NVIDIA RTX 4060, 15.6\" OLED",
        "badge": "Creator Favorite",
        "url": "https://www.dell.com/en-us/shop/dell-laptops/xps-15-laptop/spd/xps-15-9530-laptop",
    },
    {
        "id": "xps-16-9640",
        "name": "Dell XPS 16 9640",
        "family": "XPS",
        "category": "laptop",
        "price_usd": 1999,
        "tier": "flagship",
        "screen_in": 16.3,
        "weight_kg": 2.0,
        "weight_class": "standard",
        "use_cases": ["creator", "everyday"],
        "highlights": ["OLED 3.2K", "Intel Core Ultra 9", "RTX 4070", "studio-class"],
        "specs": "Intel Core Ultra 9 185H, 32GB LPDDR5X, 1TB SSD, NVIDIA RTX 4070, 16.3\" OLED",
        "badge": "Flagship Creator",
        "url": "https://www.dell.com/en-us/shop/dell-laptops/xps-16-laptop/spd/xps-16-9640-laptop",
    },

    # ------------------------------------------------------------ Inspiron
    {
        "id": "inspiron-14-5440",
        "name": "Dell Inspiron 14 5440",
        "family": "Inspiron",
        "category": "laptop",
        "price_usd": 699,
        "tier": "mid",
        "screen_in": 14.0,
        "weight_kg": 1.54,
        "weight_class": "light",
        "use_cases": ["student", "everyday", "business"],
        "highlights": ["Intel Core i5", "lightweight", "all-day battery", "budget-friendly"],
        "specs": "Intel Core i5-1335U, 8GB DDR5, 512GB SSD, 14\" FHD",
        "badge": "Best Value",
        "url": "https://www.dell.com/en-us/shop/dell-laptops/inspiron-14-laptop/spd/inspiron-14-5440-laptop",
    },
    {
        "id": "inspiron-15-3530",
        "name": "Dell Inspiron 15 3530",
        "family": "Inspiron",
        "category": "laptop",
        "price_usd": 549,
        "tier": "budget",
        "screen_in": 15.6,
        "weight_kg": 1.81,
        "weight_class": "standard",
        "use_cases": ["student", "everyday"],
        "highlights": ["affordable", "15.6\" screen", "Intel Core i3/i5", "everyday tasks"],
        "specs": "Intel Core i5-1334U, 8GB DDR5, 256GB SSD, 15.6\" FHD",
        "badge": "Most Affordable",
        "url": "https://www.dell.com/en-us/shop/dell-laptops/inspiron-15-laptop/spd/inspiron-15-3530-laptop",
    },
    {
        "id": "inspiron-16-5640",
        "name": "Dell Inspiron 16 5640",
        "family": "Inspiron",
        "category": "laptop",
        "price_usd": 849,
        "tier": "mid",
        "screen_in": 16.0,
        "weight_kg": 1.95,
        "weight_class": "standard",
        "use_cases": ["student", "everyday", "creator"],
        "highlights": ["16\" display", "Intel Core i7", "discrete graphics option", "big screen"],
        "specs": "Intel Core i7-1355U, 16GB DDR5, 512GB SSD, 16\" FHD+",
        "badge": "Big Screen Value",
        "url": "https://www.dell.com/en-us/shop/dell-laptops/inspiron-16-laptop/spd/inspiron-16-5640-laptop",
    },
    {
        "id": "inspiron-plus-16-7640",
        "name": "Dell Inspiron 16 Plus 7640",
        "family": "Inspiron",
        "category": "laptop",
        "price_usd": 1149,
        "tier": "premium",
        "screen_in": 16.0,
        "weight_kg": 2.05,
        "weight_class": "standard",
        "use_cases": ["creator", "student", "everyday"],
        "highlights": ["Intel Core Ultra 7", "NVIDIA RTX 4060", "3K display", "mid-range powerhouse"],
        "specs": "Intel Core Ultra 7 155H, 16GB LPDDR5, 1TB SSD, NVIDIA RTX 4060, 16\" 3K",
        "badge": "Inspiron's Best",
        "url": "https://www.dell.com/en-us/shop/dell-laptops/inspiron-16-plus-laptop/spd/inspiron-16-7640-laptop",
    },
    {
        "id": "inspiron-14-plus-7440",
        "name": "Dell Inspiron 14 Plus 7440",
        "family": "Inspiron",
        "category": "laptop",
        "price_usd": 999,
        "tier": "mid",
        "screen_in": 14.0,
        "weight_kg": 1.58,
        "weight_class": "light",
        "use_cases": ["student", "creator", "everyday"],
        "highlights": ["Intel Core Ultra 5", "2.8K display", "compact powerhouse"],
        "specs": "Intel Core Ultra 5 125H, 16GB LPDDR5, 512GB SSD, 14\" 2.8K",
        "badge": "Compact Performance",
        "url": "https://www.dell.com/en-us/shop/dell-laptops/inspiron-14-plus-laptop/spd/inspiron-14-7440-laptop",
    },

    # ------------------------------------------------------------ Alienware
    {
        "id": "alienware-m16-r2",
        "name": "Alienware m16 R2",
        "family": "Alienware",
        "category": "laptop",
        "price_usd": 1699,
        "tier": "premium",
        "screen_in": 16.0,
        "weight_kg": 3.05,
        "weight_class": "heavy",
        "use_cases": ["gaming"],
        "highlights": ["Intel Core Ultra 9", "RTX 4070", "QHD+ 240Hz", "Cherry MX keyboard"],
        "specs": "Intel Core Ultra 9 185H, 16GB DDR5, 1TB SSD, NVIDIA RTX 4070, 16\" QHD+ 240Hz",
        "badge": "Gaming Beast",
        "url": "https://www.dell.com/en-us/shop/gaming-laptops/alienware-m16-r2-gaming-laptop/spd/alienware-m16-r2-laptop",
    },
    {
        "id": "alienware-m18-r2",
        "name": "Alienware m18 R2",
        "family": "Alienware",
        "category": "laptop",
        "price_usd": 2299,
        "tier": "flagship",
        "screen_in": 18.0,
        "weight_kg": 4.24,
        "weight_class": "heavy",
        "use_cases": ["gaming"],
        "highlights": ["Intel Core i9", "RTX 4090", "18\" FHD 480Hz", "desktop replacement"],
        "specs": "Intel Core i9-14900HX, 32GB DDR5, 1TB SSD, NVIDIA RTX 4090, 18\" FHD 480Hz",
        "badge": "Desktop Replacement",
        "url": "https://www.dell.com/en-us/shop/gaming-laptops/alienware-m18-r2-gaming-laptop/spd/alienware-m18-r2-laptop",
    },
    {
        "id": "alienware-x14-r2",
        "name": "Alienware x14 R2",
        "family": "Alienware",
        "category": "laptop",
        "price_usd": 1499,
        "tier": "premium",
        "screen_in": 14.0,
        "weight_kg": 1.88,
        "weight_class": "standard",
        "use_cases": ["gaming"],
        "highlights": ["slim gaming", "Intel Core i7", "RTX 4060", "144Hz", "portable"],
        "specs": "Intel Core i7-13620H, 16GB DDR5, 512GB SSD, NVIDIA RTX 4060, 14\" FHD 144Hz",
        "badge": "Slim Gamer",
        "url": "https://www.dell.com/en-us/shop/gaming-laptops/alienware-x14-r2-gaming-laptop/spd/alienware-x14-r2-laptop",
    },
    {
        "id": "alienware-x16-r2",
        "name": "Alienware x16 R2",
        "family": "Alienware",
        "category": "laptop",
        "price_usd": 1999,
        "tier": "flagship",
        "screen_in": 16.0,
        "weight_kg": 2.99,
        "weight_class": "heavy",
        "use_cases": ["gaming"],
        "highlights": ["Intel Core Ultra 9", "RTX 4080", "QHD+ 240Hz", "Cherry MX switches"],
        "specs": "Intel Core Ultra 9 185H, 32GB DDR5, 1TB SSD, NVIDIA RTX 4080, 16\" QHD+ 240Hz",
        "badge": "Premium Gaming",
        "url": "https://www.dell.com/en-us/shop/gaming-laptops/alienware-x16-r2-gaming-laptop/spd/alienware-x16-r2-laptop",
    },

    # ------------------------------------------------------------------ G-Series
    {
        "id": "g15-5530",
        "name": "Dell G15 5530",
        "family": "G-Series",
        "category": "laptop",
        "price_usd": 879,
        "tier": "mid",
        "screen_in": 15.6,
        "weight_kg": 2.81,
        "weight_class": "heavy",
        "use_cases": ["gaming", "student"],
        "highlights": ["Intel Core i7", "RTX 4060", "165Hz display", "budget gaming"],
        "specs": "Intel Core i7-13650HX, 16GB DDR5, 512GB SSD, NVIDIA RTX 4060, 15.6\" FHD 165Hz",
        "badge": "Budget Gaming Pick",
        "url": "https://www.dell.com/en-us/shop/gaming-laptops/g15-gaming-laptop/spd/g15-5530-gaming-laptop",
    },
    {
        "id": "g16-7630",
        "name": "Dell G16 7630",
        "family": "G-Series",
        "category": "laptop",
        "price_usd": 1149,
        "tier": "premium",
        "screen_in": 16.0,
        "weight_kg": 2.99,
        "weight_class": "heavy",
        "use_cases": ["gaming"],
        "highlights": ["Intel Core i7", "RTX 4070", "QHD+ 240Hz", "value flagship gaming"],
        "specs": "Intel Core i7-13650HX, 16GB DDR5, 512GB SSD, NVIDIA RTX 4070, 16\" QHD+ 240Hz",
        "badge": "Value Gaming Flagship",
        "url": "https://www.dell.com/en-us/shop/gaming-laptops/g16-gaming-laptop/spd/g16-7630-gaming-laptop",
    },

    # ------------------------------------------------------------ Latitude (business)
    {
        "id": "latitude-5540",
        "name": "Dell Latitude 5540",
        "family": "Latitude",
        "category": "laptop",
        "price_usd": 1149,
        "tier": "premium",
        "screen_in": 15.6,
        "weight_kg": 1.78,
        "weight_class": "standard",
        "use_cases": ["business"],
        "highlights": ["enterprise security", "Intel Core i5/i7", "Thunderbolt 4", "MIL-SPEC tested"],
        "specs": "Intel Core i5-1345U, 16GB DDR4, 256GB SSD, 15.6\" FHD, vPro optional",
        "badge": "Business Standard",
        "url": "https://www.dell.com/en-us/shop/dell-laptops/latitude-5540-laptop/spd/latitude-15-5540-laptop",
    },
    {
        "id": "latitude-7440",
        "name": "Dell Latitude 7440",
        "family": "Latitude",
        "category": "laptop",
        "price_usd": 1449,
        "tier": "premium",
        "screen_in": 14.0,
        "weight_kg": 1.27,
        "weight_class": "ultralight",
        "use_cases": ["business"],
        "highlights": ["ultra-thin business", "Intel Core i7 vPro", "ExpressSign-In", "AI features"],
        "specs": "Intel Core i7-1365U vPro, 16GB DDR5, 512GB SSD, 14\" FHD+",
        "badge": "Premium Business",
        "url": "https://www.dell.com/en-us/shop/dell-laptops/latitude-7440-laptop/spd/latitude-14-7440-laptop",
    },
    {
        "id": "latitude-9440",
        "name": "Dell Latitude 9440 2-in-1",
        "family": "Latitude",
        "category": "laptop",
        "price_usd": 1999,
        "tier": "flagship",
        "screen_in": 14.0,
        "weight_kg": 1.35,
        "weight_class": "ultralight",
        "use_cases": ["business"],
        "highlights": ["2-in-1 convertible", "Intel Core i7 vPro", "OLED touch", "AI PC"],
        "specs": "Intel Core i7-1365U vPro, 32GB LPDDR5, 1TB SSD, 14\" OLED touch 2-in-1",
        "badge": "Ultimate Business 2-in-1",
        "url": "https://www.dell.com/en-us/shop/dell-laptops/latitude-9440-2-in-1-laptop/spd/latitude-14-9440-2-in-1-laptop",
    },

    # ------------------------------------------------------------ Vostro
    {
        "id": "vostro-3520",
        "name": "Dell Vostro 3520",
        "family": "Vostro",
        "category": "laptop",
        "price_usd": 479,
        "tier": "budget",
        "screen_in": 15.6,
        "weight_kg": 1.74,
        "weight_class": "standard",
        "use_cases": ["business", "student", "everyday"],
        "highlights": ["small business", "Intel Core i3/i5", "affordable", "Windows 11 Pro"],
        "specs": "Intel Core i5-1235U, 8GB DDR4, 256GB SSD, 15.6\" FHD",
        "badge": "SMB Value",
        "url": "https://www.dell.com/en-us/shop/dell-laptops/vostro-15-3520-laptop/spd/vostro-15-3520-laptop",
    },

    # ------------------------------------------------------------ Precision (workstation)
    {
        "id": "precision-3580",
        "name": "Dell Precision 3580",
        "family": "Precision",
        "category": "laptop",
        "price_usd": 1549,
        "tier": "premium",
        "screen_in": 15.6,
        "weight_kg": 1.78,
        "weight_class": "standard",
        "use_cases": ["workstation", "business", "creator"],
        "highlights": ["ISV certified", "Intel Core i7", "NVIDIA RTX A500", "ECC memory"],
        "specs": "Intel Core i7-1370P, 16GB ECC DDR5, 512GB SSD, NVIDIA RTX A500, 15.6\" FHD",
        "badge": "Entry Workstation",
        "url": "https://www.dell.com/en-us/shop/workstations/precision-3580-mobile-workstation/spd/precision-15-3580-workstation",
    },
    {
        "id": "precision-5680",
        "name": "Dell Precision 5680",
        "family": "Precision",
        "category": "laptop",
        "price_usd": 2199,
        "tier": "flagship",
        "screen_in": 15.6,
        "weight_kg": 1.85,
        "weight_class": "standard",
        "use_cases": ["workstation", "creator"],
        "highlights": ["Intel Core i9", "NVIDIA RTX 5000 Ada", "OLED 3.5K", "professional GPU"],
        "specs": "Intel Core i9-13900H, 32GB DDR5, 1TB SSD, NVIDIA RTX 5000 Ada, 15.6\" OLED 3.5K",
        "badge": "Pro Workstation",
        "url": "https://www.dell.com/en-us/shop/workstations/precision-5680-mobile-workstation/spd/precision-15-5680-workstation",
    },

    # ------------------------------------------------------------ Monitors
    {
        "id": "u2723qe",
        "name": "Dell UltraSharp 27 4K USB-C Hub Monitor U2723QE",
        "family": "UltraSharp",
        "category": "monitor",
        "price_usd": 699,
        "tier": "premium",
        "screen_in": 27.0,
        "weight_kg": 6.32,
        "weight_class": "heavy",
        "use_cases": ["creator", "business", "workstation"],
        "highlights": ["4K IPS Black", "USB-C 90W", "hub built-in", "color accurate"],
        "specs": "27\" 4K IPS Black, USB-C 90W, HDMI, DP, 6x USB, 99% sRGB",
        "badge": "Best 4K Monitor",
        "url": "https://www.dell.com/en-us/shop/dell-monitors/ultrasharp-27-4k-usb-c-hub-monitor/apd/210-bdpg/monitors-monitor-accessories",
    },
    {
        "id": "s2722dc",
        "name": "Dell 27 USB-C Monitor S2722DC",
        "family": "Dell Monitor",
        "category": "monitor",
        "price_usd": 329,
        "tier": "mid",
        "screen_in": 27.0,
        "weight_kg": 5.56,
        "weight_class": "heavy",
        "use_cases": ["everyday", "business", "student"],
        "highlights": ["QHD", "USB-C 65W", "affordable productivity", "eye comfort"],
        "specs": "27\" QHD IPS, USB-C 65W, HDMI, DP, built-in speakers",
        "badge": "Best Value Monitor",
        "url": "https://www.dell.com/en-us/shop/dell-monitors/dell-27-usb-c-monitor/apd/210-bdsg/monitors-monitor-accessories",
    },

    # ------------------------------------------------------------ Accessories
    {
        "id": "wd19s",
        "name": "Dell WD19S 130W Docking Station",
        "family": "Docking Station",
        "category": "accessory",
        "price_usd": 199,
        "tier": "mid",
        "screen_in": 0,
        "weight_kg": 0.77,
        "weight_class": "light",
        "use_cases": ["business", "workstation", "everyday"],
        "highlights": ["USB-C dock", "130W power delivery", "dual display", "single cable setup"],
        "specs": "USB-C, 130W, Dual Display, 3x USB-A, 2x USB-C, HDMI, DP, Ethernet",
        "badge": "Best Dock",
        "url": "https://www.dell.com/en-us/shop/dell-docking-stations/wd19s-130w-docking-station/apd/210-azbi/pc-accessories",
    },
    {
        "id": "premier-wireless-km7321w",
        "name": "Dell Premier Wireless Keyboard and Mouse KM7321W",
        "family": "Peripherals",
        "category": "accessory",
        "price_usd": 129,
        "tier": "mid",
        "screen_in": 0,
        "weight_kg": 0.45,
        "weight_class": "ultralight",
        "use_cases": ["business", "everyday"],
        "highlights": ["wireless", "multi-device", "quiet keys", "rechargeable"],
        "specs": "Wireless 2.4GHz + Bluetooth, multi-device pairing, 36mo battery",
        "badge": "Productivity Set",
        "url": "https://www.dell.com/en-us/shop/dell-premier-wireless-keyboard-and-mouse-km7321w/apd/580-akfz/pc-accessories",
    },
]

# ---------------------------------------------------------------------------
# Index helpers
# ---------------------------------------------------------------------------
_BY_ID: dict[str, dict] = {p["id"]: p for p in CATALOG}
_BY_FAMILY: dict[str, list[dict]] = {}
for _p in CATALOG:
    _BY_FAMILY.setdefault(_p["family"], []).append(_p)


def get_by_id(product_id: str) -> dict | None:
    return _BY_ID.get(product_id)


def search_by_name(name: str) -> dict | None:
    """Fuzzy match a product name against the catalog."""
    name_lower = name.lower()
    # Exact family+number match
    for p in CATALOG:
        if p["name"].lower() == name_lower:
            return p
    # Partial match
    for p in CATALOG:
        if name_lower in p["name"].lower() or p["name"].lower() in name_lower:
            return p
    # Family keyword match
    for p in CATALOG:
        if p["family"].lower() in name_lower or any(h.lower() in name_lower for h in p["highlights"]):
            return p
    return None


def get_family(family: str) -> list[dict]:
    return _BY_FAMILY.get(family, [])


def all_laptops() -> list[dict]:
    return [p for p in CATALOG if p["category"] == "laptop"]


# ---------------------------------------------------------------------------
# Recommendation engine
# ---------------------------------------------------------------------------

def recommend(
    products_seen: list[str],
    intent_signals: dict,
    n: int = 3,
) -> list[dict]:
    """
    Return up to n catalog products the user has NOT seen, ranked by relevance.

    intent_signals keys (all optional):
      use_case      str  — gaming | creator | business | student | everyday | workstation
      tier          str  — budget | mid | premium | flagship
      screen_pref   int  — preferred screen size in inches
      weight_pref   str  — ultralight | light | standard (if portability matters)
      decision_stage str — browsing | exploring | evaluating | deciding
      family_seen   list[str] — families already viewed (to diversify)
    """
    seen_lower = {s.lower() for s in products_seen}

    # Exclude already-seen products (fuzzy match)
    def is_seen(p: dict) -> bool:
        pname = p["name"].lower()
        return any(
            s in pname or pname in s or p["id"].lower() in s
            for s in seen_lower
        )

    candidates = [p for p in CATALOG if not is_seen(p) and p["category"] == "laptop"]
    if not candidates:
        candidates = [p for p in CATALOG if p["category"] == "laptop"]

    use_case = intent_signals.get("use_case", "")
    tier = intent_signals.get("tier", "")
    screen_pref = intent_signals.get("screen_pref", 0)
    weight_pref = intent_signals.get("weight_pref", "")
    family_seen = {f.lower() for f in intent_signals.get("family_seen", [])}

    def score(p: dict) -> float:
        s = 0.0
        # Use case match is the strongest signal
        if use_case and use_case in p["use_cases"]:
            s += 4.0
        # Tier proximity
        tiers = ["budget", "mid", "premium", "flagship"]
        if tier and tier in tiers and p["tier"] in tiers:
            dist = abs(tiers.index(tier) - tiers.index(p["tier"]))
            s += max(0, 2.0 - dist * 0.8)
        # Screen size proximity (within 1.5 inches)
        if screen_pref and p["screen_in"]:
            diff = abs(p["screen_in"] - screen_pref)
            s += max(0, 2.0 - diff * 0.5)
        # Weight preference
        if weight_pref and p["weight_class"] == weight_pref:
            s += 1.5
        # Diversity: prefer families not yet seen
        if p["family"].lower() not in family_seen:
            s += 1.0
        # Slight boost for higher-tier products (aspirational)
        tier_boost = {"budget": 0, "mid": 0.1, "premium": 0.2, "flagship": 0.1}
        s += tier_boost.get(p["tier"], 0)
        return s

    ranked = sorted(candidates, key=score, reverse=True)
    return ranked[:n]


def extract_intent_signals(insight_dict: dict, products_seen: list[str]) -> dict:
    """
    Convert a SessionInsight dict into intent_signals for the recommender.
    """
    intent = (insight_dict.get("intent") or "").lower()
    stage = insight_dict.get("decision_stage", "browsing")
    friction = (insight_dict.get("friction_point") or "").lower()

    # Infer use_case from intent text
    use_case = ""
    if any(w in intent for w in ["gam", "fps", "rtx", "alienware", "g15", "g16"]):
        use_case = "gaming"
    elif any(w in intent for w in ["creat", "video", "photo", "design", "oled", "color"]):
        use_case = "creator"
    elif any(w in intent for w in ["business", "enterprise", "work", "office", "latitude"]):
        use_case = "business"
    elif any(w in intent for w in ["student", "school", "college", "affordable", "budget"]):
        use_case = "student"
    elif any(w in intent for w in ["workstation", "precision", "cad", "3d", "render"]):
        use_case = "workstation"
    else:
        use_case = "everyday"

    # Infer tier from seen products
    tier = "mid"
    if products_seen:
        matched = [search_by_name(p) for p in products_seen]
        matched = [p for p in matched if p]
        if matched:
            tiers = [p["tier"] for p in matched]
            # Use the most common tier seen
            tier = max(set(tiers), key=tiers.count)

    # Screen pref from seen products
    screen_pref = 0.0
    if products_seen:
        matched = [search_by_name(p) for p in products_seen]
        screens = [p["screen_in"] for p in matched if p and p["screen_in"]]
        if screens:
            screen_pref = sum(screens) / len(screens)

    # Family seen
    family_seen = []
    for p in products_seen:
        m = search_by_name(p)
        if m:
            family_seen.append(m["family"])

    # Weight pref: if portability keywords in intent
    weight_pref = ""
    if any(w in intent for w in ["light", "portable", "thin", "slim", "compact"]):
        weight_pref = "ultralight"

    return {
        "use_case": use_case,
        "tier": tier,
        "screen_pref": screen_pref,
        "weight_pref": weight_pref,
        "decision_stage": stage,
        "family_seen": family_seen,
    }
