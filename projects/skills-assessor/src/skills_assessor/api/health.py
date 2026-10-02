"""Health check API routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from skills_assessor.config.settings import Settings, get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    timestamp: datetime
    environment: str


class ReadinessResponse(BaseModel):
    """Readiness check response model."""

    ready: bool
    checks: dict[str, bool]


@router.get("/health", response_model=HealthResponse)
async def health_check(
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    """Health check endpoint.

    Returns:
        HealthResponse: Current health status of the application.
    """
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        environment=settings.environment,
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check(
    settings: Settings = Depends(get_settings),
) -> ReadinessResponse:
    """Readiness check endpoint for Kubernetes probes.

    Returns:
        ReadinessResponse: Readiness status with component checks.
    """
    checks = {
        "config_loaded": True,
        "llm_configured": bool(settings.openai_api_key),
    }
    ready = all(checks.values())
    return ReadinessResponse(ready=ready, checks=checks)
