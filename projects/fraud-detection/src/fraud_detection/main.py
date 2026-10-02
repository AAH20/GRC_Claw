"""Fraud Detection FastAPI application."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from fraud_detection.api.routes import accounts, agents, analysis, health, monitoring, reports
from fraud_detection.config.logging_config import configure_logging, get_logger
from fraud_detection.config.settings import get_settings
from fraud_detection.integrations.database import close_db, init_db
from fraud_detection.integrations.kafka_producer import close_kafka
from fraud_detection.integrations.redis_client import close_redis

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Args:
        app: FastAPI application instance.
    """
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("Starting fraud detection service", env=settings.app_env)

    await init_db()

    yield

    await close_db()
    await close_redis()
    await close_kafka()
    logger.info("Fraud detection service stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="Fraud Detection API",
        description="Agentic AI fraud detection system with pattern detection, anomaly detection, and risk scoring",  # noqa: E501
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Include routers
    app.include_router(health.router)
    app.include_router(analysis.router)
    app.include_router(reports.router)
    app.include_router(accounts.router)
    app.include_router(monitoring.router)
    app.include_router(agents.router)

    return app


def main() -> None:
    """Run the application with uvicorn."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "fraud_detection.main:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
