"""Analytics API routes."""
from __future__ import annotations

from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from journey_orchestrator.agents.journey_analytics import (
    AnalyticsRequest,
    JourneyAnalytics,
)
from journey_orchestrator.models.analytics import AnalyticsSummary, MetricType

logger = structlog.get_logger(__name__)
router = APIRouter()

# In-memory store for analytics reports (replace with database in production)
_analytics_reports: dict[str, dict] = {}


class AnalyticsRequestSchema(BaseModel):
    """API request schema for analytics."""

    journey_id: str = Field(..., description="The journey ID to analyze")
    start_date: datetime | None = Field(default=None, description="Analysis period start")
    end_date: datetime | None = Field(default=None, description="Analysis period end")
    metrics: list[str] = Field(
        default=["conversion_rate", "engagement_rate", "revenue_per_customer"],
        description="Metrics to compute",
    )
    include_funnel: bool = Field(default=True, description="Include funnel analysis")
    include_cohorts: bool = Field(default=False, description="Include cohort analysis")


class AnalyticsResponse(BaseModel):
    """API response schema for analytics."""

    journey_id: str
    conversion_rate: float
    engagement_rate: float
    revenue_per_customer: float
    total_customers: int
    converted_customers: int
    insights_count: int
    generated_at: datetime


@router.post("", response_model=AnalyticsResponse, status_code=200)
async def get_analytics(request: AnalyticsRequestSchema) -> AnalyticsResponse:
    """Get analytics for a journey.

    Args:
        request: The analytics request.

    Returns:
        The analytics response.

    Raises:
        HTTPException: If analytics computation fails.
    """
    if not request.journey_id.strip():
        raise HTTPException(status_code=400, detail="journey_id must not be empty")

    try:
        metric_types = [MetricType(m) for m in request.metrics]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid metric type: {e}") from e

    analytics_request = AnalyticsRequest(
        journey_id=request.journey_id,
        start_date=request.start_date,
        end_date=request.end_date,
        metrics=metric_types,
        include_funnel=request.include_funnel,
        include_cohorts=request.include_cohorts,
    )

    agent = JourneyAnalytics()
    try:
        report = await agent.analyze(analytics_request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    # Store report
    _analytics_reports[request.journey_id] = report.model_dump()

    logger.info(
        "Analytics computed via API",
        journey_id=request.journey_id,
        conversion_rate=report.performance.conversion_rate,
    )

    return AnalyticsResponse(
        journey_id=report.journey_id,
        conversion_rate=report.performance.conversion_rate,
        engagement_rate=report.performance.engagement_rate,
        revenue_per_customer=report.performance.revenue_per_customer,
        total_customers=report.performance.total_customers,
        converted_customers=report.performance.converted_customers,
        insights_count=len(report.insights),
        generated_at=report.generated_at,
    )


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary() -> AnalyticsSummary:
    """Get a high-level analytics summary across all journeys.

    Returns:
        The analytics summary.
    """
    agent = JourneyAnalytics()
    summary = await agent.get_summary()
    logger.info("Analytics summary retrieved", total_journeys=summary.total_journeys)
    return summary


@router.get("/{journey_id}", response_model=AnalyticsResponse)
async def get_journey_analytics(journey_id: str) -> AnalyticsResponse:
    """Get cached analytics for a journey.

    Args:
        journey_id: The journey ID.

    Returns:
        The cached analytics response.

    Raises:
        HTTPException: If no analytics found for the journey.
    """
    report = _analytics_reports.get(journey_id)
    if not report:
        raise HTTPException(
            status_code=404,
            detail="No analytics found for this journey. Run POST /analytics first.",
        )

    return AnalyticsResponse(
        journey_id=report["journey_id"],
        conversion_rate=report["performance"]["conversion_rate"],
        engagement_rate=report["performance"]["engagement_rate"],
        revenue_per_customer=report["performance"]["revenue_per_customer"],
        total_customers=report["performance"]["total_customers"],
        converted_customers=report["performance"]["converted_customers"],
        insights_count=len(report.get("insights", [])),
        generated_at=datetime.now(UTC),
    )
