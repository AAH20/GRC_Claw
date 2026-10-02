"""Customer Service AI Platform — Main Application Entry Point."""

from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from customer_service.api import customers, tickets
from customer_service.config import get_settings

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    """Application lifespan manager for startup/shutdown events."""
    settings = get_settings()
    logger.info(
        "Starting Customer Service AI Platform",
        version="0.1.0",
        environment=settings.environment,
    )
    yield
    logger.info("Shutting down Customer Service AI Platform")


def create_app() -> FastAPI:
    """Application factory for the Customer Service AI Platform."""
    settings = get_settings()

    app = FastAPI(
        title="Customer Service AI Platform",
        description="Modularized agentic AI customer service platform",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.environment == "development" else None,
        redoc_url="/redoc" if settings.environment == "development" else None,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
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

    # Include routers
    app.include_router(tickets.router, prefix="/api/v1/tickets", tags=["tickets"])
    app.include_router(customers.router, prefix="/api/v1/customers", tags=["customers"])

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy", "version": "0.1.0"}

    return app


app = create_app()
