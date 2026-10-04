from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.discovery_client import create_discovery_client
from app.embedding_model import smoke_test
from app.routers import clickstream, stream
from app.session_store import create_store

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    store = create_store()
    app.state.store = store
    app.state.discovery = create_discovery_client()

    ok = await smoke_test()
    if ok:
        logger.info("Embedding smoke test passed (%d dims)", settings.embedding_dims)
    else:
        logger.warning("Embedding smoke test FAILED — check GENAI_API_URL / embedding model")

    logger.info("Store backend: %s", settings.store_backend)
    logger.info("Discovery mode: %s", settings.discovery_mode)

    yield

    # Shutdown
    await store.close()


app = FastAPI(
    title="Live Stream Signals",
    description="Real-time behavioral signal intelligence for dell.com",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(clickstream.router)
app.include_router(stream.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
