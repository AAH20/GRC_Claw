"""Configuration management for the community governance application."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via environment variables prefixed with
    ``COMMUNITY_GOVERNANCE_``.
    """

    model_config = SettingsConfigDict(
        env_prefix="COMMUNITY_GOVERNANCE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = Field(
        default="community-governance", description="Application name"
    )
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Enable debug mode")
    environment: str = Field(
        default="development", description="Deployment environment"
    )

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=1, description="Number of worker processes")

    # Security
    api_key_header: str = Field(default="X-API-Key", description="API key header name")
    allowed_api_keys: list[str] = Field(
        default_factory=list, description="List of allowed API keys"
    )

    # LangChain / LLM
    openai_api_key: str = Field(default="", description="OpenAI API key")
    langchain_api_key: str = Field(default="", description="LangChain API key")
    langchain_tracing_v2: bool = Field(
        default=False, description="Enable LangChain tracing"
    )
    langchain_project: str = Field(
        default="community-governance", description="LangChain project name"
    )
    llm_model: str = Field(default="gpt-4o-mini", description="LLM model name")
    llm_temperature: float = Field(default=0.1, description="LLM temperature")
    llm_max_tokens: int = Field(default=2048, description="LLM max tokens")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")

    # Metrics
    metrics_enabled: bool = Field(default=True, description="Enable Prometheus metrics")

    @field_validator("allowed_api_keys", mode="before")
    @classmethod
    def parse_api_keys(cls, v: Any) -> list[str]:
        """Parse comma-separated API keys from string."""
        if isinstance(v, str):
            return [key.strip() for key in v.split(",") if key.strip()]
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a valid logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return upper

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: The application settings instance.
    """
    return Settings()
