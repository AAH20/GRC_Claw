"""Application settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MODQ_", env_file=".env")

    app_name: str = "moderation-queue"
    debug: bool = False

    # LLM
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.1

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Moderation thresholds
    auto_approve_threshold: float = 0.85
    auto_reject_threshold: float = 0.15
    human_review_threshold: float = 0.50

    # Queue
    max_queue_size: int = 10_000
    default_priority: int = 5
    priority_scale: int = 10

    # API
    host: str = "0.0.0.0"
    port: int = 8000


@lru_cache
def get_settings() -> Settings:
    return Settings()
