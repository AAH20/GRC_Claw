"""Application settings using Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["Settings", "get_settings"]


class Settings(BaseSettings):
    """Application configuration settings.

    All settings can be overridden via environment variables prefixed with
    ``ONBOARDING_`` (e.g. ``ONBOARDING_LOG_LEVEL=debug``).
    """

    model_config = SettingsConfigDict(
        env_prefix="ONBOARDING_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "onboarding-automator"
    environment: str = Field(default="development", pattern="^(development|staging|production|test)$")
    debug: bool = False
    log_level: str = "INFO"

    # Server
    host: str = "0.0.0.0"  # noqa: S104
    port: int = 8000

    # Security
    api_key_header: str = "X-API-Key"
    allowed_origins: list[str] = Field(default_factory=lambda: ["*"])

    # LLM
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096
    openai_api_key: str = Field(default="", repr=False)

    # Agent settings
    agent_timeout_seconds: int = 300
    max_concurrent_agents: int = 5
    max_retries: int = 3
    retry_delay_seconds: float = 1.0

    # Document storage
    document_storage_backend: str = "local"
    document_max_size_mb: int = 50
    document_allowed_types: list[str] = Field(
        default_factory=lambda: ["pdf", "doc", "docx", "txt", "rtf", "png", "jpg", "jpeg"]
    )
    document_storage_path: str = "/tmp/onboarding-automator/documents"

    # Database
    database_url: str = "sqlite:///./onboarding.db"
    database_pool_size: int = 5

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Compliance
    compliance_enabled: bool = True
    compliance_strict_mode: bool = False

    # Notifications
    notifications_enabled: bool = True
    notification_channels: list[str] = Field(default_factory=lambda: ["email", "slack"])

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate and normalize the log level."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return upper

    @field_validator("llm_temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is in valid range."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("llm_temperature must be between 0.0 and 2.0")
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_test(self) -> bool:
        """Check if running in test environment."""
        return self.environment == "test"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings instance.

    Returns:
        The global Settings instance (cached via ``lru_cache``).
    """
    return Settings()
