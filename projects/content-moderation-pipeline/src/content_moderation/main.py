"""FastAPI application factory for the content moderation pipeline."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from content_moderation.api.routes import appeals, health, moderation, policies
from content_moderation.config.settings import get_settings

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown events."""
    settings = get_settings()
    logger.info(
        "Starting content moderation pipeline",
        environment=settings.app_env,
        log_level=settings.log_level,
    )
    yield
    logger.info("Shutting down content moderation pipeline")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title="Content Moderation Pipeline",
        description="Agentic AI content moderation with multi-modal analysis",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.app_env == "development" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions globally."""
        logger.error(
            "Unhandled exception",
            error=str(exc),
            path=request.url.path,
            method=request.method,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error", "error_id": str(id(exc))},
        )

    app.include_router(health.router, tags=["Health"])
    app.include_router(moderation.router, prefix="/api/v1", tags=["Moderation"])
    app.include_router(policies.router, prefix="/api/v1", tags=["Policies"])
    app.include_router(appeals.router, prefix="/api/v1", tags=["Appeals"])

    return app


app = create_app()
