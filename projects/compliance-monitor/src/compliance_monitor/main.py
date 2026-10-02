"""FastAPI application factory for Compliance Monitor."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from compliance_monitor.api.routes import audits, policies, remediation, scores, violations
from compliance_monitor.config.settings import get_settings

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown events."""
    settings = get_settings()
    logger.info("Starting compliance monitor", env=settings.app_env, debug=settings.debug)
    yield
    logger.info("Shutting down compliance monitor")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title="Compliance Monitor",
        description="Agentic AI compliance monitoring with policy tracking, violation detection, and audit reporting",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions globally."""
        logger.error("Unhandled exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error", "error": str(exc)},
        )

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "service": "compliance-monitor"}

    # API routes
    app.include_router(policies.router, prefix="/api/v1/policies", tags=["policies"])
    app.include_router(violations.router, prefix="/api/v1/violations", tags=["violations"])
    app.include_router(audits.router, prefix="/api/v1/audits", tags=["audits"])
    app.include_router(scores.router, prefix="/api/v1/scores", tags=["scores"])
    app.include_router(remediation.router, prefix="/api/v1", tags=["remediation"])

    return app


app = create_app()
