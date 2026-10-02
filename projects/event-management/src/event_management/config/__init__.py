"""Configuration models for the Event Management system."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Application
    app_name: str = "Event Management"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False
    log_level: str = "info"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Security
    secret_key: str = "change-me-in-production"
    cors_origins: list[str] = ["http://localhost:3000"]

    # Database
    database_url: str = "sqlite:///./events.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # LLM
    openai_api_key: str = ""
    openai_model: str = "gpt-4"
    openai_max_tokens: int = 4096
    openai_temperature: float = 0.7

    # LangChain
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "event-management"

    # Integrations
    eventbrite_api_key: str = ""
    eventbrite_oauth_token: str = ""
    meetup_api_key: str = ""
    meetup_client_id: str = ""
    meetup_client_secret: str = ""
    luma_api_key: str = ""

    # grc-marketing-core
    grc_marketing_api_key: str = ""
    grc_marketing_base_url: str = "https://api.grc-marketing.example.com"

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60


settings = Settings()
