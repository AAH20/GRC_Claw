"""Application configuration and settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="ESCALATION_",
        env_file=".env",
        extra="ignore",
    )

    # Application
    app_name: str = "escalation-workflow"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"

    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 1

    # LangChain / LLM
    openai_api_key: str = ""
    langchain_api_key: str = ""
    langchain_tracing_v2: bool = False
    langchain_project: str = "escalation-workflow"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.1

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Database
    database_url: str = "sqlite:///./escalation_workflow.db"

    # SLA Defaults
    default_sla_minutes: int = 60
    critical_sla_minutes: int = 15
    high_sla_minutes: int = 30
    medium_sla_minutes: int = 120
    low_sla_minutes: int = 480

    # Notifications
    slack_webhook_url: str = ""
    pagerduty_api_key: str = ""
    email_smtp_host: str = ""
    email_smtp_port: int = 587
    email_from: str = "escalations@example.com"

    # Observability
    log_level: str = "INFO"
    enable_metrics: bool = True
    metrics_port: int = 9090


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: Application settings instance.
    """
    return Settings()
