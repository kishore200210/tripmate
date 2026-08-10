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
from pydantic import PostgresDsn, computed_field, Field, model_validator
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

    DATABASE_URL: str | None = None

    # ── Redis ─────────────────────────────────────────────
    ML_SERVICE_URL: str = Field(default="http://localhost:8001")
    
    # ── Machine Learning ──────────────────────────────────
    ENABLE_ML_MODELS: bool = True
    
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
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
        "http://127.0.0.1:3003",
    ]

    # ── External APIs ─────────────────────────────────────
    GROQ_API_KEY: str  # REQUIRED — set in .env
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    OPENAI_API_KEY: str | None = None  # Optional (only needed for RAG embeddings)
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

    @model_validator(mode="after")
    def assemble_db_connection(self) -> "Settings":
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        # Convert standard Postgres URLs to async driver (required for Render)
        if self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
        elif self.DATABASE_URL.startswith("postgresql://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
        return self

    @model_validator(mode="after")
    def validate_production_secret(self) -> "Settings":
        if self.APP_ENV == "production":
            placeholders = [
                "change_this",
                "your-super-secret-key",
                "dummy-key",
                "test",
            ]
            key_lower = self.SECRET_KEY.lower()
            if any(p in key_lower for p in placeholders) or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "SECRET_KEY must be a cryptographically secure random string "
                    "of at least 32 characters in production environments."
                )
        return self


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached singleton instance of Settings.
    Use `Depends(get_settings)` in FastAPI endpoints for dependency injection.

    The @lru_cache ensures the .env file is read only once per process,
    improving performance significantly.
    """
    return Settings()


# Module-level instance for direct import (e.g. from app.core.config import settings)
settings = get_settings()
