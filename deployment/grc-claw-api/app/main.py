"""GRC_Claw API main application."""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram
from structlog import get_logger

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import GRCClawException, generic_exception_handler, grc_exception_handler
from app.middleware.rate_limit import RateLimitMiddleware

settings = get_settings()
logger = get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter(
    "grc_api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status"],
)
REQUEST_DURATION = Histogram(
    "grc_api_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("starting_up", app_name=settings.APP_NAME, version=settings.APP_VERSION)
    yield
    logger.info("shutting_down", app_name=settings.APP_NAME)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=settings.API_TITLE,
        description=settings.API_DESCRIPTION,
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # Exception handlers
    app.add_exception_handler(GRCClawException, grc_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.DEBUG else ["https://api.grc-claw.io"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"] if settings.DEBUG else ["api.grc-claw.io"])
    app.add_middleware(RateLimitMiddleware)

    # Request logging and metrics
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log requests and record metrics."""
        import time

        start = time.monotonic()
        response = await call_next(request)
        duration = time.monotonic() - start

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
        ).inc()
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(duration)

        return response

    # Include routers
    app.include_router(api_router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else 4,
    )
