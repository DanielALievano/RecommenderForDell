# Live Stream Signals

Real-time behavioral signal intelligence for dell.com. Captures browser interactions, builds a weighted intent vector, detects intent shifts, and pushes proactive product recommendations the user hasn't seen yet — via a dismissible strip at the top of the page.

---

## How to run (full demo in 5 steps)

### Prerequisites
- Python 3.11+
- Chrome or Edge browser
- Tampermonkey extension (free, from Chrome Web Store)

---

### Step 1 — Clone and install

Open a terminal (PowerShell or Command Prompt on Windows):

```bash
git clone git@github.com:DanielALievano/RecommenderForDell.git
cd RecommenderForDell
```

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux
```

```bash
pip install -r requirements.txt
cp .env.example .env
```

---

### Step 2 — Start the backend

```bash
uvicorn app.main:app --reload --port 8000
```

Leave this terminal open. You should see:

```
INFO:     Application startup complete.
INFO:     Embedding smoke test passed (768 dims)
INFO:     Store backend: memory
INFO:     Discovery mode: mock
```

Verify it works: open http://localhost:8000/health in your browser — should return `{"status":"ok"}`.
Full API docs at http://localhost:8000/docs.

---

### Step 3 — Allow mixed content on dell.com (one-time)

The backend runs on HTTP, dell.com is HTTPS. You need to allow this once:

1. Go to **dell.com** in Chrome
2. Click the **lock icon** in the address bar
3. Click **Site settings**
4. Find **Insecure content** → set to **Allow**
5. Refresh dell.com

---

### Step 4 — Install the Tampermonkey userscript

This makes the tracker auto-run on every dell.com page without manual injection.

1. Install **Tampermonkey** from the Chrome Web Store (free)
2. Click the Tampermonkey icon in the toolbar → **Create a new script**
3. Delete everything in the editor
4. Open `userscript.js` from this repo (in Notepad or VS Code), select all, copy
5. Paste into the Tampermonkey editor → **File → Save** (`Ctrl+S`)
6. Refresh dell.com

You should see a dark floating panel in the bottom-right corner of the page.

---

### Step 5 — Browse and watch it work

Navigate around dell.com — laptops, product pages, spec pages. The panel shows:

- **Gold lines** = high-intent signals (T1): searches, text selection, copy, compare
- **Blue lines** = behavioral signals (T2): clicks, dwells, multi-pass hovers
- **Gray lines** = weak signals (T3): scrolls, tab changes
- **Green lines** = system events: flushes, backend ACKs, intent shift detected

After enough browsing (or hit **Flush now** to force it), a **blue recommendation strip** appears at the top of the page with products you haven't seen yet, chosen based on your browsing signals.

**Console helpers** (open DevTools → Console):
```js
_lssFlush()      // force send all buffered events now
_lssProducts()   // list all products the tracker has seen this session
_lssSession()    // your session id
```

---

## How recommendations work

The system tracks which products you've already seen and **excludes them** from recommendations. It infers your intent (gaming / creator / business / student / everyday) from your behavioral signals and matches you against a catalog of 25 Dell products you haven't visited yet.

Example: if you've been on the XPS 15 and Inspiron 16 pages, the nudge might say:
> *"For your creative work — you haven't seen the XPS 16 or Precision 5680 yet. Worth a look."*

---

## Run tests

```bash
pytest -v
```

36 tests covering: narrative parser, noise filter, vector math (EMA, cosine delta), push gating.

---

## Demo replay (no browser needed)

Test the full backend pipeline without opening a browser:

```bash
# Terminal 1 — backend must be running
uvicorn app.main:app --reload --port 8000

# Terminal 2 — replay a sample session
python scripts/replay_narrative.py

