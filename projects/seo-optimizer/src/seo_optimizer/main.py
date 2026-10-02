"""SEO Optimizer FastAPI application entry point."""

from __future__ import annotations

import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

from seo_optimizer.api import content, keywords
from seo_optimizer.config import get_settings

logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "seo_optimizer_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "seo_optimizer_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics for each request."""

    async def dispatch(self, request: Request, call_next: callable) -> JSONResponse:
        """Process request and record metrics.

        Args:
            request: The incoming HTTP request.
            call_next: The next handler in the middleware chain.

        Returns:
            The HTTP response.
        """
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
        ).inc()
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(duration)

        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown events.

    Args:
        app: The FastAPI application instance.
    """
    settings = get_settings()
    logger.info(
        "Starting SEO Optimizer",
        version="0.1.0",
        environment=settings.app_environment,
    )
    yield
    logger.info("Shutting down SEO Optimizer")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="SEO Optimizer",
        description="AI-powered SEO optimization platform with multi-agent architecture",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(PrometheusMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(keywords.router, prefix="/api/v1/keywords", tags=["keywords"])
    app.include_router(content.router, prefix="/api/v1/content", tags=["content"])

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        """Health check endpoint.

        Returns:
            Health status information.
        """
        return {"status": "healthy", "version": "0.1.0"}

    @app.get("/metrics", tags=["monitoring"])
    async def metrics() -> JSONResponse:
        """Prometheus metrics endpoint.

        Returns:
            Prometheus-formatted metrics.
        """
        return JSONResponse(content=generate_latest().decode("utf-8"))

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Global exception handler for unhandled exceptions.

        Args:
            request: The HTTP request that caused the exception.
            exc: The unhandled exception.

        Returns:
            JSON error response.
        """
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

    return app


app = create_app()


def main() -> None:
    """Run the application with uvicorn."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "seo_optimizer.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.workers,
        reload=settings.app_environment == "development",
    )


if __name__ == "__main__":
    main()
