"""Finance Marketing Platform - FastAPI Application Entry Point."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

import structlog
import yaml
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from finance_marketing.agents.analytics import AnalyticsAgent
from finance_marketing.agents.campaigns import CampaignAgent
from finance_marketing.agents.compliance import ComplianceAgent
from finance_marketing.agents.content import ContentAgent
from finance_marketing.agents.reporting import ReportingAgent
from finance_marketing.api import campaigns, content

logger = structlog.get_logger(__name__)


def load_config() -> dict:
    """Load configuration from YAML file.

    Returns:
        Dictionary containing the application configuration.
    """
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "config",
        "config.yaml",
    )
    try:
        with open(config_path) as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.warning("Config file not found, using defaults", path=config_path)
        return {}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup/shutdown events.

    Args:
        app: The FastAPI application instance.

    Yields:
        None
    """
    logger.info("Starting Finance Marketing Platform")
    app.state.content_agent = ContentAgent()
    app.state.compliance_agent = ComplianceAgent()
    app.state.campaign_agent = CampaignAgent()
    app.state.analytics_agent = AnalyticsAgent()
    app.state.reporting_agent = ReportingAgent()
    logger.info("All agents initialized successfully")
    yield
    logger.info("Shutting down Finance Marketing Platform")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    load_config()

    app = FastAPI(
        title="Finance Marketing Platform",
        description="FINRA/SEC-compliant agentic AI marketing platform for financial services",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    app.include_router(content.router, prefix="/api/v1/content", tags=["content"])
    app.include_router(campaigns.router, prefix="/api/v1/campaigns", tags=["campaigns"])

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle all unhandled exceptions."""
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
        """Health check endpoint."""
        return {"status": "healthy", "version": "0.1.0"}

    return app


app = create_app()


def main() -> None:
    """Run the application with uvicorn."""
    import uvicorn

    uvicorn.run(
        "finance_marketing.main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("APP_ENV") == "dev",
        workers=int(os.getenv("WORKERS", "4")),
    )


if __name__ == "__main__":
    main()
