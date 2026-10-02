"""Core configuration management for Campaign Optimizer."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database connection settings."""

    url: str = "postgresql://campaign:campaign@localhost:5432/campaign_optimizer"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    echo: bool = False

    model_config = SettingsConfigDict(env_prefix="DB_")


class RedisSettings(BaseSettings):
    """Redis connection settings."""

    url: str = "redis://localhost:6379/0"
    max_connections: int = 50
    socket_timeout: int = 5

    model_config = SettingsConfigDict(env_prefix="REDIS_")


class LLMSettings(BaseSettings):
    """LLM provider settings."""

    default_model: str = "gpt-4o"
    fallback_model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0

    model_config = SettingsConfigDict(env_prefix="LLM_")


class GovernanceSettings(BaseSettings):
    """GRC_Claw governance settings."""

    enabled: bool = True
    policy_engine: str = "default"
    approval_threshold: float = 0.8
    audit_log: bool = True
    max_budget_change_pct: float = 20.0
    require_approval_above: float = 1000.0
    compliance_checks: list[str] = Field(
        default_factory=lambda: [
            "budget_limits",
            "audience_restrictions",
            "creative_compliance",
            "data_privacy",
        ]
    )

    model_config = SettingsConfigDict(env_prefix="GRC_CLAW_")


class OptimizationSettings(BaseSettings):
    """Campaign optimization settings."""

    interval: int = 300
    min_improvement_threshold: float = 0.05
    max_budget_adjustment: float = 0.15
    lookback_window: int = 7
    ab_test_duration: int = 3
    confidence_level: float = 0.95

    model_config = SettingsConfigDict(env_prefix="OPTIMIZATION_")


class APISettings(BaseSettings):
    """API server settings."""

    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    rate_limit: int = 100
    request_timeout: int = 30

    model_config = SettingsConfigDict(env_prefix="API_")


class Settings(BaseSettings):
    """Application settings loaded from config.yaml and environment variables."""

    app_name: str = "campaign-optimizer"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"
    debug: bool = False

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    governance: GovernanceSettings = Field(default_factory=GovernanceSettings)
    optimization: OptimizationSettings = Field(default_factory=OptimizationSettings)
    api: APISettings = Field(default_factory=APISettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v


def load_yaml_config(path: str | Path = "config.yaml") -> dict[str, Any]:
    """Load configuration from a YAML file.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        Dictionary containing the configuration values.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        yaml.YAMLError: If the file contains invalid YAML.
    """
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Application settings instance.
    """
    return Settings()
