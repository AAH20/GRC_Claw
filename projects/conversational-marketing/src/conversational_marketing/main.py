"""FastAPI application entry point for the Conversational Marketing platform."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from conversational_marketing.api import conversations, leads
from conversational_marketing.config.settings import get_settings
from conversational_marketing.integrations import facebook_messenger, slack, whatsapp

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = structlog.get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown events."""
    logger.info(
        "Starting Conversational Marketing",
        app_name=settings.app_name,
        version=settings.app_version,
        env=settings.app_env,
    )
    yield
    logger.info("Shutting down Conversational Marketing")


app = FastAPI(
    title="Conversational Marketing API",
    description="Agentic AI conversational marketing platform with multi-platform support",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["conversations"])
app.include_router(leads.router, prefix="/api/v1/leads", tags=["leads"])
app.include_router(whatsapp.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(facebook_messenger.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(slack.router, prefix="/webhooks", tags=["webhooks"])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint for load balancers and monitoring."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "env": settings.app_env,
    }


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    """Root endpoint with basic API information."""
    return {
        "name": "Conversational Marketing API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }


def main() -> None:
    """Run the application with uvicorn."""
    import uvicorn

    uvicorn.run(
        "conversational_marketing.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=settings.workers,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
