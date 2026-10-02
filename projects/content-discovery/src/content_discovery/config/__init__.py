"""Application configuration and settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "content-discovery"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False
    log_level: str = "info"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 300

    # OpenAI / LLM
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.7
    embedding_model: str = "text-embedding-3-small"

    # Vector Store
    vector_store_url: str = "http://localhost:8080"
    vector_dimensions: int = 1536

    # Search
    max_search_results: int = 50
    default_search_results: int = 10
    min_relevance_score: float = 0.3

    # Personalization
    personalization_ttl: int = 3600
    max_user_history: int = 100

    # Trends
    trend_window_days: int = 7
    min_trend_volume: int = 5

    # Rate Limiting
    rate_limit_per_minute: int = 60

    # Metrics
    enable_metrics: bool = True


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: Application settings instance.
    """
    return Settings()
