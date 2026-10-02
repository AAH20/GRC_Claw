"""Application configuration loading."""

from __future__ import annotations

import functools
import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"


class Settings(BaseSettings):
    """Environment-driven application settings."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    compliance_environment: str = Field(default="development")
    compliance_log_level: str = Field(default="INFO")
    compliance_secret_key: str = Field(default="change-me-in-production")

    server_host: str = Field(default="0.0.0.0")
    server_port: int = Field(default=8000)

    openai_api_key: str | None = Field(default=None)
    langchain_api_key: str | None = Field(default=None)
    langchain_tracing_v2: bool = Field(default=False)
    langchain_project: str = Field(default="marketing-compliance")

    salesforce_client_id: str | None = Field(default=None)
    salesforce_client_secret: str | None = Field(default=None)
    salesforce_username: str | None = Field(default=None)
    salesforce_password: str | None = Field(default=None)
    salesforce_security_token: str | None = Field(default=None)
    salesforce_sandbox: bool = Field(default=False)

    hubspot_api_key: str | None = Field(default=None)
    hubspot_access_token: str | None = Field(default=None)

    mailchimp_api_key: str | None = Field(default=None)
    mailchimp_server_prefix: str | None = Field(default=None)

    prometheus_enabled: bool = Field(default=True)
    slack_webhook_url: str | None = Field(default=None)

    data_dir: str = Field(default="./data")


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings.

    Returns:
        The resolved :class:`Settings` instance.
    """
    return Settings()


def load_yaml_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load the YAML configuration file.

    Args:
        path: Optional explicit path; defaults to ``config/config.yaml``.

    Returns:
        The parsed configuration mapping, or an empty mapping when the file is
        missing or unreadable.
    """
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not config_path.exists():
        return {}
    try:
        with config_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def get_config() -> dict[str, Any]:
    """Return merged application configuration.

    Returns:
        The YAML configuration augmented with the resolved environment name.
    """
    config = load_yaml_config()
    config.setdefault("environment", os.getenv("COMPLIANCE_ENVIRONMENT", "development"))
    return config
