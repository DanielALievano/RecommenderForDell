#!/usr/bin/env python3
"""
Dump meta, chunks, vector head, and insight for a session id.
Runs against the in-memory store directly (starts a temporary app instance).

Usage:
    python scripts/inspect_state.py --session-id <id>
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys


async def _dump(session_id: str):
    from app.session_store import create_store

    store = create_store()
    print(f"\n=== Session: {session_id} ===\n")

    # Meta
    meta = await store.hget_all(session_id, "meta")
    print("--- META ---")
    print(json.dumps(meta, indent=2) if meta else "  (none)")

    # Narrative chunks
    chunks = await store.list_get_all(session_id, "narrative")
    print(f"\n--- NARRATIVE CHUNKS ({len(chunks)}) ---")
    for i, c in enumerate(chunks, 1):
        ts = c.get("ts", "?") if isinstance(c, dict) else "?"
        trigger = c.get("trigger", "?") if isinstance(c, dict) else "?"
        text_preview = (c.get("text", "") if isinstance(c, dict) else str(c))[:120].replace("\n", " | ")
        print(f"  [{i}] {ts}  trigger={trigger}")
        print(f"       {text_preview}")

    # Vector
    vec = await store.get_json(session_id, "vector")
    if vec is not None:
        head = vec[:8]
        print(f"\n--- VECTOR (first 8 of {len(vec)} dims) ---")
        print(f"  {[round(x, 4) for x in head]}")
    else:
        print("\n--- VECTOR ---")
        print("  (none)")

    # Insight
    insight = await store.get_json(session_id, "insight")
    print("\n--- INSIGHT ---")
    if insight:
        # Don't print the full baseline vector
        display = {k: v for k, v in insight.items() if k != "vector_baseline"}
        if "vector_baseline" in insight and insight["vector_baseline"]:
            display["vector_baseline"] = f"[{len(insight['vector_baseline'])} floats]"
        print(json.dumps(display, indent=2))
    else:
        print("  (none)")

    await store.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-id", required=True)
    args = parser.parse_args()

    print("NOTE: This script reads from an in-memory store — it will show empty state")
    print("unless called within the same process. For Redis, point STORE_BACKEND=redis.")

    asyncio.run(_dump(args.session_id))


if __name__ == "__main__":
    main()
