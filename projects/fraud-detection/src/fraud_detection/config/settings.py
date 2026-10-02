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
    app_name: str = "fraud-detection"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    # LangChain / LLM
    openai_api_key: str = "sk-your-key-here"
    langchain_api_key: str = "lsv2-your-key-here"
    langchain_tracing_v2: bool = True
    langchain_project: str = "fraud-detection"

    # Database
    database_url: str = "sqlite+aiosqlite:///./fraud_detection.db"
    redis_url: str = "redis://localhost:6379/0"

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_transactions: str = "transactions"
    kafka_topic_alerts: str = "fraud-alerts"

    # Security
    api_key_header: str = "X-API-Key"
    api_key: str = "dev-api-key-change-in-production"

    # Risk Scoring Thresholds
    high_risk_threshold: float = 0.8
    medium_risk_threshold: float = 0.5


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: Application settings instance.
    """
    return Settings()
