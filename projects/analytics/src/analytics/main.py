"""FastAPI application entry point for the Analytics & Attribution platform."""

from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from analytics.api.attribution import router as attribution_router
from analytics.api.forecasting import router as forecasting_router

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    logger.info("Starting Analytics & Attribution platform")
    yield
    logger.info("Shutting down Analytics & Attribution platform")


app = FastAPI(
    title="Analytics & Attribution",
    description="Modular agentic AI marketing analytics and attribution platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(attribution_router, prefix="/api/v1/attribution", tags=["attribution"])
app.include_router(forecasting_router, prefix="/api/v1/forecasting", tags=["forecasting"])


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


def main() -> None:
    """Run the application with uvicorn."""
    import uvicorn

    uvicorn.run(
        "analytics.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=1,
    )


if __name__ == "__main__":
    main()
