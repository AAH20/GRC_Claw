"""Application configuration module."""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment and config file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "partner-management"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000

    # Security
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Database
    database_url: str = "sqlite:///./partner_management.db"

    # Integrations
    salesforce_enabled: bool = False
    salesforce_client_id: str = ""
    salesforce_client_secret: str = ""
    salesforce_username: str = ""
    salesforce_password: str = ""
    salesforce_security_token: str = ""
    salesforce_sandbox: bool = False

    hubspot_enabled: bool = False
    hubspot_api_key: str = ""
    hubspot_portal_id: str = ""

    impartner_enabled: bool = False
    impartner_api_key: str = ""
    impartner_base_url: str = ""

    # LangChain
    langchain_api_key: str = ""
    langchain_tracing_v2: bool = False
    langchain_project: str = "partner-management"

    # Observability
    metrics_enabled: bool = True
    tracing_enabled: bool = False


def load_yaml_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load configuration from YAML file.

    Args:
        config_path: Path to the YAML config file. Defaults to config/config.yaml.

    Returns:
        Dictionary containing configuration values.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"

    if not config_path.exists():
        return {}

    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings instance.
    """
    return Settings()
