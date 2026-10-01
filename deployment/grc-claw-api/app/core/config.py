"""Application configuration."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Application
    APP_NAME: str = "GRC_Claw API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # API
    API_V1_PREFIX: str = "/v1.0"
    API_TITLE: str = "GRC_Claw API"
    API_DESCRIPTION: str = "Governance, Risk, and Compliance platform for agentic AI"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "RS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    OIDC_ISSUER: str = "https://auth.grc-claw.io"
    OIDC_AUDIENCE: str = "https://api.grc-claw.io"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://grc:grc@localhost:5432/grc_claw"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Rate Limiting
    RATE_LIMIT_DEFAULT_RPS: int = 100
    RATE_LIMIT_DEFAULT_BURST: int = 200
    RATE_LIMIT_ENFORCEMENT_RPS: int = 10000
    RATE_LIMIT_ENFORCEMENT_BURST: int = 2000

    # gRPC
    GRPC_HOST: str = "0.0.0.0"
    GRPC_PORT: int = 50051
    GRPC_MAX_WORKERS: int = 100

    # Webhooks
    WEBHOOK_MAX_RETRIES: int = 6
    WEBHOOK_RETRY_DELAYS: list[int] = [0, 60, 300, 1800, 7200, 28800]
    WEBHOOK_TIMEOUT_SECONDS: int = 10
    WEBHOOK_TIMESTAMP_TOLERANCE: int = 300

    # Observability
    OTEL_SERVICE_NAME: str = "grc-claw-api"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"
    LOG_LEVEL: str = "INFO"
    ENABLE_METRICS: bool = True


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
