"""Analytics API routes — Campaign performance analytics and reporting."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

router = APIRouter()


# ─── Request/Response Models ────────────────────────────────────────


class MetricsResponse(BaseModel):
    """Response model for campaign metrics."""

    campaign_id: str
    impressions: int
    clicks: int
    conversions: int
    spend: float
    revenue: float
    ctr: float
    cpc: float
    cpa: float
    roas: float
    period: str


class ReportRequest(BaseModel):
    """Request model for generating a report."""

    campaign_id: str = Field(..., min_length=1)
    start_date: str | None = None
    end_date: str | None = None
    granularity: str = Field(default="daily", pattern="^(daily|weekly|monthly)$")


class ReportResponse(BaseModel):
    """Response model for generated reports."""

    campaign_id: str
    report_type: str
    generated_at: str
    summary: dict[str, Any]
    daily_breakdown: list[dict[str, Any]]
    recommendations: list[str]


# ─── In-Memory Store (replace with database in production) ──────────

_analytics: dict[str, dict[str, Any]] = {}


# ─── Routes ─────────────────────────────────────────────────────────


@router.get("/{campaign_id}", response_model=MetricsResponse)
async def get_campaign_analytics(campaign_id: str) -> MetricsResponse:
    """Get analytics for a specific campaign.

    Args:
        campaign_id: The campaign identifier.

    Returns:
        Campaign performance metrics.

    Raises:
        HTTPException: If analytics data is not found.
    """
    data = _analytics.get(campaign_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analytics for campaign {campaign_id} not found",
        )
    return MetricsResponse(**data)


@router.post("/{campaign_id}/report", response_model=ReportResponse)
async def generate_report(request: ReportRequest) -> ReportResponse:
    """Generate a performance report for a campaign.

    Args:
        request: Report generation parameters.

    Returns:
        Generated performance report.

    Raises:
        HTTPException: If campaign data is not found.
    """
    data = _analytics.get(request.campaign_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analytics for campaign {request.campaign_id} not found",
        )

    logger.info("Report generated", campaign_id=request.campaign_id)

    # In production, this would aggregate data from multiple sources
    daily_breakdown = [
        {
            "date": (datetime.now(UTC)).isoformat(),
            "impressions": data.get("impressions", 0) // 30,
            "clicks": data.get("clicks", 0) // 30,
            "conversions": data.get("conversions", 0) // 30,
            "spend": data.get("spend", 0) / 30,
            "revenue": data.get("revenue", 0) / 30,
        }
    ]

    return ReportResponse(
        campaign_id=request.campaign_id,
        report_type="performance",
        generated_at=datetime.now(UTC).isoformat(),
        summary={
            "total_spend": data.get("spend", 0),
            "total_revenue": data.get("revenue", 0),
            "roas": data.get("roas", 0),
            "ctr": data.get("ctr", 0),
            "cpa": data.get("cpa", 0),
        },
        daily_breakdown=daily_breakdown,
        recommendations=[
            "Increase budget on high-performing ad sets",
            "Refresh creative for ad sets with declining CTR",
            "Expand lookalike audiences based on converters",
        ],
    )


@router.get("/{campaign_id}/funnel")
async def get_funnel_analytics(campaign_id: str) -> dict[str, Any]:
    """Get funnel analytics for a campaign.

    Args:
        campaign_id: The campaign identifier.

    Returns:
        Funnel stage data.

    Raises:
        HTTPException: If analytics data is not found.
    """
    data = _analytics.get(campaign_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analytics for campaign {campaign_id} not found",
        )

    impressions = data.get("impressions", 0)
    clicks = data.get("clicks", 0)
    conversions = data.get("conversions", 0)

    return {
        "campaign_id": campaign_id,
        "stages": [
            {
                "stage": "impressions",
                "count": impressions,
                "rate": 1.0,
            },
            {
                "stage": "clicks",
                "count": clicks,
                "rate": clicks / impressions if impressions > 0 else 0,
            },
            {
                "stage": "conversions",
                "count": conversions,
                "rate": conversions / clicks if clicks > 0 else 0,
            },
        ],
    }
