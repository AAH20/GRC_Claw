"""Configuration management for Customer Service AI Platform."""

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
    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    cors_origins: list[str] = Field(default=["*"], alias="CORS_ORIGINS")

    # OpenAI
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")

    # LangChain
    langchain_tracing_v2: bool = Field(default=False, alias="LANGCHAIN_TRACING_V2")
    langchain_api_key: str = Field(default="", alias="LANGCHAIN_API_KEY")
    langchain_project: str = Field(default="customer-service", alias="LANGCHAIN_PROJECT")

    # Zendesk
    zendesk_subdomain: str = Field(default="", alias="ZENDESK_SUBDOMAIN")
    zendesk_email: str = Field(default="", alias="ZENDESK_EMAIL")
    zendesk_api_token: str = Field(default="", alias="ZENDESK_API_TOKEN")

    # Intercom
    intercom_access_token: str = Field(default="", alias="INTERCOM_ACCESS_TOKEN")
    intercom_workspace_id: str = Field(default="", alias="INTERCOM_WORKSPACE_ID")

    # Salesforce
    salesforce_username: str = Field(default="", alias="SALESFORCE_USERNAME")
    salesforce_password: str = Field(default="", alias="SALESFORCE_PASSWORD")
    salesforce_security_token: str = Field(default="", alias="SALESFORCE_SECURITY_TOKEN")
    salesforce_client_id: str = Field(default="", alias="SALESFORCE_CLIENT_ID")
    salesforce_client_secret: str = Field(default="", alias="SALESFORCE_CLIENT_SECRET")
    salesforce_domain: str = Field(default="login", alias="SALESFORCE_DOMAIN")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # Monitoring
    prometheus_enabled: bool = Field(default=True, alias="PROMETHEUS_ENABLED")
    sentry_dsn: str = Field(default="", alias="SENTRY_DSN")


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Application settings instance.
    """
    return Settings()
