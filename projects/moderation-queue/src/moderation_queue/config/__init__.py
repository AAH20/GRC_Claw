"""Configuration management for the moderation queue application."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="moderation-queue", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    environment: Literal["development", "staging", "production"] = Field(
        default="development", description="Deployment environment"
    )
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=1, description="Number of worker processes")

    # Database
    database_url: str = Field(
        default="sqlite:///./moderation.db", description="Database connection URL"
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0", description="Redis connection URL"
    )

    # OpenAI / LangChain
    openai_api_key: str | None = Field(default=None, description="OpenAI API key")
    langchain_model: str = Field(
        default="gpt-4o-mini", description="LangChain model name"
    )
    langchain_temperature: float = Field(
        default=0.1, description="LangChain model temperature"
    )

    # Moderation
    auto_moderation_enabled: bool = Field(
        default=True, description="Enable auto-moderation"
    )
    auto_moderation_threshold: float = Field(
        default=0.7, description="Confidence threshold for auto-moderation"
    )
    escalation_threshold: float = Field(
        default=0.9, description="Priority score threshold for escalation"
    )
    max_queue_size: int = Field(default=1000, description="Maximum items per queue")
    review_timeout_seconds: int = Field(
        default=3600, description="Timeout for human review in seconds"
    )

    # Metrics
    metrics_enabled: bool = Field(default=True, description="Enable Prometheus metrics")
    metrics_port: int = Field(default=9090, description="Prometheus metrics port")

    @field_validator("langchain_temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is within valid range."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v

    @field_validator("auto_moderation_threshold", "escalation_threshold")
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        """Validate threshold is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
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
        Settings: Application settings instance.
    """
    return Settings()
