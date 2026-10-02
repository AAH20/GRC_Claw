"""Application configuration loaded from environment variables and config.yaml."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentConfig(BaseModel):
    """Per-agent feature flags and tuning parameters."""

    enabled: bool = True


class ContentCreationConfig(AgentConfig):
    """Content Creation agent settings."""

    default_language: str = "en"
    max_lessons_per_course: int = Field(default=30, ge=1, le=100)
    max_quiz_questions_per_lesson: int = Field(default=10, ge=1, le=50)


class DeliveryConfig(AgentConfig):
    """Delivery agent settings."""

    default_lms: str = Field(default="canvas", pattern="^(canvas|moodle|scorm)$")
    publish_draft: bool = False
    retry_attempts: int = Field(default=3, ge=1, le=10)


class AssessmentConfig(AgentConfig):
    """Assessment agent settings."""

    mastery_threshold: float = Field(default=0.75, ge=0.0, le=1.0)
    passing_score: float = Field(default=0.70, ge=0.0, le=1.0)
    max_grading_retries: int = Field(default=3, ge=1, le=10)


class OptimizationConfig(AgentConfig):
    """Optimization agent settings."""

    min_feedback_samples: int = Field(default=20, ge=1)
    auto_apply: bool = False


class PerformanceAnalyticsConfig(AgentConfig):
    """Performance Analytics agent settings."""

    default_lookback_days: int = Field(default=30, ge=1, le=365)
    alert_completion_threshold: float = Field(default=0.40, ge=0.0, le=1.0)


class CanvasConfig(BaseModel):
    """Canvas LMS integration settings."""

    enabled: bool = True
    base_url: str = "https://canvas.instructure.com/api/v1"
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    page_size: int = Field(default=100, ge=1, le=500)


class MoodleConfig(BaseModel):
    """Moodle LMS integration settings."""

    enabled: bool = True
    base_url: str = "https://moodle.example.com"
    webservice_endpoint: str = "/webservice/rest/server.php"
    timeout_seconds: int = Field(default=30, ge=1, le=300)


class ScormConfig(BaseModel):
    """SCORM packaging/validation settings."""

    enabled: bool = True
    version: str = Field(default="2004", pattern="^(1\\.2|2004)$")
    strict_mode: bool = False


class ObservabilityConfig(BaseModel):
    """Observability and metrics settings."""

    prometheus_enabled: bool = True
    metrics_path: str = "/metrics"
    health_path: str = "/health"
    structured_logging: bool = True
    sentry_dsn: str | None = None


class Settings(BaseSettings):
    """Top-level application settings.

    Values are resolved from (in order of precedence):
      1. Environment variables
      2. ``.env`` file (if present)
      3. ``config/config.yaml`` (for non-secret defaults)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # Application
    app_env: str = Field(default="development",
        pattern="^(development|staging|production)$")
    log_level: str = Field(default="info",
        pattern="^(debug|info|warning|error|critical)$")
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=2, ge=1, le=16)
    request_timeout_seconds: int = Field(default=60, ge=1, le=600)
    cors_origins: list[str] = Field(default_factory=lambda: ["https://grc.local"])

    # Models
    openai_api_key: str = Field(default="", min_length=0)
    openai_model: str = "gpt-4o-mini"
    model_temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    model_max_tokens: int = Field(default=4096, ge=1, le=32768)
    deepagents_max_iterations: int = Field(default=25, ge=1, le=100)

    # Agents
    content_creation: ContentCreationConfig = Field(
        default_factory=ContentCreationConfig
    )
    delivery: DeliveryConfig = Field(default_factory=DeliveryConfig)
    assessment: AssessmentConfig = Field(default_factory=AssessmentConfig)
    optimization: OptimizationConfig = Field(default_factory=OptimizationConfig)
    performance_analytics: PerformanceAnalyticsConfig = Field(
        default_factory=PerformanceAnalyticsConfig
    )

    # LMS integrations
    canvas: CanvasConfig = Field(default_factory=CanvasConfig)
    moodle: MoodleConfig = Field(default_factory=MoodleConfig)
    scorm: ScormConfig = Field(default_factory=ScormConfig)

    # Observability
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, v: Any) -> Any:
        """Allow CORS origins to be provided as a comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


def _load_yaml_defaults() -> dict[str, Any]:
    """Load non-secret defaults from config/config.yaml if it exists."""
    config_path = Path(__file__).resolve().parents[3] / "config" / "config.yaml"
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    # Only pull non-secret sections; secrets come from env vars.
    return {
        key: value
        for key, value in data.items()
        if key not in {"openai_api_key", "canvas", "moodle"}
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    yaml_defaults = _load_yaml_defaults()
    return Settings(**yaml_defaults)
