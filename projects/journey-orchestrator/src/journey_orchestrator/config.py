"""Configuration management for Journey Orchestrator."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Application
    environment: str = "development"
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # LangChain / LLM
    openai_api_key: str = ""
    langchain_api_key: str = ""
    langchain_tracing_v2: bool = False
    langchain_project: str = "journey-orchestrator"

    # Salesforce
    salesforce_client_id: str = ""
    salesforce_client_secret: str = ""
    salesforce_username: str = ""
    salesforce_password: str = ""
    salesforce_security_token: str = ""
    salesforce_domain: str = "https://login.salesforce.com"

    # Segment
    segment_write_key: str = ""

    # Amplitude
    amplitude_api_key: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Monitoring
    prometheus_port: int = 9090
    otel_exporter_otlp_endpoint: str = "http://localhost:4318"


_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the application settings singleton.

    Returns:
        The application settings instance.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
