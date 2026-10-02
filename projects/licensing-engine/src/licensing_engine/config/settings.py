"""Application settings using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""

    model_config = SettingsConfigDict(env_prefix="LE_", env_file=".env", extra="ignore")

    # App
    app_name: str = Field(default="licensing-engine", description="Application name")
    app_env: Literal["development", "staging", "production"] = Field(
        default="development", description="Environment"
    )
    debug: bool = Field(default=False, description="Debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )

    # Server
    host: str = Field(default="127.0.0.1", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=1, description="Number of worker processes")

    # AI/LLM
    openai_api_key: str = Field(default="", description="OpenAI API key")
    llm_model: str = Field(default="gpt-4o", description="LLM model name")
    llm_temperature: float = Field(default=0.1, description="LLM temperature")
    llm_max_tokens: int = Field(default=4096, description="Max tokens for LLM")
    agent_timeout_seconds: int = Field(default=300, description="Agent timeout in seconds")

    # Database
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/licensing",
        description="Database connection URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis URL")

    # Security
    api_key_header: str = Field(default="X-API-Key", description="API key header name")
    allowed_hosts: list[str] = Field(default=["*"], description="Allowed CORS hosts")

    # Feature flags
    enable_telemetry: bool = Field(default=True, description="Enable telemetry")
    enable_caching: bool = Field(default=True, description="Enable response caching")
    cache_ttl_seconds: int = Field(default=300, description="Cache TTL in seconds")


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
