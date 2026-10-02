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
    app_name: str = "interview-scheduler"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    # Security
    api_key_header: str = "X-API-Key"
    api_key: str | None = None
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    # LangChain / LLM
    openai_api_key: str | None = None
    langchain_api_key: str | None = None
    langchain_tracing_v2: bool = False
    langchain_project: str = "interview-scheduler"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.1

    # Google Calendar
    google_credentials_path: str | None = None
    google_token_path: str | None = None
    google_scopes: list[str] = Field(
        default_factory=lambda: ["https://www.googleapis.com/auth/calendar"]
    )

    # Outlook Calendar
    outlook_client_id: str | None = None
    outlook_client_secret: str | None = None
    outlook_tenant_id: str | None = None

    # Scheduling
    default_timezone: str = "UTC"
    default_slot_duration_minutes: int = 60
    min_scheduling_notice_hours: int = 24
    max_scheduling_horizon_days: int = 30
    business_hours_start: int = 9
    business_hours_end: int = 17

    # Reminders
    default_reminder_minutes_before: list[int] = Field(
        default_factory=lambda: [1440, 60, 15]
    )

    # Observability
    enable_metrics: bool = True
    metrics_port: int = 9090

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("google_scopes", "default_reminder_minutes_before", mode="before")
    @classmethod
    def parse_list_field(cls, v: str | list[str]) -> list[str]:
        """Parse comma-separated string into list."""
        if isinstance(v, str):
            return [item.strip() for item in v.split(",")]
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: Application settings instance.
    """
    return Settings()
