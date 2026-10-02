"""Application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings sourced from environment / ``.env``."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["development", "staging", "production"] = "development"
    log_level: str = "INFO"
    secret_key: str = Field(default="change-me-in-production", repr=False)
    host: str = "0.0.0.0"
    port: int = 8000

    openai_api_key: str | None = Field(default=None, repr=False)

    twitter_api_key: str | None = Field(default=None, repr=False)
    twitter_api_secret: str | None = Field(default=None, repr=False)
    twitter_access_token: str | None = Field(default=None, repr=False)
    twitter_access_token_secret: str | None = Field(default=None, repr=False)
    twitter_bearer_token: str | None = Field(default=None, repr=False)

    instagram_access_token: str | None = Field(default=None, repr=False)
    instagram_app_id: str | None = None
    instagram_app_secret: str | None = Field(default=None, repr=False)

    facebook_access_token: str | None = Field(default=None, repr=False)
    facebook_app_id: str | None = None
    facebook_app_secret: str | None = Field(default=None, repr=False)
    facebook_page_id: str | None = None

    linkedin_access_token: str | None = Field(default=None, repr=False)
    linkedin_client_id: str | None = None
    linkedin_client_secret: str | None = Field(default=None, repr=False)

    tiktok_access_token: str | None = Field(default=None, repr=False)
    tiktok_app_id: str | None = None
    tiktok_app_secret: str | None = Field(default=None, repr=False)

    redis_url: str = "redis://localhost:6379/0"
    database_url: str | None = None

    request_timeout: float = 30.0
    max_retries: int = 3


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""
    return Settings()
