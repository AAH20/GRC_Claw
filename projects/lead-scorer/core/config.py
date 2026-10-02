"""Core configuration and settings management."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


class Settings(BaseSettings):
    """Application settings loaded from environment and config file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "lead-scorer"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # Database
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://leadscorer:leadscorer@localhost:5432/leadscorer"
    )
    db_pool_size: int = 20
    db_max_overflow: int = 10

    # Redis
    redis_url: RedisDsn = Field(default="redis://localhost:6379/0")

    # LLM
    openai_api_key: str = Field(default="")
    scoring_model: str = "gpt-4o"
    scoring_temperature: float = 0.1

    # Governance
    enable_governance: bool = True
    audit_log: bool = True
    pii_redaction: bool = True

    # Observability
    log_level: str = "INFO"
    prometheus_enabled: bool = True
    otel_enabled: bool = True
    otel_endpoint: str = "http://localhost:4318"

    # Security
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

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
    """Get cached settings instance.

    Returns:
        Settings singleton.
    """
    return Settings()


def load_yaml_config(path: Path | None = None) -> dict:
    """Load YAML configuration file.

    Args:
        path: Path to config file. Defaults to config.yaml in project root.

    Returns:
        Parsed configuration dictionary.
    """
    config_path = path or CONFIG_PATH
    if not config_path.exists():
        return {}
    with open(config_path) as f:
        return yaml.safe_load(f) or {}
