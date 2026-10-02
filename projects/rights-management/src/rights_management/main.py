"""Application factory for the rights-management service."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from rights_management.api.routes import (
    infringement,
    licenses,
    takedown,
    usage,
    validation,
)
from rights_management.config.settings import get_settings
from rights_management.integrations.storage import InMemoryStorage


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle resources."""
    settings = get_settings()
    storage = InMemoryStorage()
    app.state.storage = storage
    app.state.settings = settings
    yield
    await storage.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        A fully configured FastAPI application instance.
    """
    settings = get_settings()
    app = FastAPI(
        title="Rights Management Service",
        description=(
            "Agentic AI content rights management with license detection, "
            "usage tracking, and infringement detection."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(licenses.router, prefix="/api/v1/licenses", tags=["licenses"])
    app.include_router(usage.router, prefix="/api/v1/usage", tags=["usage"])
    app.include_router(infringement.router, prefix="/api/v1/infringement", tags=["infringement"])
    app.include_router(validation.router, prefix="/api/v1/validation", tags=["validation"])
    app.include_router(takedown.router, prefix="/api/v1/takedown", tags=["takedown"])

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok"}

    return app


app = create_app()
