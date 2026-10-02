"""FastAPI application entry point for the Website Optimization platform."""

from __future__ import annotations

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from website_optimization.api import experiments, pages
from website_optimization.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="Website Optimization API",
        description="Agentic AI platform for website optimization",
        version="0.1.0",
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

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle all unhandled exceptions.

        Args:
            request: The incoming request.
            exc: The exception that was raised.

        Returns:
            JSON response with error details.
        """
        logger.error(
            "Unhandled exception",
            exc_info=exc,
            path=request.url.path,
            method=request.method,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    app.include_router(experiments.router, prefix="/api/v1/experiments", tags=["experiments"])
    app.include_router(pages.router, prefix="/api/v1/pages", tags=["pages"])

    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        """Health check endpoint.

        Returns:
            Health status dictionary.
        """
        return {"status": "healthy", "version": "0.1.0"}

    return app


app = create_app()


def main() -> None:
    """Run the application with uvicorn."""
    import uvicorn

    uvicorn.run(
        "website_optimization.main:app",
        host=settings.server.host,
        port=settings.server.port,
        workers=settings.server.workers,
        log_level=settings.app.log_level.lower(),
    )


if __name__ == "__main__":
    main()
