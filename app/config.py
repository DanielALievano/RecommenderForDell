from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Store
    store_backend: str = "memory"          # memory | redis
    session_ttl_seconds: int = 1800        # 30 min

    # Redis (only used when store_backend=redis)
    redis_url: str = "redis://localhost:6379/0"
    redis_tls: bool = False

    # GenAI / LLM
    genai_api_url: str = "http://localhost:11434/v1"
    opensource_llm_key: str = "placeholder"
    genai_llm_model: str = "llama3"
    embedding_model: str = "embeddinggemma-300m"
    embedding_dims: int = 768

    # Pipeline
    vector_ema_alpha: float = 0.30         # chunk weight
    cosine_delta_threshold: float = 0.20
    recent_raw_chunks: int = 5
    push_min_confidence: float = 0.70

    # Discovery
    discovery_mode: str = "mock"           # mock | live
    discovery_api_url: str = ""
    discovery_api_key: str = ""

    # App
    cors_origins: list[str] = ["*"]
    log_level: str = "INFO"


settings = Settings()
