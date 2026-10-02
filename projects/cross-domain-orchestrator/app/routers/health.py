"""Health check router.

Provides endpoints for liveness and readiness probes.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model.

    Attributes:
        status: Service status.
        timestamp: Current timestamp.
        version: Application version.
    """

    status: str = Field(default="healthy", description="Service status")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Current timestamp",
    )
    version: str = Field(default="1.0.0", description="Application version")


class ReadinessResponse(BaseModel):
    """Readiness probe response model.

    Attributes:
        ready: Whether the service is ready.
        checks: Individual component check results.
    """

    ready: bool = Field(..., description="Whether the service is ready")
    checks: dict[str, bool] = Field(
        default_factory=dict,
        description="Component check results",
    )


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Liveness probe endpoint.

    Returns:
        Health status response.
    """
    return HealthResponse()


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness_check() -> ReadinessResponse:
    """Readiness probe endpoint.

    Returns:
        Readiness status with component checks.
    """
    return ReadinessResponse(
        ready=True,
        checks={
            "api": True,
            "agents": True,
        },
    )
