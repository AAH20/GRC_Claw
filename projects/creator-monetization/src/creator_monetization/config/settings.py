"""Application settings using pydantic-settings."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App
    app_name: str = "creator-monetization"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"

    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 4

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/creator_monetization"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50

    # LangChain / LLM
    openai_api_key: str = ""
    langchain_api_key: str = ""
    langchain_tracing_v2: bool = False
    langchain_project: str = "creator-monetization"

    # Agent Models
    revenue_optimizer_model: str = "gpt-4"
    payout_manager_model: str = "gpt-4"
    tier_recommender_model: str = "gpt-4"
    subscription_model: str = "gpt-4"
    analytics_model: str = "gpt-4"

    # Integrations
    stripe_api_key: str = ""
    stripe_webhook_secret: str = ""
    paypal_client_id: str = ""
    paypal_client_secret: str = ""
    patreon_api_key: str = ""

    # Monitoring
    prometheus_enabled: bool = True
    sentry_enabled: bool = False
    sentry_dsn: str = ""

    # Security
    access_token_expire_minutes: int = 30


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
