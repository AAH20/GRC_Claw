"""Application settings using pydantic-settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    APP_NAME: str = "content-marketplace"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/content_marketplace"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Marketplace settings
    MAX_LISTINGS_PER_USER: int = 100
    DEFAULT_CURRENCY: str = "USD"
    PRICE_UPDATE_INTERVAL_SECONDS: int = 3600
    TRUST_SCORE_THRESHOLD: float = 0.7
    ANALYTICS_CACHE_TTL_SECONDS: int = 300

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()
