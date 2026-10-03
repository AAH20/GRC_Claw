"""Main application module for UGC Marketplace."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ugc_marketplace import __version__
from ugc_marketplace.api.community_curation import router as curation_router
from ugc_marketplace.api.content_discovery import router as discovery_router
from ugc_marketplace.api.content_marketplace import \
    router as marketplace_router
from ugc_marketplace.api.content_moderation import router as moderation_router
from ugc_marketplace.api.creator_analytics import router as analytics_router
from ugc_marketplace.api.creator_monetization import \
    router as monetization_router
from ugc_marketplace.api.fraud_detection import router as fraud_router
from ugc_marketplace.api.health import router as health_router
from ugc_marketplace.api.licensing_engine import router as licensing_router
from ugc_marketplace.api.quality_scoring import router as quality_router
from ugc_marketplace.api.rights_management import router as rights_router
from ugc_marketplace.config import get_settings
from ugc_marketplace.config.logging_config import configure_logging

logger = structlog.get_logger(__name__)


def setup_logging() -> None:
    """Configure structured logging for the application."""
    settings = get_settings()
    configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Args:
        app: The FastAPI application instance.
    """
    settings = get_settings()
    setup_logging()
    logger.info(
        "Starting UGC Marketplace",
        version=__version__,
        environment=settings.app_env,
    )
    yield
    logger.info("Shutting down UGC Marketplace")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title="UGC Marketplace",
        description="Unified agentic AI platform for content marketplace operations",
        version=__version__,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_hosts,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle uncaught exceptions.

        Args:
            request: The incoming request.
            exc: The exception that was raised.

        Returns:
            JSON response with error details.
        """
        logger.error(
            "Unhandled exception",
            error=str(exc),
            path=request.url.path,
            method=request.method,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    api_prefix = settings.api_prefix

    app.include_router(health_router, prefix=api_prefix, tags=["Health"])
    app.include_router(
        moderation_router, prefix=f"{api_prefix}/moderation", tags=["Moderation"]
    )
    app.include_router(
        monetization_router, prefix=f"{api_prefix}/monetization", tags=["Monetization"]
    )
    app.include_router(
        discovery_router, prefix=f"{api_prefix}/discovery", tags=["Discovery"]
    )
    app.include_router(rights_router, prefix=f"{api_prefix}/rights", tags=["Rights"])
    app.include_router(quality_router, prefix=f"{api_prefix}/quality", tags=["Quality"])
    app.include_router(fraud_router, prefix=f"{api_prefix}/fraud", tags=["Fraud"])
    app.include_router(
        analytics_router, prefix=f"{api_prefix}/analytics", tags=["Analytics"]
    )
    app.include_router(
        licensing_router, prefix=f"{api_prefix}/licensing", tags=["Licensing"]
    )
    app.include_router(
        curation_router, prefix=f"{api_prefix}/curation", tags=["Curation"]
    )
    app.include_router(
        marketplace_router, prefix=f"{api_prefix}/marketplace", tags=["Marketplace"]
    )

    return app


app = create_app()


def run() -> None:
    """Run the application using uvicorn."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "ugc_marketplace.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
