"""Application settings using pydantic-settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via environment variables prefixed with
    ``CANDIDATE_MATCHER_`` (e.g. ``CANDIDATE_MATCHER_DEBUG=true``).
    """

    model_config = SettingsConfigDict(
        env_prefix="CANDIDATE_MATCHER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "candidate-matcher"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    # LLM Configuration
    llm_provider: Literal["openai", "anthropic", "mock"] = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096
    openai_api_key: str = Field(default="", repr=False)

    # Embedding Configuration
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Matching Configuration
    semantic_similarity_threshold: float = 0.7
    skills_gap_threshold: float = 0.5
    bias_penalty_factor: float = 0.15
    max_candidates_per_request: int = 100
    default_top_k: int = 10

    # Vector Store
    vector_store_url: str = "http://localhost:6333"
    vector_store_collection: str = "candidate_embeddings"

    # Cache
    cache_ttl_seconds: int = 3600
    redis_url: str = "redis://localhost:6379/0"

    # Observability
    enable_metrics: bool = True
    enable_tracing: bool = False
    jaeger_endpoint: str = "http://localhost:14268/api/traces"

    @field_validator("llm_temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Ensure temperature is within valid range."""
        if not 0.0 <= v <= 2.0:
            raise ValueError("llm_temperature must be between 0.0 and 2.0")
        return v

    @field_validator("semantic_similarity_threshold", "skills_gap_threshold")
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        """Ensure thresholds are between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("threshold must be between 0.0 and 1.0")
        return v

    @field_validator("max_candidates_per_request")
    @classmethod
    def validate_max_candidates(cls, v: int) -> int:
        """Ensure max candidates is positive."""
        if v < 1:
            raise ValueError("max_candidates_per_request must be at least 1")
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: The application settings singleton.
    """
    return Settings()
