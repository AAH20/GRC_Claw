"""Application configuration."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Service configuration loaded from environment variables.

    All settings are prefixed with ``RIGHTS_`` in the environment.
    """

    model_config = SettingsConfigDict(env_prefix="RIGHTS_", extra="ignore")

    app_name: str = "rights-management"
    debug: bool = False
    log_level: str = "INFO"
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str | None = None
    storage_backend: str = "memory"
    max_upload_size: int = 10_000_000


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the cached settings instance.

    Returns:
        The application-wide Settings singleton.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
