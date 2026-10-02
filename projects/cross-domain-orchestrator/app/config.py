"""Application configuration module.

Provides settings management using pydantic-settings with environment
variable support.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via environment variables prefixed with
    the field name in uppercase.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = Field(default="development", description="Runtime environment")
    debug: bool = Field(default=True, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins",
    )
    app_name: str = Field(
        default="cross-domain-orchestrator",
        description="Application name",
    )
    max_workflow_steps: int = Field(
        default=50,
        description="Maximum steps per workflow",
    )
    workflow_timeout_seconds: int = Field(
        default=300,
        description="Workflow execution timeout in seconds",
    )
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts for failed operations",
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings instance cached for the application lifetime.
    """
    return Settings()