# Inspect what was stored
python scripts/replay_narrative.py --session-id demo123
python scripts/inspect_state.py --session-id demo123
```

---

## Environment variables

Copy `.env.example` to `.env`. All defaults work offline with no real API keys.

| Variable | Default | Description |
|---|---|---|
| `STORE_BACKEND` | `memory` | `memory` or `redis` |
| `SESSION_TTL_SECONDS` | `1800` | Session TTL (30 min) |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL |
| `REDIS_TLS` | `false` | Enable TLS for Redis |
| `GENAI_API_URL` | `http://localhost:11434/v1` | OpenAI-compatible LLM endpoint |
| `OPENSOURCE_LLM_KEY` | `placeholder` | API key for LLM endpoint |
| `GENAI_LLM_MODEL` | `llama3` | LLM model name |
| `EMBEDDING_MODEL` | `embeddinggemma-300m` | Embedding model name |
| `EMBEDDING_DIMS` | `768` | Embedding dimensions |
| `VECTOR_EMA_ALPHA` | `0.30` | Chunk weight in EMA update |
| `COSINE_DELTA_THRESHOLD` | `0.20` | Minimum delta to trigger inference |
| `PUSH_MIN_CONFIDENCE` | `0.70` | Minimum confidence to push nudge |
| `DISCOVERY_MODE` | `mock` | `mock` or `live` |
| `DISCOVERY_API_URL` | _(empty)_ | Live discovery endpoint |
| `DISCOVERY_API_KEY` | _(empty)_ | Live discovery API key |

Never commit real secrets. `.env` is gitignored.

---

## Swap mock → live Discovery agent

```env
DISCOVERY_MODE=live
DISCOVERY_API_URL=https://your-discovery-endpoint
DISCOVERY_API_KEY=your-key
```

The `LiveDiscoveryClient` in `app/discovery_client.py` POSTs to `/recommend` with `{intent, products_of_interest, decision_stage}`.

---

## Swap memory → Redis

```env
STORE_BACKEND=redis
REDIS_URL=rediss://your-redis-host:6380/0
REDIS_TLS=true
```

```bash
pip install "redis[hiredis]"
```

---

## Swap stub → real LLM + embeddings

```env
GENAI_API_URL=https://your-openai-compatible-endpoint/v1
OPENSOURCE_LLM_KEY=your-key
GENAI_LLM_MODEL=your-model
```

The system auto-detects that the URL is not localhost and switches from stub to live calls. Embeddings and LLM inference both use the same endpoint.

---

## Architecture

```
Browser (userscript.js — Tampermonkey, auto-runs on dell.com)
    │  captures clicks / dwells / search / scroll / hovers
    │  scans DOM for product names on each page
    │  POST /api/clickstream/ingest  (every 15s or on T1 event)
    ▼
FastAPI  app/main.py
    │
    ├─ narrative_parser.py    parse lines → typed signals + noise filter
    ├─ vector_builder.py      batch embed signals → weighted chunk vector
    ├─ vector_math.py         EMA update → cosine delta → should_act()
    │  → 202 returned immediately (target <50ms)
    │
    └─ BackgroundTask (when delta >= threshold)
        ├─ llm_inference.py     extract products + build SessionInsight
        ├─ catalog.py           score unseen products against intent signals
        ├─ discovery_client.py  build display payload from catalog recs
        └─ sse.py               push nudge to browser

Browser ← GET /api/session/stream/{session_id}  (SSE, keepalive 15s)
    └─ renders dismissible recommendation strip (shadow DOM, non-blocking)
```

## Project layout

```
app/
  main.py               FastAPI app, lifespan
  config.py             pydantic-settings, reads .env
  models.py             Pydantic models
  session_store.py      SessionStore interface + InMemoryStore + RedisStore
  narrative_parser.py   Line parser + noise filter
  embedding_model.py    Stub + live OpenAI-compatible embeddings
  vector_builder.py     Weighted batch embed → chunk vector
  vector_math.py        EMA, cosine distance, should_act()
  llm_inference.py      Prompt builder + LLM call + JSON parsing
  catalog.py            25-product Dell catalog + recommendation engine
  discovery_client.py   DiscoveryClient interface + CatalogMock + Live
  sse.py                Connection registry + push helper
  routers/
    clickstream.py      POST /api/clickstream/ingest
    stream.py           GET /api/session/stream/{session_id}
userscript.js           Tampermonkey auto-inject tracker (recommended)
clickstream.js          Manual DevTools snippet version
demo.js                 Debug version with floating panel (DevTools)
scripts/
  replay_narrative.py   Demo replay without a browser
  inspect_state.py      Dump session state
tests/
  test_parser.py
  test_vector_math.py
  test_push_gate.py
```
