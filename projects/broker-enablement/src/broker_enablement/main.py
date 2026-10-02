"""FastAPI application entry point for the Broker Enablement platform."""

from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from broker_enablement.api.commissions import router as commissions_router
from broker_enablement.api.partners import router as partners_router

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    logger.info("Starting Broker Enablement platform")
    yield
    logger.info("Shutting down Broker Enablement platform")


app = FastAPI(
    title="Broker Enablement Platform",
    description="Multi-tenant AI-powered broker enablement platform",
    version="0.1.0",
    lifespan=lifespan,
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
    """Global exception handler for unhandled errors."""
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


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint for load balancers and monitoring."""
    return {"status": "healthy", "version": "0.1.0"}


app.include_router(partners_router, prefix="/partners", tags=["partners"])
app.include_router(commissions_router, prefix="/commissions", tags=["commissions"])


def main() -> None:
    """Run the application with uvicorn."""
    import uvicorn

    uvicorn.run(
        "broker_enablement.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=4,
    )


if __name__ == "__main__":
    main()
