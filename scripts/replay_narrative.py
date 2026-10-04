#!/usr/bin/env python3
"""
POST a sample session to the ingest endpoint for demo purposes.

Usage:
    python scripts/replay_narrative.py [--url http://localhost:8000] [--session-id mysession]
"""
from __future__ import annotations

import argparse
import json
import time
import uuid

import httpx

SAMPLE_NARRATIVE = """\
[10s] [T1 0.85] DWELL 8s on "Spring Sale Savings Up to $650 Off" (promo_banner)
[2s] [T2 0.7] CURSOR THRASH — hesitation/confusion
[44s] [T2 0.75] MULTI-PASS #2 on "DELL 14 PLUS LAPTOP" — HIGH INTEREST
[36s] [T3 0.5] CLICK "Next slide" (pagination)
[15s] [T1 0.80] SELECT "13th Gen Intel Core i5-1334U"
[90s] [T2 0.75] IDLE START — thinking pause (active: 84s)
[5s] [T1 0.90] SEARCH "dell xps 15 i7"
[20s] [T2 0.60] FILTER APPLIED "16GB RAM" (memory)
[8s] [T1 0.88] COMPARE ADD "Dell XPS 15"
[12s] [T3 0.35] SCROLL DEPTH 45%
[3s] [T2 0.55] RAGE CLICK on "Add to Cart" (checkout)
[25s] [T1 0.92] DWELL 12s on "Dell XPS 15 9530" (product_card)
[18s] [T2 0.70] MULTI-PASS #3 on "Dell XPS 15 9530" — HIGH INTEREST
[6s] [T1 0.87] COMPARE ADD "Dell Inspiron 16 Plus"
"""

CHUNKS = [
    # Chunk 1: initial browsing
    {
        "trigger": "idle_start",
        "active_seconds": 45,
        "total_events": 4,
        "narrative": "\n".join(SAMPLE_NARRATIVE.splitlines()[:4]),
    },
    # Chunk 2: spec selection
    {
        "trigger": "T1_event",
        "active_seconds": 70,
        "total_events": 7,
        "narrative": "\n".join(SAMPLE_NARRATIVE.splitlines()[4:8]),
    },
    # Chunk 3: compare flow
    {
        "trigger": "compare_add",
        "active_seconds": 120,
        "total_events": 11,
        "narrative": "\n".join(SAMPLE_NARRATIVE.splitlines()[8:]),
    },
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--session-id", default=f"replay_{uuid.uuid4().hex[:8]}")
    parser.add_argument("--delay", type=float, default=0.5, help="Seconds between chunks")
    args = parser.parse_args()

    base = args.url.rstrip("/")
    session_id = args.session_id
    print(f"Replaying session: {session_id}")
    print(f"Endpoint: {base}/api/clickstream/ingest\n")

    with httpx.Client(timeout=10.0) as client:
        for i, chunk in enumerate(CHUNKS, 1):
            payload = {
                "session_id": session_id,
                "visit_number": 1,
                "page_url": "https://www.dell.com/en-us/shop/dell-laptops/sc/laptops",
                "page_title": "Dell Laptops | Dell USA",
                "referrer": "https://www.google.com/",
                **chunk,
            }
            print(f"--- Chunk {i}/{len(CHUNKS)} (trigger={chunk['trigger']}) ---")
            resp = client.post(f"{base}/api/clickstream/ingest", json=payload)
            print(f"  Status: {resp.status_code}")
            print(f"  Response: {json.dumps(resp.json(), indent=2)}")
            if i < len(CHUNKS):
                time.sleep(args.delay)

    print(f"\nDone. Inspect state with:")
    print(f"  python scripts/inspect_state.py --session-id {session_id}")


if __name__ == "__main__":
    main()
