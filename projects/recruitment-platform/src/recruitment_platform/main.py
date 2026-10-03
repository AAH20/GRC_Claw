"""Application entry point for the unified Recruitment Platform."""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from recruitment_platform.api.router import api_router
from recruitment_platform.config.settings import get_settings

settings = get_settings()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Unified Recruitment Platform - AI-powered recruitment automation",
        docs_url="/docs",
        redoc_url="/redoc",
    )
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
