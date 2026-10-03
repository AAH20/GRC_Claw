"""Member Verification Service - Main application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from member_verification.api.routes import agents, documents, fraud, health, trust, verification
from member_verification.config.logging_config import configure_logging, get_logger
from member_verification.config.settings import get_settings
from member_verification.models.schemas import ErrorResponse

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Args:
        app: The FastAPI application instance.
    """
    settings = get_settings()
    configure_logging(
        log_level=settings.log_level,
        json_format=settings.environment == "production",
    )
    logger.info(
        "Starting member verification service",
        version=settings.app_version,
        environment=settings.environment,
    )
    yield
    logger.info("Shutting down member verification service")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title="Member Verification Service",
        description=(
            "AI-powered community member verification with identity verification, "
            "trust scoring, and fraud prevention"
        ),
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
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
    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle uncaught exceptions.

        Args:
            request: The incoming request.
            exc: The exception that was raised.

        Returns:
            JSON error response.
        """
        logger.error(
            "Unhandled exception",
            error=str(exc),
            path=request.url.path,
            method=request.method,
        )
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="internal_server_error",
                message="An unexpected error occurred",
            ).model_dump(),
        )

    # Include routers
    app.include_router(health.router)
    app.include_router(verification.router)
    app.include_router(agents.router)
    app.include_router(trust.router)
    app.include_router(fraud.router)
    app.include_router(documents.router)

    return app


def main() -> None:
    """Run the application with uvicorn."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "member_verification.main:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
