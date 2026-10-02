"""Metrics routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from community_governance.api.dependencies import get_metrics
from community_governance.integrations import MetricsIntegration

router = APIRouter(tags=["metrics"])


@router.get("/metrics", response_class=PlainTextResponse)
async def get_prometheus_metrics(
    metrics: MetricsIntegration = Depends(get_metrics),
) -> str:
    """Get Prometheus-formatted metrics.

    Args:
        metrics: The metrics integration.

    Returns:
        Prometheus-formatted metrics string.
    """
    collected = metrics.get_metrics()

    lines: list[str] = []
    for key, value in collected["counters"].items():
        lines.append(f"# TYPE {key.split('{')[0]} counter")
        lines.append(f"{key} {value}")
    for key, value in collected["gauges"].items():
        lines.append(f"# TYPE {key.split('{')[0]} gauge")
        lines.append(f"{key} {value}")

    return "\n".join(lines)
