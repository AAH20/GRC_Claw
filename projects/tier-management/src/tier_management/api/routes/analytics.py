"""Analytics endpoints."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from tier_management.agents.tier_analytics import TierAnalyticsAgent
from tier_management.config.settings import Settings, get_settings
from tier_management.models.schemas import TierAnalytics

analytics_router = APIRouter()

# In-memory store
_analytics_store: dict[UUID, TierAnalytics] = {}


@analytics_router.post("", response_model=TierAnalytics, status_code=status.HTTP_201_CREATED)
async def generate_analytics(
    analytics_data: dict[str, Any],
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> TierAnalytics:
    """Generate analytics for a tier.

    Args:
        analytics_data: Analytics request data.
        settings: Application settings.

    Returns:
        The generated analytics.
    """
    agent = TierAnalyticsAgent()
    await agent.initialize()

    try:
        result = await agent.execute(analytics_data)
        _analytics_store[result.id] = result
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e


@analytics_router.get("/{analytics_id}", response_model=TierAnalytics)
async def get_analytics(
    analytics_id: UUID,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> TierAnalytics:
    """Get a specific analytics record by ID.

    Args:
        analytics_id: The analytics identifier.
        settings: Application settings.

    Returns:
        The requested analytics.

    Raises:
        HTTPException: If analytics not found.
    """
    analytics = _analytics_store.get(analytics_id)
    if not analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analytics '{analytics_id}' not found",
        )
    return analytics


@analytics_router.get("/tier/{tier_id}", response_model=list[TierAnalytics])
async def get_tier_analytics(
    tier_id: UUID,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> list[TierAnalytics]:
    """Get all analytics for a specific tier.

    Args:
        tier_id: The tier identifier.
        settings: Application settings.

    Returns:
        List of analytics for the tier.
    """
    return [
        a for a in _analytics_store.values()
        if a.tier_id == tier_id
    ]


@analytics_router.get("/tier/{tier_id}/summary")
async def get_tier_summary(
    tier_id: UUID,
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> dict[str, Any]:
    """Get a summary of analytics for a tier.

    Args:
        tier_id: The tier identifier.
        settings: Application settings.

    Returns:
        Summary dictionary with aggregated metrics.
    """
    tier_analytics = [
        a for a in _analytics_store.values()
        if a.tier_id == tier_id
    ]

    if not tier_analytics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No analytics found for tier '{tier_id}'",
        )

    # Aggregate metrics
    total_members = sum(a.total_members for a in tier_analytics)
    total_revenue = sum(a.revenue for a in tier_analytics)
    avg_engagement = (
        sum(a.avg_engagement_score for a in tier_analytics) / len(tier_analytics)
        if tier_analytics else 0.0
    )

    all_insights = []
    for a in tier_analytics:
        all_insights.extend(a.insights)

    return {
        "tier_id": str(tier_id),
        "total_members": total_members,
        "total_revenue": total_revenue,
        "avg_engagement_score": avg_engagement,
        "insights": all_insights,
        "periods_analyzed": len(tier_analytics),
    }
