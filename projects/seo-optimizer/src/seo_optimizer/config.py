"""Configuration management for SEO Optimizer."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via environment variables with the
    same name in uppercase.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_environment: str = "development"
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4

    # LLM
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_temperature: float = 0.1
    openai_max_tokens: int = 4096

    # Google Search Console
    google_search_console_enabled: bool = False
    google_search_console_credentials_path: str | None = None
    google_search_console_site_url: str | None = None

    # SEMrush
    semrush_enabled: bool = False
    semrush_api_key: str | None = None

    # Ahrefs
    ahrefs_enabled: bool = False
    ahrefs_api_key: str | None = None

    # Screaming Frog
    screaming_frog_enabled: bool = False
    screaming_frog_spider_path: str | None = None

    # Cache
    cache_backend: str = "memory"
    cache_ttl_seconds: int = 3600
    cache_max_size: int = 1000

    # Rate Limiting
    rate_limiting_enabled: bool = True
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst_size: int = 10

    # Monitoring
    prometheus_enabled: bool = True
    prometheus_port: int = 9090

    # Agents
    max_concurrent_agents: int = 3
    agent_timeout_seconds: int = 300
    agent_retry_attempts: int = 3
    agent_retry_delay_seconds: int = 5


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings instance.
    """
    return Settings()
