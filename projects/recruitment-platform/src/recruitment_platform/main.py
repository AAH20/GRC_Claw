"""Application entry point for the unified Recruitment Platform."""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from recruitment_platform.api.router import api_router
from recruitment_platform.config.settings import get_settings
from recruitment_platform.config.logging_config import configure_logging
from recruitment_platform.monitoring.metrics import MetricsMiddleware
from recruitment_platform.monitoring.tracing import setup_tracing
from recruitment_platform.security.middleware import SecurityHeadersMiddleware, RequestIDMiddleware

settings = get_settings()
configure_logging(settings.log_level, settings.log_format)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    setup_tracing(service_name="recruitment-platform")
    yield
    # Shutdown
    pass


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Unified Recruitment Platform - AI-powered recruitment automation",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Security middleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(MetricsMiddleware)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_hosts,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Trusted hosts
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

    # Include API routes
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()


def main() -> None:
    """Run the application server."""
    uvicorn.run(
        "recruitment_platform.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=settings.workers,
    )


if __name__ == "__main__":
    main()
