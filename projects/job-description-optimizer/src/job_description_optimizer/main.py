"""FastAPI application factory for the job description optimizer."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from job_description_optimizer.api.routes import router
from job_description_optimizer.config import Settings, get_settings
from job_description_optimizer.models import ErrorResponse

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles startup and shutdown events for the application.

    Args:
        app: FastAPI application instance.
    """
    settings = get_settings()
    logger.info(
        "Starting job description optimizer",
        app_name=settings.app_name,
        env=settings.app_env,
        debug=settings.debug,
    )
    yield
    logger.info("Shutting down job description optimizer")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    This is the application factory pattern used for creating
    the FastAPI app instance with all configurations.

    Args:
        settings: Optional settings override for testing.

    Returns:
        Configured FastAPI application instance.
    """
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title="Job Description Optimizer",
        description=(
            "Agentic AI-powered job description optimizer with bias removal, "
            "SEO, and ATS compatibility"
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle all unhandled exceptions.

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
            content=ErrorResponse(
                error="Internal server error",
                detail=str(exc) if settings.debug else None,
            ).model_dump(),
        )

    # Include routers
    app.include_router(router, prefix="/api/v1")

    return app


def main() -> None:
    """Entry point for running the application with uvicorn."""
    import uvicorn

    settings = get_settings()
    uvicorn.create_app = create_app  # type: ignore[attr-defined]
    uvicorn.run(
        "job_description_optimizer.main:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
