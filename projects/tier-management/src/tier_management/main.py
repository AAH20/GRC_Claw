"""Main application entry point for the tier management service.

Creates and configures the FastAPI application with all routes,
middleware, exception handlers, and agent initialization.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from tier_management.api.routes import router
from tier_management.config.logging_config import get_logger, setup_logging
from tier_management.config.settings import get_settings
from tier_management.exceptions import TierManagementError

# Setup logging on module import
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Handles startup and shutdown events including agent initialization
    and resource cleanup.

    Args:
        app: The FastAPI application instance.
    """
    settings = get_settings()
    logger.info(
        "application_starting",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )

    # Initialize agents
    from tier_management.agents import (
        AccessControllerAgent,
        BenefitManagerAgent,
        TierAnalyticsAgent,
        TierEvaluatorAgent,
        UpgradeRecommenderAgent,
    )

    agents = [
        TierEvaluatorAgent(),
        UpgradeRecommenderAgent(),
        AccessControllerAgent(),
        BenefitManagerAgent(),
        TierAnalyticsAgent(),
    ]

    for agent in agents:
        await agent.initialize()

    logger.info("agents_initialized", count=len(agents))

    yield

    # Cleanup
    logger.info("application_shutting_down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title="Tier Management Service",
        description="Multi-tier gated community access management with agentic AI",
        version=settings.app_version,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_hosts,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    @app.exception_handler(TierManagementError)
    async def tier_management_exception_handler(
        request: Request,
        exc: TierManagementError,
    ) -> JSONResponse:
        """Handle custom tier management exceptions.

        Args:
            request: The incoming request.
            exc: The raised exception.

        Returns:
            JSON response with error details.
        """
        logger.error(
            "request_error",
            error=exc.message,
            status_code=exc.status_code,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Handle uncaught exceptions.

        Args:
            request: The incoming request.
            exc: The raised exception.

        Returns:
            JSON response with generic error.
        """
        logger.error(
            "unhandled_exception",
            error=str(exc),
            path=request.url.path,
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "detail": str(exc) if settings.debug else None,
            },
        )

    # Include routers
    from tier_management.api.routes.health import health_router
    app.include_router(health_router)
    app.include_router(router, prefix="/api/v1")

    # Root endpoint
    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint with service info.

        Returns:
            Service information dictionary.
        """
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "docs": "/docs",
        }

    return app


# Create the application instance
app = create_app()


def main() -> None:
    """Run the application using Uvicorn."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "tier_management.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
