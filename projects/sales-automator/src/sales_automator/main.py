"""FastAPI application entry point for Sales Automator."""

from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from sales_automator.api import prospects, sequences
from sales_automator.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    """Manage application lifecycle."""
    logger.info("Starting Sales Automator", version=app.version)
    yield
    logger.info("Shutting down Sales Automator")


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="Sales Automator",
        description="Agentic AI sales automation platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(prospects.router, prefix="/api/v1")
    app.include_router(sequences.router, prefix="/api/v1")

    # Health check
    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "healthy", "version": app.version}

    # Prometheus metrics
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    return app


app = create_app()


def main() -> None:
    """Run the application with uvicorn."""
    import uvicorn

    uvicorn.run(
        "sales_automator.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
