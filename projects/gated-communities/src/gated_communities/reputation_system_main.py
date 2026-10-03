"""Main application entry point for the reputation system."""

import logging
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from reputation_system.api.routes import api_router
from reputation_system.config.settings import Settings, get_settings
from reputation_system.integrations.langchain_client import LangChainClient

logger = structlog.get_logger()


def setup_logging(settings: Settings) -> None:
    """Configure structured logging.

    Args:
        settings: Application settings.
    """
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format="%(message)s",
    )
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            (
                structlog.processors.JSONRenderer()
                if settings.LOG_FORMAT == "json"
                else structlog.dev.ConsoleRenderer()
            ),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL.upper())
        ),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Args:
        app: FastAPI application instance.
    """
    settings = get_settings()
    setup_logging(settings)

    # Initialize integrations
    langchain_client = LangChainClient(settings)
    await langchain_client.initialize()
    app.state.langchain_client = langchain_client

    logger.info("Application starting", env=settings.APP_ENV)
    yield
    logger.info("Application shutting down")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Optional settings override for testing.

    Returns:
        Configured FastAPI application.
    """
    app_settings = settings or get_settings()

    app = FastAPI(
        title="Reputation System API",
        description="Agentic AI reputation management system with scoring, badges, and trust tiers",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router)

    # Exception handlers
    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle uncaught exceptions.

        Args:
            request: Incoming request.
            exc: Exception that was raised.

        Returns:
            JSON error response.
        """
        logger.error("Unhandled exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal server error", "detail": str(exc)},
        )

    return app


app = create_app()


def main() -> None:
    """Run the application with uvicorn."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "reputation_system.main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS,
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    main()
