"""Application configuration using Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via environment variables prefixed with
    ``RECRUITMENT_`` (e.g. ``RECRUITMENT_ENVIRONMENT=production``).
    """

    model_config = SettingsConfigDict(
        env_prefix="RECRUITMENT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "recruitment-analytics"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    secret_key: str = Field(default="change-me-in-production", min_length=16)

    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = Field(default=1, ge=1, le=16)

    # LLM / LangChain
    openai_api_key: str = Field(default="", description="OpenAI API key for LangChain agents")
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=4096, ge=256, le=8192)

    # External APIs
    ats_api_url: str = Field(default="https://api.ats.example.com")
    ats_api_key: str = Field(default="")
    hrms_api_url: str = Field(default="https://api.hrms.example.com")
    hrms_api_key: str = Field(default="")

    # Cache / Queue
    redis_url: str = Field(default="redis://localhost:6379/0")
    cache_ttl_seconds: int = Field(default=300, ge=60, le=3600)

    # Database
    database_url: str = Field(default="postgresql://postgres:postgres@localhost:5432/recruitment_analytics")

    # Observability
    enable_metrics: bool = True
    enable_tracing: bool = False
    jaeger_endpoint: str = Field(default="http://localhost:14268/api/traces")

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Ensure secret key is changed in production."""
        values = info.data
        if values.get("environment") == "production" and v == "change-me-in-production":
            raise ValueError("secret_key must be changed in production environment")
        return v

    @property
    def is_production(self) -> bool:
        """Return True when running in production environment."""
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
