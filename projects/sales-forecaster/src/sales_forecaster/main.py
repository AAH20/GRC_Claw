"""FastAPI application entry point for the Sales Forecaster."""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from sales_forecaster.api import forecasts_router, pipeline_router
from sales_forecaster.core import get_settings, setup_logging
from sales_forecaster.core.exceptions import SalesForecasterError
from sales_forecaster.core.models import ApiResponse, HealthCheck, HealthStatus

logger = setup_logging()
_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager handling startup and shutdown events."""
    settings = get_settings()
    logger.info(
        "Starting Sales Forecaster",
        version=settings.app_version,
        environment=settings.environment,
    )
    yield
    logger.info("Shutting down Sales Forecaster")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title="Sales Forecaster API",
        description="AI-powered sales forecasting with multi-agent pipeline",
        version=settings.app_version,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        """Add a unique request ID to each request."""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(SalesForecasterError)
    async def sales_forecaster_exception_handler(
        request: Request, exc: SalesForecasterError
    ) -> JSONResponse:
        """Handle custom Sales Forecaster exceptions."""
        request_id = getattr(request.state, "request_id", None)
        logger.error("Application error", error=str(exc), request_id=request_id, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ApiResponse(
                success=False, error=str(exc), request_id=request_id
            ).model_dump(),
        )

    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    app.include_router(forecasts_router)
    app.include_router(pipeline_router)

    return app


app = create_app()


@app.get("/health", response_model=HealthCheck, tags=["health"])
async def health_check() -> HealthCheck:
    """Health check endpoint.

    Returns:
        Health check status with component health info.
    """
    settings = get_settings()
    checks: dict[str, bool] = {"api": True}

    try:
        from sales_forecaster.core.cache import get_redis_client

        redis = get_redis_client()
        if redis:
            await redis.ping()
            checks["redis"] = True
        else:
            checks["redis"] = False
    except Exception:
        checks["redis"] = False

    overall_status = HealthStatus.HEALTHY if all(checks.values()) else HealthStatus.DEGRADED

    return HealthCheck(
        status=overall_status,
        version=settings.app_version,
        timestamp=datetime.now(),
        checks=checks,
        uptime_seconds=time.time() - _start_time,
    )


@app.get("/", response_model=ApiResponse[dict[str, str]], tags=["root"])
async def root() -> ApiResponse[dict[str, str]]:
    """Root endpoint.

    Returns:
        Basic API information.
    """
    settings = get_settings()
    return ApiResponse(
        success=True,
        data={
            "name": "Sales Forecaster API",
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/health",
        },
    )


def main() -> None:
    """Run the application with uvicorn."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "sales_forecaster.main:app",
        host=settings.server_host,
        port=settings.server_port,
        workers=settings.server_workers,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
