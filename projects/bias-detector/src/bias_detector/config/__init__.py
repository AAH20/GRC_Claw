"""Configuration management for the bias-detector application."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via environment variables prefixed with
    ``BIAS_DETECTOR_`` (e.g. ``BIAS_DETECTOR_LOG_LEVEL=debug``).
    """

    model_config = SettingsConfigDict(
        env_prefix="BIAS_DETECTOR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "bias-detector"
    app_version: str = "0.1.0"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "text"] = "json"

    # LLM / LangChain
    openai_api_key: str = Field(default="", repr=False)
    openai_model: str = "gpt-4o-mini"
    langchain_tracing: bool = False
    langchain_project: str = "bias-detector"

    # Analysis thresholds
    demographic_disparity_threshold: float = 0.15
    language_bias_threshold: float = 0.3
    fairness_score_threshold: float = 0.7
    pattern_confidence_threshold: float = 0.6

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60

    # CORS
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def is_production(self) -> bool:
        """Return True if running in production environment."""
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Return a cached instance of application settings.

    Returns:
        Settings: The application settings singleton.
    """
    return Settings()
