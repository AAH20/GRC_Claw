"""Main application entry point for resume-parser service."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from resume_parser.api.routes import router
from resume_parser.config import Settings, get_settings
from resume_parser.integrations import create_llm_client
from resume_parser.integrations.storage import create_storage
from resume_parser.utils.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Args:
        app: FastAPI application instance.
    """
    settings: Settings = app.state.settings

    # Setup logging
    setup_logging(
        log_level=settings.log_level,
        json_format=settings.is_production,
    )

    logger.info(
        "application_starting",
        app_name=settings.app_name,
        env=settings.app_env,
        version="0.1.0",
    )

    # Initialize LLM client
    app.state.llm_client = create_llm_client(settings)

    # Initialize storage
    app.state.storage = create_storage(
        backend=settings.storage_backend,
        path=settings.storage_path,
    )

    # Ensure upload directory exists
    settings.upload_dir.mkdir(parents=True, exist_ok=True)

    logger.info("application_ready")

    yield

    logger.info("application_shutting_down")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Optional settings override. If not provided, uses get_settings().

    Returns:
        FastAPI: Configured FastAPI application.
    """
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title="Resume Parser API",
        description="Agentic AI resume parsing service using LangChain DeepAgents",
        version="0.1.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # Store settings in app state
    app.state.settings = settings

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API router
    app.include_router(router, prefix=settings.api_v1_prefix)

    # Root endpoint
    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint.

        Returns:
            dict[str, str]: Service info.
        """
        return {
            "service": "resume-parser",
            "version": "0.1.0",
            "docs": "/docs",
        }

    return app


def main() -> None:
    """Run the application with uvicorn."""
    import uvicorn

    settings = get_settings()
    setup_logging(
        log_level=settings.log_level,
        json_format=settings.is_production,
    )

    uvicorn.run(
        "resume_parser.main:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
