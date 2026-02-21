"""Application configuration layer.

This module reads runtime configuration from environment variables and exposes
one cached Settings object for the rest of the app.
"""

import os
from dataclasses import dataclass
from functools import lru_cache


def _require_env(name: str) -> str:
    """Read a required environment variable and fail fast if missing."""
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _normalize_database_url(url: str) -> str:
    """Ensure SQLAlchemy async engine always receives an asyncpg URL."""
    normalized = url.strip()
    if normalized.startswith("postgres://"):
        normalized = "postgresql://" + normalized[len("postgres://") :]
    if normalized.startswith("postgresql://"):
        normalized = "postgresql+asyncpg://" + normalized[len("postgresql://") :]
    return normalized


@dataclass(frozen=True)
class Settings:
    """Typed runtime settings used by backend modules."""

    database_url: str
    aes_key: str
    hmac_key: str
    app_secret: str
    session_ttl_hours: int
    cors_origins: list[str]
    bloom_filter_size: int
    bloom_filter_hash_count: int


@lru_cache
def get_settings() -> Settings:
    """Build and cache settings once per process."""
    raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    return Settings(
        database_url=_normalize_database_url(_require_env("DATABASE_URL")),
        aes_key=_require_env("AES_KEY"),
        hmac_key=_require_env("HMAC_KEY"),
        app_secret=_require_env("APP_SECRET"),
        session_ttl_hours=int(os.getenv("SESSION_TTL_HOURS", "168")),
        cors_origins=origins,
        bloom_filter_size=int(os.getenv("BLOOM_FILTER_SIZE", "50000")),
        bloom_filter_hash_count=int(os.getenv("BLOOM_FILTER_HASH_COUNT", "7")),
    )
