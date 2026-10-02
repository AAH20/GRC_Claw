"""Application configuration and settings management."""

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
    app_env: Literal["dev", "staging", "prod"] = "dev"
    app_name: str = "workflow-automation"
    app_version: str = "0.1.0"
    log_level: str = "INFO"
    secret_key: str = Field(default="change-me-in-production")

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # n8n Integration
    n8n_base_url: str = "http://localhost:5678"
    n8n_api_key: str = ""
    n8n_timeout: int = 30

    # Zapier Integration
    zapier_webhook_url: str = ""
    zapier_timeout: int = 30

    # Make Integration
    make_base_url: str = "https://www.make.com"
    make_api_key: str = ""
    make_team_id: str = ""
    make_timeout: int = 30

    # LangChain
    langchain_api_key: str = ""
    langchain_project: str = "workflow-automation"
    langchain_tracing: bool = False
    langchain_model: str = "gpt-4"
    langchain_temperature: float = 0.1
    langchain_max_tokens: int = 4096

    # grc-marketing-core
    grc_marketing_core_enabled: bool = True
    grc_marketing_core_api_endpoint: str = ""
    grc_marketing_core_api_key: str = ""

    # Prometheus
    prometheus_enabled: bool = True
    prometheus_port: int = 9090

    # Agent settings
    max_concurrent_discoveries: int = 5
    max_concurrent_optimizations: int = 3
    max_concurrent_executions: int = 10
    discovery_timeout: int = 300
    optimization_timeout: int = 600
    execution_timeout: int = 1800
    retry_attempts: int = 3
    retry_delay: int = 5

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a valid logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return upper

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "prod"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == "dev"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
