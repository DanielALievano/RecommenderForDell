from __future__ import annotations

import re
from typing import Optional

from app.models import NarrativeSignal, ParsedNarrative

# ---------------------------------------------------------------------------
# Header regex: [10s] [T1 0.85] REST_OF_LINE
# ---------------------------------------------------------------------------
_HEADER = re.compile(
    r"^\[(\d+)s\]\s+\[T(\d)\s+([\d.]+)\]\s+(.+)$",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Body regexes per event type (order matters for ambiguous patterns)
# ---------------------------------------------------------------------------
_BODY_PATTERNS: list[tuple[str, re.Pattern]] = [
    # Dwell: DWELL Xs on "content" (ctx)
    ("dwell",          re.compile(r'DWELL\s+([\d.]+)s\s+on\s+"([^"]*)"(?:\s+\(([^)]*)\))?', re.I)),
    # Viewport dwell: VIEWPORT DWELL Xs on "content" (ctx)
    ("viewport_dwell", re.compile(r'VIEWPORT\s+DWELL\s+([\d.]+)s\s+on\s+"([^"]*)"(?:\s+\(([^)]*)\))?', re.I)),
    # Touch hold: TOUCH HOLD Xs on "content" (ctx)
    ("touch_hold",     re.compile(r'TOUCH\s+HOLD\s+([\d.]+)s\s+on\s+"([^"]*)"(?:\s+\(([^)]*)\))?', re.I)),
    # Multi-pass: MULTI-PASS #N on "content" — note
    ("multi_pass",     re.compile(r'MULTI-PASS\s+#(\d+)\s+on\s+"([^"]*)"', re.I)),
    # Search: SEARCH "query"
    ("search_query",   re.compile(r'SEARCH\s+"([^"]*)"', re.I)),
    # Text copy: COPY "content"
    ("text_copy",      re.compile(r'(?:TEXT\s+)?COPY\s+"([^"]*)"', re.I)),
    # Config change: CONFIG CHANGE "key" -> "value" (ctx)
    ("config_change",  re.compile(r'CONFIG\s+CHANGE\s+"([^"]*)"(?:\s*->\s*"([^"]*)")?(?:\s+\(([^)]*)\))?', re.I)),
    # Filter applied: FILTER APPLIED "value" (key)
    ("filter_applied", re.compile(r'FILTER\s+APPLIED\s+"([^"]*)"(?:\s+\(([^)]*)\))?', re.I)),
    # Filter removed: FILTER REMOVED "value"
    ("filter_removed", re.compile(r'FILTER\s+REMOVED\s+"([^"]*)"', re.I)),
    # Compare add: COMPARE ADD "product"
    ("compare_add",    re.compile(r'COMPARE\s+ADD\s+"([^"]*)"', re.I)),
    # Text select: SELECT "content" (ctx)
    ("text_select",    re.compile(r'(?:TEXT\s+)?SELECT\s+"([^"]*)"(?:\s+\(([^)]*)\))?', re.I)),
    # Input change: INPUT "field" -> "value" (ctx)
    ("input_change",   re.compile(r'INPUT\s+"([^"]*)"(?:\s*->\s*"([^"]*)")?(?:\s+\(([^)]*)\))?', re.I)),
    # Rage click: RAGE CLICK on "content" (ctx)
    ("rage_click",     re.compile(r'RAGE\s+CLICK(?:\s+on\s+"([^"]*)")?(?:\s+\(([^)]*)\))?', re.I)),
    # Dead click: DEAD CLICK on "content" (ctx)
    ("dead_click",     re.compile(r'DEAD\s+CLICK(?:\s+on\s+"([^"]*)")?(?:\s+\(([^)]*)\))?', re.I)),
    # Cursor thrash: CURSOR THRASH — note
    ("cursor_thrash",  re.compile(r'CURSOR\s+THRASH', re.I)),
    # Idle start: IDLE START — note (active: Xs)
    ("idle_start",     re.compile(r'IDLE\s+START', re.I)),
    # Tab hidden / visible
    ("tab_hidden",     re.compile(r'TAB\s+HIDDEN', re.I)),
    ("tab_visible",    re.compile(r'TAB\s+VISIBLE', re.I)),
    # Scroll depth: SCROLL DEPTH X%
    ("scroll_depth",   re.compile(r'SCROLL\s+DEPTH\s+([\d.]+)%?', re.I)),
    # Scroll mode: SCROLL MODE "mode"
    ("scroll_mode",    re.compile(r'SCROLL\s+MODE\s+"([^"]*)"', re.I)),
    # Page change: PAGE CHANGE "url"
    ("page_change",    re.compile(r'PAGE\s+CHANGE\s+"([^"]*)"', re.I)),
    # Results updated: RESULTS UPDATED N items
    ("results_updated",re.compile(r'RESULTS\s+UPDATED\s+(\d+)\s+items?', re.I)),
    # Tab change: TAB CHANGE "label"
    ("tab_change",     re.compile(r'TAB\s+CHANGE\s+"([^"]*)"', re.I)),
    # Page exit: PAGE EXIT
    ("page_exit",      re.compile(r'PAGE\s+EXIT', re.I)),
    # Generic click: CLICK "content" (ctx)
    ("click",          re.compile(r'CLICK\s+"([^"]*)"(?:\s+\(([^)]*)\))?', re.I)),
]

# Context-type noise buckets (used by noise filter)
_NOISE_CONTEXTS = {"navigation", "pagination", "breadcrumb", "menu", "header", "footer"}

# Text-level noise patterns
_NOISE_TEXT = re.compile(
    r'^(skip to (main|content)|sign in)',
    re.I,
)


def _parse_body(event_type_hint: str, body: str) -> tuple[str, str, str, float]:
    """Return (event_type, content_text, context_type, dwell_seconds)."""
    for event_type, pat in _BODY_PATTERNS:
        m = pat.search(body)
        if m:
            g = m.groups()
            content = ""
            context = ""
            dwell = 0.0
            if event_type in ("dwell", "viewport_dwell", "touch_hold"):
                dwell = float(g[0]) if g[0] else 0.0
                content = g[1] or ""
                context = g[2] or ""
            elif event_type == "multi_pass":
                content = g[1] or ""
            elif event_type in ("search_query", "text_copy", "filter_removed", "compare_add",
                                "page_change", "scroll_mode", "tab_change", "page_exit"):
                content = g[0] or ""
            elif event_type == "config_change":
                content = g[0] or ""
                context = g[2] or ""
            elif event_type == "filter_applied":
                content = g[0] or ""
                context = g[1] or ""
            elif event_type in ("text_select", "input_change"):
                content = g[0] or ""
                context = g[2] if len(g) > 2 and g[2] else (g[1] or "")
            elif event_type in ("rage_click", "dead_click", "click"):
                content = g[0] or ""
                context = g[1] or "" if len(g) > 1 else ""
            elif event_type == "scroll_depth":
                content = f"{g[0]}%" if g[0] else ""
            elif event_type == "results_updated":
                content = f"{g[0]} items" if g[0] else ""
            return event_type, content.strip(), context.strip().lower(), dwell
    # Fallback: unknown
    return "unknown", "", "", 0.0


def is_vector_contributor(sig: NarrativeSignal) -> bool:
    """Structural noise filter — returns True if this signal should build the vector."""
    if sig.context_type in _NOISE_CONTEXTS:
        return False
    if sig.tier == 3 and sig.confidence < 0.40:
        return False
    if not sig.content_text or _NOISE_TEXT.match(sig.content_text):
        return False
    # Frustration / thrash / scroll events never contribute
    if sig.event_type in ("rage_click", "dead_click", "cursor_thrash",
                          "scroll_depth", "scroll_mode", "tab_hidden",
                          "tab_visible", "idle_start", "page_exit"):
        return False
    return True


def parse_narrative(text: str) -> ParsedNarrative:
    result = ParsedNarrative()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        hm = _HEADER.match(line)
        if not hm:
            continue
        ts_s = int(hm.group(1))
        tier = int(hm.group(2))
        conf = float(hm.group(3))
        body = hm.group(4).strip()

        event_type, content, context, dwell = _parse_body(body, body)
        if event_type == "unknown":
            continue

        sig = NarrativeSignal(
            timestamp_s=ts_s,
            tier=tier,
            confidence=conf,
            event_type=event_type,
            content_text=content,
            context_type=context,
            dwell_seconds=dwell,
            is_high_interest=(tier == 1 and conf >= 0.75),
        )
        result.signals.append(sig)

        # Aggregate counters
        if event_type == "cursor_thrash":
            result.thrash_count += 1
        if event_type in ("rage_click", "dead_click"):
            result.frustration_count += 1
        if event_type == "idle_start":
            result.idle_detected = True
        if event_type == "scroll_depth":
            try:
                depth = float(content.rstrip("%"))
                result.max_scroll_depth = max(result.max_scroll_depth, depth)
            except ValueError:
                pass
        if event_type == "search_query" and content:
            result.search_queries.append(content)
        if event_type == "text_copy" and content:
            result.copied_texts.append(content)
        if event_type == "filter_applied" and content:
            result.applied_filters[context or content] = content

        if is_vector_contributor(sig):
            result.vector_signals.append(sig)

    return result
