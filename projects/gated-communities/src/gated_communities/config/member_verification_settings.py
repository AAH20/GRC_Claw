"""Application configuration using Pydantic Settings."""

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
    app_name: str = Field(default="member-verification", description="Application name")
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

    # Security
    secret_key: str = Field(
        default="change-me-in-production", description="Secret key for JWT"
    )
    access_token_expire_minutes: int = Field(
        default=30, description="Token expiration in minutes"
    )
    api_key_header: str = Field(default="X-API-Key", description="API key header name")

    # LangChain / LLM
    openai_api_key: str = Field(default="", description="OpenAI API key")
    langchain_api_key: str = Field(default="", description="LangChain API key")
    langchain_tracing_v2: bool = Field(
        default=False, description="Enable LangChain tracing"
    )
    llm_model: str = Field(default="gpt-4o-mini", description="LLM model name")
    llm_temperature: float = Field(default=0.1, description="LLM temperature")

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0", description="Redis connection URL"
    )

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./member_verification.db",
        description="Database connection URL",
    )

    # Rate Limiting
    rate_limit_requests: int = Field(default=100, description="Max requests per window")
    rate_limit_window: int = Field(
        default=60, description="Rate limit window in seconds"
    )

    # Verification
    min_trust_score: float = Field(
        default=0.3, description="Minimum trust score to pass"
    )
    max_fraud_risk: float = Field(
        default=0.7, description="Maximum fraud risk to allow"
    )
    verification_timeout: int = Field(
        default=30, description="Verification timeout in seconds"
    )

    @field_validator("llm_temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate LLM temperature is within valid range."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("llm_temperature must be between 0.0 and 2.0")
        return v

    @field_validator("min_trust_score", "max_fraud_risk")
    @classmethod
    def validate_score_range(cls, v: float) -> float:
        """Validate score is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Score must be between 0.0 and 1.0")
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: Application settings instance.
    """
    return Settings()
