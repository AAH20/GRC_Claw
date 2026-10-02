"""Application settings for Sales Forecaster."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Sales Forecaster"
    app_version: str = "0.1.0"
    environment: str = "development"
    is_development: bool = True
    log_level: str = "INFO"

    server_host: str = "0.0.0.0"
    server_port: int = 8000
    server_workers: int = 1

    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 300

    forecast_default_horizon_days: int = 30
    forecast_max_horizon_days: int = 365

    data_collection_timeout_seconds: int = 60
    max_retry_attempts: int = 3


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


def setup_logging() -> None:
    """Configure structured logging."""
    import logging
    import structlog

    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger(__name__)
