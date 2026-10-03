"""Application configuration and settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "moderation-analytics"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 1

    # LangChain / LLM
    openai_api_key: str = Field(
        default="", description="OpenAI API key for LangChain agents"
    )
    langchain_model: str = "gpt-4o-mini"
    langchain_temperature: float = 0.1
    langchain_max_tokens: int = 4096
    langchain_tracing: bool = False

    # Analytics
    default_time_window_days: int = 30
    max_time_window_days: int = 365
    min_confidence_threshold: float = 0.7

    # Integrations
    moderation_api_url: str = Field(
        default="", description="External moderation API URL"
    )
    moderation_api_key: str = Field(
        default="", description="External moderation API key"
    )
    analytics_db_url: str = Field(default="", description="Analytics database URL")

    # Observability
    enable_metrics: bool = True
    enable_tracing: bool = False
    jaeger_endpoint: str = Field(default="", description="Jaeger tracing endpoint")

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port number is in valid range."""
        if not 1 <= v <= 65535:
            raise ValueError(f"Port must be between 1 and 65535, got {v}")
        return v

    @field_validator("workers")
    @classmethod
    def validate_workers(cls, v: int) -> int:
        """Validate worker count is positive."""
        if v < 1:
            raise ValueError(f"Workers must be at least 1, got {v}")
        return v

    @field_validator("langchain_temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is in valid range."""
        if not 0.0 <= v <= 2.0:
            raise ValueError(f"Temperature must be between 0.0 and 2.0, got {v}")
        return v

    @field_validator("min_confidence_threshold")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate confidence threshold is in valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(
                f"Confidence threshold must be between 0.0 and 1.0, got {v}"
            )
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: Application settings instance.
    """
    return Settings()
