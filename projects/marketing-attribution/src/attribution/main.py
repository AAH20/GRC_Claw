"""FastAPI application entry point for the Marketing Attribution platform."""

from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from attribution.api.attribution import router as attribution_router
from attribution.api.reports import router as reports_router

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    """Manage application lifecycle events."""
    logger.info("Starting Marketing Attribution API", version="0.1.0")
    yield
    logger.info("Shutting down Marketing Attribution API")


app = FastAPI(
    title="Marketing Attribution API",
    description=(
        "Agentic AI marketing attribution platform with multi-touch attribution, "
        "predictive analytics, and real-time dashboards."
    ),
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
app.include_router(reports_router, prefix="/api/v1/reports", tags=["reports"])


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


def main() -> None:
    """Run the application with uvicorn."""
    import uvicorn

    uvicorn.run(
        "attribution.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
