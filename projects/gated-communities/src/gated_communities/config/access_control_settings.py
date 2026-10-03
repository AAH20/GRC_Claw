"""Application configuration module."""

from functools import lru_cache

from pydantic import BaseModel, Field, SecretStr


class Settings(BaseModel):
    """Application settings loaded from environment variables."""

    app_name: str = Field(default="access-control-service")
    app_env: str = Field(default="development")
    debug: bool = Field(default=True)
    secret_key: str = Field(default="default-secret-key")
    openai_api_key: SecretStr = Field(default=SecretStr(""))
    llm_model: str = Field(default="gpt-4o-mini")
    llm_temperature: float = Field(default=0.1)
    llm_max_tokens: int = Field(default=2048)

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


__all__ = ["Settings", "get_settings"]
