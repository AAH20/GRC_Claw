"""Application settings using pydantic-settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings.

    Attributes:
        app_name: Application name.
        app_env: Environment name (development, staging, production).
        debug: Debug mode flag.
        log_level: Logging level.
        host: Server bind host.
        port: Server bind port.
        langchain_api_key: LangChain API key.
        langchain_tracing_v2: Enable LangChain tracing.
        langchain_project: LangChain project name.
        openai_api_key: OpenAI API key for LLM calls.
        slack_webhook_url: Slack webhook for notifications.
        smtp_host: SMTP server host.
        smtp_port: SMTP server port.
        smtp_user: SMTP username.
        smtp_password: SMTP password.
        notification_email: Default notification recipient.
        database_url: Database connection URL.
        redis_url: Redis connection URL.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "compliance-monitor"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000

    langchain_api_key: str = ""
    langchain_tracing_v2: bool = False
    langchain_project: str = "compliance-monitor"
    openai_api_key: str = ""

    slack_webhook_url: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    notification_email: str = ""

    database_url: str = "sqlite+aiosqlite:///./compliance.db"
    redis_url: str = "redis://localhost:6379/0"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Application settings instance.
    """
    return Settings()
