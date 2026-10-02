"""Application settings and configuration management."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database connection settings."""

    url: str = "postgresql+asyncpg://journey:journey@localhost:5432/journey_orchestrator"
    pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30
    echo: bool = False

    model_config = SettingsConfigDict(env_prefix="JOURNEY_DB_")


class RedisSettings(BaseSettings):
    """Redis connection settings."""

    url: str = "redis://localhost:6379/0"
    max_connections: int = 50
    socket_timeout: int = 5
    socket_connect_timeout: int = 5

    model_config = SettingsConfigDict(env_prefix="JOURNEY_REDIS_")


class AgentSettings(BaseSettings):
    """Per-agent configuration settings."""

    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 60
    retry_attempts: int = 3
    retry_delay: float = 1.0

    model_config = SettingsConfigDict(env_prefix="JOURNEY_AGENT_")


class OrchestrationSettings(BaseSettings):
    """Orchestration-level settings."""

    max_concurrent_journeys: int = 100
    max_steps_per_journey: int = 50
    default_step_timeout: int = 300
    checkpoint_interval: int = 60
    enable_critic: bool = True
    critic_threshold: float = 0.7

    model_config = SettingsConfigDict(env_prefix="JOURNEY_ORCH_")


class SecuritySettings(BaseSettings):
    """Security and authentication settings."""

    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600
    allowed_hosts: list[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1"])
    enable_https_redirect: bool = False

    model_config = SettingsConfigDict(env_prefix="JOURNEY_SECURITY_")


class ObservabilitySettings(BaseSettings):
    """Observability and monitoring settings."""

    metrics_enabled: bool = True
    metrics_port: int = 9090
    tracing_enabled: bool = False
    tracing_endpoint: str = "http://localhost:4318"
    profiling_enabled: bool = False

    model_config = SettingsConfigDict(env_prefix="JOURNEY_OBS_")


class Settings(BaseSettings):
    """Main application settings, loaded from config.yaml and environment variables."""

    app_name: str = "journey-orchestrator"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    log_format: str = "json"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    rate_limit: str = "100/minute"
    request_timeout: int = 30

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    orchestration: OrchestrationSettings = Field(default_factory=OrchestrationSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)

    agents: dict[str, AgentSettings] = Field(default_factory=dict)

    model_config = SettingsConfigDict(
        env_prefix="JOURNEY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production", "testing"}
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


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: The application settings singleton.
    """
    return Settings()


def load_yaml_config(path: str = "config.yaml") -> dict[str, Any]:
    """Load configuration from a YAML file.

    Args:
        path: Path to the YAML configuration file.

    Returns:
        Dictionary containing the configuration values.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        yaml.YAMLError: If the file contains invalid YAML.
    """
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
