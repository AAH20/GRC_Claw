"""Application configuration using pydantic-settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Service
    app_name: str = Field(default="community-curation", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Deployment environment")

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=1, description="Number of worker processes")

    # LLM
    openai_api_key: str = Field(default="", description="OpenAI API key")
    llm_model: str = Field(default="gpt-4o-mini", description="LLM model name")
    llm_temperature: float = Field(default=0.1, description="LLM temperature")
    llm_max_tokens: int = Field(default=2048, description="Max tokens for LLM responses")

    # Agents
    ranking_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "engagement": 0.35,
            "recency": 0.25,
            "quality": 0.25,
            "relevance": 0.15,
        },
        description="Weights for content ranking algorithm",
    )
    trend_lookback_hours: int = Field(default=72, description="Hours to look back for trends")
    quality_threshold: float = Field(default=0.6, description="Minimum quality score threshold")
    max_cluster_count: int = Field(default=10, description="Maximum number of topic clusters")

    # External APIs
    reddit_api_url: str = Field(default="https://www.reddit.com", description="Reddit API base URL")
    hackernews_api_url: str = Field(
        default="https://hacker-news.firebaseio.com", description="Hacker News API base URL"
    )
    twitter_api_url: str = Field(default="https://api.twitter.com", description="Twitter API base URL")

    # Rate limiting
    rate_limit_requests: int = Field(default=100, description="Requests per minute per client")
    rate_limit_window: int = Field(default=60, description="Rate limit window in seconds")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.

    Returns:
        Settings: Application settings instance.
    """
    return Settings()
