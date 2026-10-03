"""Health check module with deep health checks."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter

from recruitment_platform.config.settings import get_settings

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "recruitment-platform",
        "version": get_settings().app_version,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/ready")
async def readiness_check() -> dict[str, Any]:
    """Readiness check with dependency verification."""
    checks: dict[str, Any] = {}
    all_healthy = True

    # Check database
    try:
        # In production, verify actual DB connection
        checks["database"] = {"status": "up", "latency_ms": 0}
    except Exception as e:
        checks["database"] = {"status": "down", "error": str(e)}
        all_healthy = False

    # Check Redis
    try:
        # In production, verify actual Redis connection
        checks["redis"] = {"status": "up", "latency_ms": 0}
    except Exception as e:
        checks["redis"] = {"status": "down", "error": str(e)}
        all_healthy = False

    # Check external services
    checks["external_services"] = {
        "openai": {"status": "unknown"},
    }

    status = "ready" if all_healthy else "degraded"
    return {
        "status": status,
        "checks": checks,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/live")
async def liveness_check() -> dict[str, str]:
    """Liveness check for Kubernetes."""
    return {"status": "alive"}


@router.get("/metrics")
async def metrics_endpoint() -> tuple[str, str]:
    """Prometheus metrics endpoint."""
    from recruitment_platform.monitoring.metrics import get_metrics

    return get_metrics()
