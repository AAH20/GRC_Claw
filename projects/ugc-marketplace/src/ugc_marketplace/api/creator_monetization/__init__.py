"""API routes for creator monetization."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monetization", tags=["monetization"])


class MetricRecordRequest(BaseModel):
    """Request model for recording a metric."""

    name: str = Field(..., min_length=1, description="Metric name")
    value: float = Field(..., description="Metric value")
    label: str | None = Field(default=None)


class ReportRequest(BaseModel):
    """Request model for generating a report."""

    report_id: str = Field(..., description="Unique report identifier")
    creator_id: str = Field(..., description="Creator identifier")
    period_start: datetime = Field(..., description="Report period start")
    period_end: datetime = Field(..., description="Report period end")


class ForecastRequest(BaseModel):
    """Request model for forecasting a metric."""

    name: str = Field(..., description="Metric name to forecast")
    days: int = Field(default=30, ge=1, le=365, description="Number of days to forecast")


class RevenueReportResponse(BaseModel):
    """Response model for revenue report."""

    report_id: str
    creator_id: str
    period_start: str
    period_end: str
    total_revenue: str
    subscription_revenue: str
    tip_revenue: str
    merchandise_revenue: str
    sponsorship_revenue: str
    other_revenue: str
    subscriber_count: int
    active_subscribers: int
    churned_subscribers: int
    currency: str
    insights: list[str]
    generated_at: str


_reports: dict[str, dict[str, Any]] = {}
_metrics: dict[str, list[dict[str, Any]]] = {}


@router.post("/metrics", status_code=status.HTTP_201_CREATED)
async def record_metric(request: MetricRecordRequest) -> dict[str, Any]:
    """Record a metric data point."""
    point = {
        "timestamp": datetime.now(UTC).isoformat(),
        "value": request.value,
        "label": request.label,
    }

    if request.name not in _metrics:
        _metrics[request.name] = []
    _metrics[request.name].append(point)

    logger.debug("Metric recorded", extra={"name": request.name, "value": request.value})
    return {"name": request.name, "recorded": True, "point": point}


@router.get("/metrics")
async def list_metrics() -> dict[str, Any]:
    """List all available metrics."""
    return {
        "metrics": list(_metrics.keys()),
        "count": len(_metrics),
    }


@router.post("/reports", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
async def generate_report(request: ReportRequest) -> dict[str, Any]:
    """Generate an analytics report."""
    if request.report_id in _reports:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Report {request.report_id} already exists",
        )

    if request.period_start >= request.period_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Period start must be before end",
        )

    period_metrics: dict[str, list[dict[str, Any]]] = {}
    for name, points in _metrics.items():
        filtered = [
            p for p in points
            if request.period_start <= datetime.fromisoformat(p["timestamp"]) <= request.period_end
        ]
        if filtered:
            period_metrics[name] = filtered

    summary: dict[str, float] = {}
    for name, points in period_metrics.items():
        values = [p["value"] for p in points]
        summary[f"{name}_total"] = sum(values)
        summary[f"{name}_avg"] = sum(values) / len(values) if values else 0.0
        summary[f"{name}_max"] = max(values) if values else 0.0
        summary[f"{name}_min"] = min(values) if values else 0.0

    insights: list[str] = []
    if "revenue_total" in summary and summary["revenue_total"] > 0:
        insights.append(f"Total revenue: ${summary['revenue_total']:.2f}")
    if "subscribers_total" in summary:
        if summary["subscribers_total"] > 1000:
            insights.append("Large subscriber base - focus on retention strategies")
        elif summary["subscribers_total"] < 50:
            insights.append("Growing subscriber base - consider promotional campaigns")
    if not insights:
        insights.append("Performance within normal ranges")

    report = {
        "report_id": request.report_id,
        "creator_id": request.creator_id,
        "period": {
            "start": request.period_start.isoformat(),
            "end": request.period_end.isoformat(),
        },
        "metrics": period_metrics,
        "summary": summary,
        "insights": insights,
        "generated_at": datetime.now(UTC).isoformat(),
    }

    _reports[request.report_id] = report
    logger.info("Report generated", extra={"report_id": request.report_id})
    return report


@router.get("/reports/{report_id}")
async def get_report(report_id: str) -> dict[str, Any]:
    """Get a generated report by ID."""
    if report_id not in _reports:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' not found",
        )
    return _reports[report_id]


@router.post("/forecast")
async def forecast_metric(request: ForecastRequest) -> dict[str, Any]:
    """Forecast a metric for future days."""
    if request.name not in _metrics or len(_metrics[request.name]) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient data for metric {request.name}",
        )

    points = _metrics[request.name]
    n = len(points)

    x_mean = (n - 1) / 2
    y_mean = sum(p["value"] for p in points) / n

    numerator = sum(
        (i - x_mean) * (p["value"] - y_mean) for i, p in enumerate(points)
    )
    denominator = sum((i - x_mean) ** 2 for i in range(n))

    slope = numerator / denominator if denominator != 0 else 0
    intercept = y_mean - slope * x_mean

    last_time = datetime.fromisoformat(points[-1]["timestamp"])
    forecast: list[dict[str, Any]] = []
    for i in range(1, request.days + 1):
        value = intercept + slope * (n - 1 + i)
        forecast.append(
            {
                "date": (last_time + timedelta(days=i)).isoformat(),
                "value": max(0, round(value, 2)),
            }
        )

    return {
        "metric": request.name,
        "days": request.days,
        "forecast": forecast,
    }


@router.get("/revenue/{creator_id}", response_model=RevenueReportResponse)
async def get_revenue_report(creator_id: str) -> RevenueReportResponse:
    """Get a revenue report for a creator."""
    now = datetime.now(UTC)
    thirty_days_ago = now - timedelta(days=30)

    return RevenueReportResponse(
        report_id=f"rev-{creator_id}",
        creator_id=creator_id,
        period_start=thirty_days_ago.isoformat(),
        period_end=now.isoformat(),
        total_revenue="0.00",
        subscription_revenue="0.00",
        tip_revenue="0.00",
        merchandise_revenue="0.00",
        sponsorship_revenue="0.00",
        other_revenue="0.00",
        subscriber_count=0,
        active_subscribers=0,
        churned_subscribers=0,
        currency="USD",
        insights=["No data available for this period"],
        generated_at=now.isoformat(),
    )
