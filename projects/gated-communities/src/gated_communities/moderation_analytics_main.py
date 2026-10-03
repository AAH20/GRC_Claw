"""Main application entry point for moderation analytics service."""

from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from moderation_analytics.api import router
from moderation_analytics.config import get_settings
from moderation_analytics.exceptions import ModerationAnalyticsError
from moderation_analytics.models import ErrorResponse

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Args:
        app: FastAPI application instance.
    """
    settings = get_settings()
    logger.info(
        "Starting moderation analytics service",
        version=settings.app_version,
        environment=settings.environment,
    )
    yield
    logger.info("Shutting down moderation analytics service")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title="Moderation Analytics API",
        description="Agentic AI-powered moderation analytics service",
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(router)

    # Exception handlers
    @app.exception_handler(ModerationAnalyticsError)
    async def moderation_analytics_exception_handler(
        request: Request, exc: ModerationAnalyticsError
    ) -> JSONResponse:
        """Handle custom moderation analytics errors.

        Args:
            request: Incoming request.
            exc: The exception that occurred.

        Returns:
            JSONResponse: Error response.
        """
        logger.error(
            "Moderation analytics error",
            error=exc.message,
            details=exc.details,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error=type(exc).__name__,
                message=exc.message,
                details=exc.details,
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle general exceptions.

        Args:
            request: Incoming request.
            exc: The exception that occurred.

        Returns:
            JSONResponse: Error response.
        """
        logger.error(
            "Unhandled exception",
            error=str(exc),
            error_type=type(exc).__name__,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="InternalServerError",
                message="An unexpected error occurred",
            ).model_dump(),
        )

    return app


def main() -> None:
    """Main entry point for running the application."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "moderation_analytics.main:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
