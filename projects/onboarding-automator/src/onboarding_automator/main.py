"""Main FastAPI application module.

Provides the ``create_app`` factory function that wires together the
configuration, agents, integrations and API routes for the onboarding
automator service.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

from contextlib import asynccontextmanager

from fastapi import FastAPI

from onboarding_automator.api.router import api_router
from onboarding_automator.config.settings import get_settings
from onboarding_automator.integrations.manager import IntegrationManager
from onboarding_automator.integrations.store import InMemoryStore

__all__ = ["create_app", "run"]

__version__ = "0.1.0"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown events."""
    settings = get_settings()
    app.state.settings = settings
    app.state.store = InMemoryStore()
    app.state.integration_manager = IntegrationManager(settings)
    yield
    await app.state.integration_manager.close()
    await app.state.store.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        A fully configured FastAPI application instance with all routes
        and middleware registered.
    """
    settings = get_settings()

    app = FastAPI(
        title="Onboarding Automator",
        description="Agentic AI-powered employee onboarding automation service",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
    )

    # Register API routes
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()


def run() -> None:
    """Entry-point for running the application with Uvicorn."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "onboarding_automator.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
