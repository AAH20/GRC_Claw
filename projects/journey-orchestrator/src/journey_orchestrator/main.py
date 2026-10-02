"""FastAPI application entry point for the Journey Orchestrator."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from journey_orchestrator.api import analytics, events, journeys, optimization, segments
from journey_orchestrator.config import get_settings

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = structlog.get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown events."""
    logger.info("Starting Journey Orchestrator", version="0.1.0")
    yield
    logger.info("Shutting down Journey Orchestrator")


app = FastAPI(
    title="Journey Orchestrator",
    description="Agentic Customer Journey Orchestration platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include routers
app.include_router(journeys.router, prefix="/api/v1/journeys", tags=["journeys"])
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
app.include_router(segments.router, prefix="/api/v1/segments", tags=["segments"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(optimization.router, prefix="/api/v1/optimization", tags=["optimization"])


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


def main() -> None:
    """Run the application with uvicorn."""
    import uvicorn

    uvicorn.run(
        "journey_orchestrator.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
    )


if __name__ == "__main__":
    main()
