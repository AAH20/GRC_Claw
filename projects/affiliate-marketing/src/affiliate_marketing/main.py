"""FastAPI application entry point for the Affiliate Marketing Platform."""

from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from affiliate_marketing.api import commissions, partners
from affiliate_marketing.core.config import get_settings
from affiliate_marketing.core.logging import configure_logging

logger = structlog.get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    """Application lifespan manager for startup/shutdown events."""
    configure_logging()
    logger.info("Starting Affiliate Marketing Platform", version=settings.app_version)
    yield
    logger.info("Shutting down Affiliate Marketing Platform")


app = FastAPI(
    title="Affiliate Marketing Platform",
    description="Modularized agentic AI affiliate marketing platform",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(partners.router, prefix="/partners", tags=["partners"])
app.include_router(commissions.router, prefix="/commissions", tags=["commissions"])


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.app_version}


def main() -> None:
    """Run the application with uvicorn."""
    import uvicorn

    uvicorn.run(
        "affiliate_marketing.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
