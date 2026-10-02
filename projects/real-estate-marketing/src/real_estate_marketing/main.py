"""FastAPI application entry point for the Real Estate Marketing platform."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from real_estate_marketing.api.leads import router as leads_router
from real_estate_marketing.api.properties import router as properties_router
from real_estate_marketing.config import get_settings
from real_estate_marketing.models import ErrorResponse, HealthResponse

logger = structlog.get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown events."""
    logger.info(
        "application_starting",
        app_name=settings.app_name,
        version=settings.version,
        environment=settings.environment,
    )
    yield
    logger.info("application_shutting_down", app_name=settings.app_name)


app = FastAPI(
    title=settings.app_name,
    description=settings.description,
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors."""
    logger.error(
        "unhandled_exception",
        error=str(exc),
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal Server Error",
            detail=str(exc) if settings.debug else None,
            code="INTERNAL_ERROR",
        ).model_dump(),
    )


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Health check endpoint for load balancers and monitoring.

    Returns:
        HealthResponse with current application status.
    """
    return HealthResponse(
        status="healthy",
        version=settings.version,
        services={
            "api": "up",
            "database": "up",
            "redis": "up",
        },
    )


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """Root endpoint with basic API information.

    Returns:
        Dictionary with API name and documentation URL.
    """
    return {
        "name": settings.app_name,
        "version": settings.version,
        "documentation": "/docs",
    }


app.include_router(properties_router, prefix="/api/v1/properties", tags=["Properties"])
app.include_router(leads_router, prefix="/api/v1/leads", tags=["Leads"])


def main() -> None:
    """Run the application with uvicorn."""
    import uvicorn

    uvicorn.run(
        "real_estate_marketing.main:app",
        host=settings.server.host,
        port=settings.server.port,
        workers=settings.server.workers,
        reload=settings.server.reload,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
