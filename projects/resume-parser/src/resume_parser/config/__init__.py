"""Configuration management for resume-parser service."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via environment variables prefixed with
    ``RESUME_PARSER_`` (e.g. ``RESUME_PARSER_DEBUG=true``).
    """

    model_config = SettingsConfigDict(
        env_prefix="RESUME_PARSER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="resume-parser", description="Application name")
    app_env: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=1, description="Number of worker processes")

    # LLM Configuration
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model name")
    llm_temperature: float = Field(default=0.1, description="LLM temperature")
    llm_max_tokens: int = Field(default=4096, description="Max tokens for LLM responses")

    # Agent Configuration
    agent_max_iterations: int = Field(default=10, description="Max agent iterations")
    agent_timeout_seconds: int = Field(default=120, description="Agent timeout in seconds")
    agent_retries: int = Field(default=3, description="Number of agent retries")

    # File Upload
    max_file_size_mb: int = Field(default=10, description="Max file size in MB")
    allowed_extensions: str = Field(
        default=".pdf,.docx,.txt", description="Comma-separated allowed file extensions"
    )
    upload_dir: Path = Field(default=Path("uploads"), description="Upload directory")

    # Storage
    storage_backend: str = Field(default="local", description="Storage backend type")
    storage_path: Path = Field(
        default=Path("./data/resumes"), description="Storage path for parsed resumes"
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis URL")
    cache_ttl_seconds: int = Field(default=3600, description="Cache TTL in seconds")

    @field_validator("allowed_extensions", mode="before")
    @classmethod
    def _parse_extensions(cls, v: str | list[str]) -> str:
        """Normalize allowed extensions to comma-separated lowercase string."""
        if isinstance(v, list):
            return ",".join(ext.lower() for ext in v)
        return v.lower()

    @property
    def allowed_extensions_list(self) -> list[str]:
        """Return allowed extensions as a list."""
        return [ext.strip() for ext in self.allowed_extensions.split(",") if ext.strip()]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    @property
    def max_file_size_bytes(self) -> int:
        """Return max file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: Application settings instance.
    """
    return Settings()
