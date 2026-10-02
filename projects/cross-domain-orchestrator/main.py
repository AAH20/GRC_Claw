"""Cross-Domain Orchestrator — FastAPI application entry point.

This module provides the ``create_app`` factory function used to build
and configure the FastAPI application instance.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.routers import agents, analytics, domains, health, workflows

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager.

    Handles startup and shutdown events for the application.
    """
    settings = get_settings()
    logger.info(
        "Starting Cross-Domain Orchestrator (env=%s, debug=%s)",
        settings.environment,
        settings.debug,
    )
    yield
    logger.info("Shutting down Cross-Domain Orchestrator")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Optional settings override. If not provided, settings
            are loaded from environment variables.

    Returns:
        Configured FastAPI application instance.
    """
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title="Cross-Domain Orchestrator",
        description=(
            "Orchestrates agents across multiple domains, routing requests, "
            "executing workflows, aggregating results, and collecting analytics."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["Workflows"])
    app.include_router(domains.router, prefix="/api/v1/domains", tags=["Domains"])
    app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
    app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])

    return app


app = create_app()
