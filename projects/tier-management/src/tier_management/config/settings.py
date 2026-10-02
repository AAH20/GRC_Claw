"""Application configuration using Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via environment variables prefixed with
    ``TIER_MANAGEMENT_`` (e.g. ``TIER_MANAGEMENT_LOG_LEVEL=DEBUG``).
    """

    model_config = SettingsConfigDict(
        env_prefix="TIER_MANAGEMENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="tier-management", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: str = Field(default="development", description="Deployment environment")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Server
    host: str = Field(default="127.0.0.1", description="Server bind host")
    port: int = Field(default=8000, description="Server bind port")
    workers: int = Field(default=1, description="Number of Uvicorn workers")

    # Security
    secret_key: str = Field(default="change-me-in-production", description="Secret key")
    access_token_expire_minutes: int = Field(default=30, description="Token expiry in minutes")
    allowed_hosts: list[str] = Field(default=["*"], description="Allowed CORS hosts")

    # LangChain / LLM
    openai_api_key: str = Field(default="", description="OpenAI API key")
    llm_model: str = Field(default="gpt-4o-mini", description="LLM model name")
    llm_temperature: float = Field(default=0.1, description="LLM temperature")
    llm_max_tokens: int = Field(default=2048, description="Max LLM output tokens")
    evaluation_timeout_seconds: int = Field(default=30, description="Agent eval timeout")

    # Tier Management
    max_tier_levels: int = Field(default=10, description="Maximum tier levels")
    upgrade_cooldown_hours: int = Field(default=24, description="Hours between upgrades")
    analytics_retention_days: int = Field(default=90, description="Days to keep analytics")

    # External Services
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis URL")
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/tier_management",
        description="Database URL",
    )

    # Observability
    enable_metrics: bool = Field(default=True, description="Enable Prometheus metrics")
    enable_tracing: bool = Field(default=False, description="Enable distributed tracing")
    jaeger_endpoint: str = Field(default="http://localhost:14268", description="Jaeger endpoint")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the allowed values."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return upper

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment is one of the allowed values."""
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: The application settings singleton.
    """
    return Settings()
