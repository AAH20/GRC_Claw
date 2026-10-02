"""Application configuration and settings."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


class AgentConfig(BaseSettings):
    """Configuration for an AI agent."""

    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000
    retry_attempts: int = 3
    retry_delay: float = 1.0


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    url: str = "postgresql://postgres:postgres@localhost:5432/real_estate"
    pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30
    echo: bool = False


class RedisConfig(BaseSettings):
    """Redis configuration."""

    url: str = "redis://localhost:6379/0"
    max_connections: int = 50


class ServerConfig(BaseSettings):
    """Server configuration."""

    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    reload: bool = True
    timeout_keep_alive: int = 30


class IntegrationConfig(BaseSettings):
    """Third-party integration configuration."""

    base_url: str
    timeout: int = 30
    rate_limit: int = 100


class SalesforceConfig(IntegrationConfig):
    """Salesforce-specific configuration."""

    api_version: str = "v58.0"


class MarketingConfig(BaseSettings):
    """Marketing configuration."""

    email_templates_dir: str = "templates/email"
    report_templates_dir: str = "templates/reports"
    default_from_email: str = "marketing@realestate.com"
    nurture_sequence: list[dict[str, Any]] = Field(default_factory=list)


class AnalyticsConfig(BaseSettings):
    """Analytics configuration."""

    tracking_enabled: bool = True
    attribution_window_days: int = 30
    session_timeout_minutes: int = 30
    metrics: list[str] = Field(default_factory=lambda: [
        "impressions", "clicks", "leads", "conversions", "revenue"
    ])


class AppConfig(BaseSettings):
    """Main application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    app_name: str = "Real Estate Marketing Platform"
    version: str = "0.1.0"
    description: str = "AI-powered real estate marketing automation"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"

    server: ServerConfig = Field(default_factory=ServerConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)

    listings_agent: AgentConfig = Field(default_factory=AgentConfig)
    lead_nurture_agent: AgentConfig = Field(default_factory=AgentConfig)
    virtual_tours_agent: AgentConfig = Field(default_factory=AgentConfig)
    analytics_agent: AgentConfig = Field(default_factory=AgentConfig)
    reporting_agent: AgentConfig = Field(default_factory=AgentConfig)

    zillow: IntegrationConfig = Field(
        default_factory=lambda: IntegrationConfig(base_url="https://api.zillow.com/v2")
    )
    realtor: IntegrationConfig = Field(
        default_factory=lambda: IntegrationConfig(base_url="https://api.realtor.com/v1")
    )
    salesforce: SalesforceConfig = Field(
        default_factory=lambda: SalesforceConfig(base_url="https://login.salesforce.com")
    )

    marketing: MarketingConfig = Field(default_factory=MarketingConfig)
    analytics: AnalyticsConfig = Field(default_factory=AnalyticsConfig)

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    zillow_api_key: str = ""
    realtor_api_key: str = ""
    salesforce_username: str = ""
    salesforce_password: str = ""
    salesforce_security_token: str = ""

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v.upper()


def load_yaml_config() -> dict[str, Any]:
    """Load configuration from YAML file.

    Returns:
        Dictionary containing configuration values from YAML file.
    """
    if not CONFIG_FILE.exists():
        return {}
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache
def get_settings() -> AppConfig:
    """Get cached application settings.

    Returns:
        Application configuration singleton.
    """
    yaml_config = load_yaml_config()
    flat_config: dict[str, Any] = {}
    for section, values in yaml_config.items():
        if isinstance(values, dict):
            for key, value in values.items():
                flat_config[f"{section}_{key}"] = value
        else:
            flat_config[section] = values
    return AppConfig(**flat_config)
