# Live Stream Signals

Real-time behavioral signal intelligence service for dell.com.

Ingests browser interaction narratives, filters noise, builds a weighted intent vector, detects intent shifts, calls an LLM to update its understanding of the session, and pushes a single proactive nudge to the browser via SSE.

---

## Quick start (zero external dependencies)

```bash
# 1. Clone and enter the repo
git clone git@github.com:DanielALievano/RecommenderForDell.git
cd RecommenderForDell

# 2. Create a virtualenv and install
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Copy env template (no real secrets needed for local demo)
cp .env.example .env

# 4. Run
uvicorn app.main:app --reload --port 8000
```

- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/health

The server starts with **in-memory store + stub embeddings + mock discovery** — no network calls required.

---

## Environment variables

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

## Run tests

```bash
pytest -v
```

Tests cover: parser, noise filter, vector math (EMA, cosine delta), push gating.

---

## Demo replay (no browser needed)

```bash
# Terminal 1: start server
uvicorn app.main:app --reload --port 8000

# Terminal 2: replay sample session
python scripts/replay_narrative.py

# Optional: custom session id
python scripts/replay_narrative.py --session-id demo123
```

---

## Inject on dell.com (DevTools snippet)

1. Open dell.com in Chrome/Edge
2. Open DevTools → Sources → Snippets → New snippet
3. Paste the contents of `clickstream.js`
4. Edit `API_BASE` at the top to point at your running server (or use ngrok for HTTPS)
5. Run snippet — you'll see `[LiveStreamSignals] Tracker active` in the console
6. The nudge strip will appear at the top of the page when an intent shift is detected

For production injection, add as a `<script>` tag or load via Tag Manager.

---

## Swapping mock → live Discovery agent

```env
# .env
DISCOVERY_MODE=live
DISCOVERY_API_URL=https://your-discovery-endpoint
DISCOVERY_API_KEY=your-key
```

The `LiveDiscoveryClient` in `app/discovery_client.py` expects a POST `/recommend` endpoint.
Implement the `DiscoveryClient` interface to add custom behavior.

---

## Swapping memory → Redis

```env
# .env
STORE_BACKEND=redis
REDIS_URL=rediss://your-redis-host:6380/0   # rediss:// for TLS
REDIS_TLS=true
```

Install the Redis client:
```bash
pip install "redis[hiredis]"
```

---

## Architecture

```
Browser (clickstream.js)
    │  POST /api/clickstream/ingest
    ▼
FastAPI (app/main.py)
    │
    ├─ narrative_parser.py  → ParsedNarrative (signals, vector_signals, counters)
    ├─ vector_builder.py    → weighted batch embed → chunk vector
    ├─ vector_math.py       → EMA update → cosine delta → should_act()
    │
    └─ BackgroundTask (when acted=True)
        ├─ llm_inference.py  → SessionInsight
        ├─ discovery_client.py → display payload
        └─ sse.py            → push nudge to browser

Browser ← GET /api/session/stream/{session_id} (SSE)
    └─ renders dismissible nudge strip (shadow DOM)
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
  discovery_client.py   DiscoveryClient interface + Mock + Live
  sse.py                Connection registry + push helper
  routers/
    clickstream.py      POST /api/clickstream/ingest
    stream.py           GET /api/session/stream/{session_id}
clickstream.js          Browser tracker + actuator
scripts/
  replay_narrative.py   Demo replay without a browser
  inspect_state.py      Dump session state
tests/
  test_parser.py
  test_vector_math.py
  test_push_gate.py
```
