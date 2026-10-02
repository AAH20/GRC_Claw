"""Main application entry point for Recruitment Analytics API."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from recruitment_analytics.api.router import api_router
from recruitment_analytics.config.settings import Settings, get_settings
from recruitment_analytics.models.exceptions import RecruitmentAnalyticsError
from recruitment_analytics.models.schemas import ErrorResponse


def setup_logging(settings: Settings) -> None:
    """Configure structured logging for the application."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(message)s",
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.log_level)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    settings = get_settings()
    setup_logging(settings)
    logger = structlog.get_logger()
    logger.info(
        "application_starting",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )
    yield
    logger.info("application_shutting_down")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Application factory for creating FastAPI instance.

    Args:
        settings: Optional settings override for testing.

    Returns:
        Configured FastAPI application instance.
    """
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title="Recruitment Analytics API",
        description=(
            "Agentic AI-powered recruitment analytics platform with funnel analysis, "
            "source tracking, and predictive hiring"
        ),
        version=settings.app_version,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
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

    # Exception handlers
    @app.exception_handler(RecruitmentAnalyticsError)
    async def recruitment_error_handler(
        request: Request, exc: RecruitmentAnalyticsError
    ) -> JSONResponse:
        """Handle custom recruitment analytics errors."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error=exc.code,
                detail=exc.message,
                code=exc.code,
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected errors."""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="INTERNAL_ERROR",
                detail=str(exc),
                code="INTERNAL_ERROR",
            ).model_dump(),
        )

    # Include routers
    app.include_router(api_router)

    return app


app = create_app()


def run() -> None:
    """Run the application with uvicorn."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "recruitment_analytics.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
