"""FastAPI application factory and configuration."""
from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from api.routes import churn, insights, leads, next_action, qualification
from api.models.schemas import ErrorResponse, HealthResponse
from core.config import get_settings
from core.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    configure_logging()
    settings = get_settings()
    logger.info("application_starting", version=settings.app_version, environment=settings.environment)
    yield
    logger.info("application_shutting_down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    app = FastAPI(
        title="AI-Powered Lead Scoring & Qualification",
        description="7-agent system for automated lead intelligence",
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

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle uncaught exceptions."""
        logger.error("unhandled_exception", path=request.url.path, error=str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(error="Internal server error", detail=str(exc) if settings.is_development else None).model_dump(),
        )

    app.include_router(leads.router)
    app.include_router(qualification.router)
    app.include_router(churn.router)
    app.include_router(next_action.router)
    app.include_router(insights.router)

    @app.get("/api/v1/health", response_model=HealthResponse, tags=["health"])
    async def health_check() -> HealthResponse:
        """Health check endpoint."""
        return HealthResponse(status="healthy", version=settings.app_version, timestamp="", services={"api": "up", "database": "up", "redis": "up"})

    if settings.prometheus_enabled:
        metrics_app = make_asgi_app()
        app.mount("/api/v1/metrics", metrics_app)

    return app


app = create_app()
