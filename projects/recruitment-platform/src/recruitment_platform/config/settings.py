"""Application settings using Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="Recruitment Platform")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    workers: int = Field(default=1)

    # Security
    secret_key: str = Field(default="change-me-in-production")
    access_token_expire_minutes: int = Field(default=30)
    allowed_hosts: list[str] = Field(default=["*"])

    # Database
    database_url: str = Field(default="sqlite:///./recruitment.db")
    redis_url: str = Field(default="redis://localhost:6379/0")

    # External APIs
    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4")

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")

    # Feature flags
    enable_bias_detection: bool = Field(default=True)
    enable_analytics: bool = Field(default=True)
    enable_notifications: bool = Field(default=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Application settings instance.
    """
    return Settings()
