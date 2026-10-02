"""Configuration management for the Website Optimization platform."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application settings.

    Attributes:
        name: Application name.
        version: Application version.
        env: Environment name.
        log_level: Logging level.
    """

    name: str = "website-optimization"
    version: str = "0.1.0"
    env: str = "development"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_prefix="APP_")


class ServerSettings(BaseSettings):
    """Server settings.

    Attributes:
        host: Bind host.
        port: Bind port.
        workers: Number of worker processes.
    """

    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4

    model_config = SettingsConfigDict(env_prefix="SERVER_")


class Settings(BaseSettings):
    """Combined application settings.

    Attributes:
        app: Application settings.
        server: Server settings.
    """

    app: AppSettings = AppSettings()
    server: ServerSettings = ServerSettings()

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Application settings.
    """
    return Settings()
