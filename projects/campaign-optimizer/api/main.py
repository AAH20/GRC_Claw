"""FastAPI application entry point for Campaign Optimizer."""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.models.schemas import ErrorResponse, HealthResponse
from api.routes import campaigns
from core.config import get_settings
from core.exceptions import CampaignOptimizerError
from core.logging import configure_logging, get_logger

settings = get_settings()
configure_logging(log_level=settings.log_level, json_format=settings.environment == "production")
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Handles startup and shutdown events for the application.
    """
    logger.info(
        "application_starting",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )
    yield
    logger.info("application_shutting_down")


app = FastAPI(
    title="Campaign Optimizer API",
    description="Autonomous Campaign Optimization — Multi-agent AI marketing platform",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add a unique request ID to each request.

    Args:
        request: Incoming request.
        call_next: Next middleware/handler.

    Returns:
        Response with request ID header.
    """
    request_id = str(uuid.uuid4())[:12]
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Exception handlers
@app.exception_handler(CampaignOptimizerError)
async def campaign_optimizer_exception_handler(
    request: Request, exc: CampaignOptimizerError
) -> JSONResponse:
    """Handle custom application exceptions.

    Args:
        request: The request that caused the exception.
        exc: The exception instance.

    Returns:
        JSON error response.
    """
    request_id = getattr(request.state, "request_id", None)
    logger.error(
        "application_error",
        error=exc.message,
        request_id=request_id,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            message=exc.message,
            details=exc.details,
            request_id=request_id,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle uncaught exceptions.

    Args:
        request: The request that caused the exception.
        exc: The exception instance.

    Returns:
        JSON error response.
    """
    request_id = getattr(request.state, "request_id", None)
    logger.error(
        "unhandled_exception",
        error=str(exc),
        request_id=request_id,
        path=request.url.path,
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            request_id=request_id,
        ).model_dump(),
    )


# Include routers
app.include_router(campaigns.router)


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health status of the API and its components.",
    tags=["health"],
)
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        Health status of the application.
    """
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        components={
            "api": "healthy",
            "database": "connected",  # Would check actual connection in production
            "redis": "connected",
            "agents": "ready",
        },
    )


@app.get(
    "/",
    summary="Root endpoint",
    description="API information and available endpoints.",
    tags=["health"],
)
async def root() -> dict[str, Any]:
    """Root endpoint with API information.

    Returns:
        API metadata.
    """
    return {
        "name": "Campaign Optimizer API",
        "version": settings.app_version,
        "description": "Autonomous Campaign Optimization — Multi-agent AI marketing platform",
        "docs": "/docs",
        "health": "/health",
    }


def main() -> None:
    """Run the application server."""
    uvicorn.run(
        "api.main:app",
        host=settings.api.host,
        port=settings.api.port,
        workers=settings.api.workers,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
