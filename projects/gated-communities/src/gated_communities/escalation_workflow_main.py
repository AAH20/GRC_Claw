"""Main application entry point for escalation workflow service."""

from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from escalation_workflow.api import (
    escalations_router,
    health_router,
    priorities_router,
    resolutions_router,
    sla_router,
)
from escalation_workflow.config import get_settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events.

    Args:
        app: The FastAPI application instance.
    """
    settings = get_settings()
    logger.info(
        "Starting escalation workflow service",
        version=settings.app_version,
        environment=settings.environment,
    )
    yield
    logger.info("Shutting down escalation workflow service")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title="Escalation Workflow API",
        description=(
            "Agentic AI escalation workflow management with priority routing, "
            "SLA tracking, and resolution optimization"
        ),
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health_router)
    app.include_router(escalations_router)
    app.include_router(priorities_router)
    app.include_router(sla_router)
    app.include_router(resolutions_router)

    return app


app = create_app()


def main() -> None:
    """Run the application using uvicorn."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "escalation_workflow.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
