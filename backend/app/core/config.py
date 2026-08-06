"""
app/core/config.py

Centralised configuration management using Pydantic BaseSettings.

Architecture:
    - Reads all secrets and config from environment variables.
    - Validated on application startup - fails fast if a required var is missing.
    - Injected into services via dependency injection (not imported globally).

Engineering Principles:
    - Single Responsibility: This module ONLY manages configuration.
    - Never hardcode secrets.
    - KISS: One source of truth for all env vars.
"""

from functools import lru_cache
from pydantic import PostgresDsn, computed_field, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application-wide settings loaded from environment variables.
    All fields are type-validated by Pydantic on startup.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────
    APP_NAME: str = "TripMate"
    APP_VERSION: str = "2.0.0"
    APP_ENV: str = "development"  # development | staging | production
    DEBUG: bool = False

    # ── Database (PostgreSQL) ──────────────────────────────
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "tripmate_user"
    POSTGRES_PASSWORD: str = "tripmate_password"
    POSTGRES_DB: str = "tripmate_db"

    @computed_field  # type: ignore[misc]
    @property
    def DATABASE_URL(self) -> str:
        """Async PostgreSQL connection string for SQLAlchemy + psycopg."""
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ── Redis ─────────────────────────────────────────────
    ML_SERVICE_URL: str = Field(default="http://localhost:8001")
    
    # Observability
    SENTRY_DSN: str | None = None
    LOGFIRE_TOKEN: str | None = None
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Security (JWT) ─────────────────────────────────────
    SECRET_KEY: str  # REQUIRED — must be set in .env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── CORS ──────────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # ── External APIs ─────────────────────────────────────
    OPENAI_API_KEY: str  # REQUIRED
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    OPEN_METEO_API_URL: str = "https://api.open-meteo.com/v1/forecast"
    EXCHANGE_RATE_API_URL: str = "https://api.exchangerate-api.com/v4/latest"

    # ── Storage (Cloudinary) ───────────────────────────────
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # ── Monitoring ────────────────────────────────────────
    SENTRY_DSN: str = ""
    LOGFIRE_TOKEN: str = ""

    # ── Rate Limiting ─────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60
    AI_RATE_LIMIT_PER_MINUTE: int = 10


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached singleton instance of Settings.
    Use `Depends(get_settings)` in FastAPI endpoints for dependency injection.

    The @lru_cache ensures the .env file is read only once per process,
    improving performance significantly.
    """
    return Settings()
