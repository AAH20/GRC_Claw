"""Main application entry point for talent pool manager."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from talent_pool_manager.api import router as api_router
from talent_pool_manager.config import get_settings
from talent_pool_manager.config.logging_config import configure_logging, get_logger
from talent_pool_manager.models import APIInfo, ErrorResponse

logger = get_logger(__name__)

# Track application start time for uptime calculation
_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    settings = get_settings()
    configure_logging(
        log_level=settings.log_level,
        json_format=settings.is_production,
    )
    logger.info(
        "Starting talent pool manager",
        version=settings.app_version,
        env=settings.app_env,
    )
    yield
    logger.info("Shutting down talent pool manager")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Agentic AI talent pool management system with candidate discovery, "
            "segmentation, and engagement optimization"
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log all incoming requests."""
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(duration * 1000, 2),
        )
        return response

    # Exception handlers
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle all unhandled exceptions."""
        logger.error("Unhandled exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="Internal server error",
                detail=str(exc) if settings.debug else None,
                code="INTERNAL_ERROR",
            ).model_dump(),
        )

    # Include API routes
    app.include_router(api_router, prefix="/api/v1")

    # Root-level health check
    @app.get("/health", tags=["system"])
    async def root_health() -> dict[str, str]:
        """Root-level health check."""
        return {"status": "ok"}

    @app.get("/", response_model=APIInfo, tags=["system"])
    async def root() -> APIInfo:
        """Root endpoint with API information."""
        return APIInfo(
            name=settings.app_name,
            version=settings.app_version,
            description="Agentic AI talent pool management system",
            endpoints=[
                "/api/v1/pools",
                "/api/v1/candidates",
                "/api/v1/segments",
                "/api/v1/engagements",
                "/api/v1/outreach/campaigns",
                "/api/v1/outreach/templates",
                "/api/v1/agents/discover",
                "/api/v1/agents/segment",
                "/api/v1/agents/score",
                "/api/v1/agents/outreach",
                "/api/v1/agents/optimize-engagement",
            ],
            documentation_url="/docs",
        )

    return app


def main() -> None:
    """Main entry point for running the application."""
    import uvicorn

    settings = get_settings()
    configure_logging(
        log_level=settings.log_level,
        json_format=settings.is_production,
    )

    uvicorn.run(
        "talent_pool_manager.main:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
