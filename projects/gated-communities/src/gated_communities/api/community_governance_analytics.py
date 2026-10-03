"""Analytics routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query

from community_governance.api.dependencies import get_governance_analytics
from community_governance.config.logging_config import get_logger
from community_governance.models.analytics import GovernanceAnalytics, GovernanceSummary

if TYPE_CHECKING:
    from community_governance.agents import GovernanceAnalyticsAgent


logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("", response_model=GovernanceAnalytics)
async def get_analytics(
    period_days: int = Query(default=30, ge=1, le=365, description="Analytics period in days"),
    focus_areas: list[str] | None = Query(default=None, description="Areas to focus on"),  # noqa: B008
    agent: GovernanceAnalyticsAgent = Depends(get_governance_analytics),  # noqa: B008
) -> GovernanceAnalytics:
    """Get comprehensive governance analytics.

    Args:
        period_days: Number of days for the analytics period.
        focus_areas: Optional areas to focus the analysis on.
        agent: The governance analytics agent.

    Returns:
        Comprehensive governance analytics.
    """
    from datetime import datetime, timedelta

    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=period_days)

    analytics = await agent.execute(
        {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "focus_areas": focus_areas or [],
        }
    )
    logger.info("Analytics generated", period_days=period_days)
    return analytics


@router.get("/summary", response_model=GovernanceSummary)
async def get_summary(
    agent: GovernanceAnalyticsAgent = Depends(get_governance_analytics)  # noqa: B008
) -> GovernanceSummary:
    """Get a quick governance summary.

    Args:
        agent: The governance analytics agent.

    Returns:
        Governance summary.
    """
    summary = await agent.get_summary()
    logger.info("Governance summary generated")
    return summary
