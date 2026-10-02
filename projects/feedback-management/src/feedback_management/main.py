"""FastAPI application entry point for the Feedback Management system."""

import os
from contextlib import asynccontextmanager

import structlog
import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings, SettingsConfigDict

from feedback_management.api.feedback import router as feedback_router
from feedback_management.api.surveys import router as surveys_router

logger = structlog.get_logger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "feedback-management"
    app_version: str = "0.1.0"
    app_env: str = "development"
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000
    openai_api_key: str = ""
    openai_model: str = "gpt-4"
    openai_max_tokens: int = 500
    openai_temperature: float = 0.7
    langchain_api_key: str = ""
    langchain_tracing_v2: bool = True
    langchain_project: str = "feedback-management"
    surveymonkey_api_key: str = ""
    surveymonkey_client_id: str = ""
    surveymonkey_client_secret: str = ""
    typeform_api_key: str = ""
    typeform_workspace_id: str = ""
    google_forms_credentials_path: str = "./config/google-credentials.json"
    google_forms_token_path: str = "./config/google-token.json"
    database_url: str = "sqlite:///./feedback.db"
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 3600
    sentry_dsn: str = ""
    prometheus_port: int = 9090
    webhook_secret: str = ""
    slack_webhook_url: str = ""


def load_yaml_config(config_path: str = "config/config.yaml") -> dict:
    """Load YAML configuration file.

    Args:
        config_path: Path to the YAML config file.

    Returns:
        Dictionary containing the configuration.
    """
    if os.path.exists(config_path):
        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


settings = Settings()
yaml_config = load_yaml_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    logger.info(
        "Starting Feedback Management service",
        version=settings.app_version,
        env=settings.app_env,
    )
    yield
    logger.info("Shutting down Feedback Management service")


app = FastAPI(
    title="Feedback Management API",
    description="Agentic AI-powered feedback collection, analysis, and response system",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(feedback_router, prefix="/api/v1/feedback", tags=["feedback"])
app.include_router(surveys_router, prefix="/api/v1/surveys", tags=["surveys"])


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Dictionary with status and version information.
    """
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.app_env,
    }


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    """Root endpoint with API information.

    Returns:
        Basic API information.
    """
    return {
        "name": "Feedback Management API",
        "version": settings.app_version,
        "docs": "/docs",
    }


def main() -> None:
    """Run the application with uvicorn."""
    import uvicorn

    uvicorn.run(
        "feedback_management.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.app_env == "development",
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
