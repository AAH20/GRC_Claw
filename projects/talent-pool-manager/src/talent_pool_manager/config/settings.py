"""Settings module for talent pool manager."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via environment variables prefixed with
    ``TALENT_POOL_``. For example ``TALENT_POOL_LOG_LEVEL=debug``.
    """

    model_config = SettingsConfigDict(
        env_prefix="TALENT_POOL_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "talent-pool-manager"
    app_version: str = "0.1.0"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    # Security
    api_key_header: str = "X-API-Key"
    api_key: str | None = None
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    # LLM / AI
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o"
    openai_temperature: float = 0.7
    llm_max_tokens: int = 4096
    llm_timeout: int = 60

    # External APIs
    linkedin_api_key: str | None = None
    github_token: str | None = None
    indeed_api_key: str | None = None

    # Email / SMTP
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    email_from: str = "noreply@talentpool.local"

    # Database
    database_url: str = "sqlite:///./talent_pool.db"
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # Redis / Cache
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 3600

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60

    # Agent Defaults
    default_discovery_depth: int = 3
    default_segment_count: int = 5
    default_outreach_tone: Literal["professional", "casual", "enthusiastic"] = "professional"
    max_candidates_per_pool: int = 1000
    max_pools_per_org: int = 100

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("log_level", mode="before")
    @classmethod
    def _uppercase_log_level(cls, v: str) -> str:
        """Normalize log level to uppercase."""
        return v.upper()

    @property
    def is_production(self) -> bool:
        """Return True when running in production environment."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Return True when running in development environment."""
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    """Return a cached instance of application settings.

    Returns:
        Settings: The application settings singleton.
    """
    return Settings()
