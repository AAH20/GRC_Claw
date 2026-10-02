"""Application configuration using Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="employer-branding", description="Application name")
    app_env: str = Field(
        default="development",
        description="Environment (development/staging/production)",
    )
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Server
    host: str = Field(default="127.0.0.1", description="Server host")
    port: int = Field(default=8000, description="Server port")

    # AI/LLM
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model name")
    langchain_tracing_v2: bool = Field(default=False, description="Enable LangChain tracing")
    langchain_api_key: str = Field(default="", description="LangSmith API key")

    # External Services
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis URL")
    glassdoor_api_key: str = Field(default="", description="Glassdoor API key")
    linkedin_api_key: str = Field(default="", description="LinkedIn API key")
    indeed_api_key: str = Field(default="", description="Indeed API key")

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=100, description="API rate limit per minute")

    # Content Generation
    max_content_length: int = Field(
        default=10000, description="Maximum content length in characters"
    )
    default_language: str = Field(default="en", description="Default content language")

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
