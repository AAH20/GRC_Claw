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
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "customer-segmentation"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    secret_key: str = Field(default="change-me-in-production", min_length=16)

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4

    # LLM Providers
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    default_llm_provider: Literal["openai", "anthropic"] = "openai"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096
    llm_timeout: int = 60

    # Salesforce
    salesforce_username: str = ""
    salesforce_password: str = ""
    salesforce_security_token: str = ""
    salesforce_domain: str = "login"
    salesforce_api_version: str = "v59.0"

    # HubSpot
    hubspot_api_key: str = ""
    hubspot_portal_id: str = ""

    # Google Analytics
    google_analytics_property_id: str = ""
    google_application_credentials: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_password: str = ""

    # Monitoring
    prometheus_port: int = 9090
    sentry_dsn: str = ""

    # Feature Flags
    enable_real_time_segmentation: bool = True
    enable_performance_tracking: bool = True
    enable_bias_detection: bool = True

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Ensure secret key is changed in production."""
        values = info.data
        if values.get("environment") == "production" and v == "change-me-in-production":
            raise ValueError("SECRET_KEY must be changed in production environment")
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
