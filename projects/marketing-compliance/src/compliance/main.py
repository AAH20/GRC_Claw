"""FastAPI application entry point for the Marketing Compliance Platform."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

from compliance import __version__
from compliance.agents.orchestrator import OrchestratorAgent
from compliance.api import policies_router, violations_router
from compliance.config import get_config, get_settings

logger = logging.getLogger("compliance.main")


def configure_logging(level: str) -> None:
    """Configure root logging.

    Args:
        level: Log level name (e.g. ``INFO``).
    """
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown.

    Args:
        app: The FastAPI application instance.

    Yields:
        Control back to the server while it is running.
    """
    settings = get_settings()
    configure_logging(settings.compliance_log_level)
    config = get_config()
    app.state.config = config
    app.state.orchestrator = OrchestratorAgent(config)
    logger.info(
        "Marketing Compliance Platform %s starting in %s mode",
        __version__,
        settings.compliance_environment,
    )
    try:
        yield
    finally:
        logger.info("Marketing Compliance Platform shutting down")


app = FastAPI(
    title="Marketing Compliance Platform",
    description="AI-powered marketing compliance monitoring and enforcement.",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(policies_router)
app.include_router(violations_router)


class HealthResponse(BaseModel):
    """Health check response payload."""

    status: str = Field(default="ok")
    version: str = Field(default=__version__)


class ScanRequest(BaseModel):
    """Payload for triggering a compliance scan."""

    sources: list[str] = Field(default_factory=lambda: ["salesforce", "hubspot", "mailchimp"])
    campaigns: list[dict[str, Any]] = Field(default_factory=list)
    batch_size: int = Field(default=50, ge=1, le=1000)
    format: str = Field(default="json")


class ScanResponse(BaseModel):
    """Result of a compliance scan."""

    status: str
    metrics: dict[str, float]
    report: dict[str, Any] | None = None
    errors: list[str] = Field(default_factory=list)


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    """Return service health information.

    Returns:
        The current health status and version.
    """
    return HealthResponse()


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    """Return a service banner.

    Returns:
        A mapping with the service name and version.
    """
    return {"service": "marketing-compliance", "version": __version__}


@app.post("/api/v1/monitor/scan", response_model=ScanResponse, tags=["scan"])
async def trigger_scan(payload: ScanRequest) -> ScanResponse:
    """Run the full compliance pipeline.

    Args:
        payload: Scan parameters.

    Returns:
        The scan result including aggregated metrics and the generated report.

    Raises:
        HTTPException: 500 if the orchestrator fails unexpectedly.
    """
    orchestrator: OrchestratorAgent = app.state.orchestrator
    try:
        result = await orchestrator.execute(payload.model_dump())
    except Exception as exc:  # noqa: BLE001 - surface as an HTTP error
        logger.exception("scan failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc

    report = result.items[0] if result.items else None
    return ScanResponse(
        status=result.status.value,
        metrics=result.metrics,
        report=report,
        errors=result.errors,
    )


@app.post("/api/v1/reports/generate", tags=["reports"])
async def generate_report(payload: ScanRequest) -> dict[str, Any]:
    """Generate a compliance report without persisting violations.

    Args:
        payload: Report parameters.

    Returns:
        The generated report document.

    Raises:
        HTTPException: 500 if report generation fails.
    """
    orchestrator: OrchestratorAgent = app.state.orchestrator
    try:
        result = await orchestrator.execute(payload.model_dump())
    except Exception as exc:  # noqa: BLE001
        logger.exception("report generation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc

    if not result.items:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="report generation produced no output",
        )
    return result.items[0]


def main() -> None:
    """Run the application with uvicorn (console entry point)."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "compliance.main:app",
        host=settings.server_host,
        port=settings.server_port,
        log_level=settings.compliance_log_level.lower(),
    )


if __name__ == "__main__":
    main()
