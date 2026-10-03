"""Application configuration and settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="community-health-scorer")
    app_version: str = Field(default="0.1.0")
    debug: bool = Field(default=False)
    environment: str = Field(default="development")

    # Server
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)
    workers: int = Field(default=1)

    # LLM
    openai_api_key: str = Field(default="")
    llm_model: str = Field(default="gpt-4o-mini")
    llm_temperature: float = Field(default=0.1)
    llm_max_tokens: int = Field(default=2048)

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_ttl: int = Field(default=3600)

    # Scoring
    engagement_weight: float = Field(default=0.30)
    toxicity_weight: float = Field(default=0.25)
    growth_weight: float = Field(default=0.25)
    churn_weight: float = Field(default=0.20)

    # Rate Limiting
    rate_limit_requests: int = Field(default=100)
    rate_limit_window: int = Field(default=60)

    # Observability
    log_level: str = Field(default="INFO")
    enable_metrics: bool = Field(default=True)
    enable_tracing: bool = Field(default=False)

    @field_validator(
        "engagement_weight", "toxicity_weight", "growth_weight", "churn_weight"
    )
    @classmethod
    def validate_weight(cls, v: float) -> float:
        """Validate that weights are between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Weight must be between 0.0 and 1.0, got {v}")
        return v

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}, got {v}")
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def weights_sum(self) -> float:
        """Sum of all scoring weights."""
        return (
            self.engagement_weight
            + self.toxicity_weight
            + self.growth_weight
            + self.churn_weight
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
