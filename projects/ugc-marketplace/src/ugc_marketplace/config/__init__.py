"""Configuration package for UGC Marketplace."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings.

    All settings can be overridden via environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_env: str = "development"
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"
    debug: bool = False

    # API
    api_prefix: str = "/api/v1"
    max_content_size_mb: int = 50
    allowed_hosts: list[str] = ["*"]

    # LLM
    openai_api_key: str = ""
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096

    # Storage
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ugc_marketplace"

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_alerts: str = "ugc-marketplace-alerts"

    # Moderation
    default_confidence_threshold: float = 0.7
    enable_metrics: bool = True

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Application settings singleton.
    """
    return Settings()
