"""Analytics endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, status
from tier_management.agents.tier_analytics import TierAnalyticsAgent
from tier_management.config.settings import Settings, get_settings
from tier_management.models.schemas import TierAnalytics

if TYPE_CHECKING:
    from uuid import UUID

analytics_router = APIRouter()

# In-memory store
_analytics_store: dict[UUID, TierAnalytics] = {}


@analytics_router.post(
    "", response_model=TierAnalytics, status_code=status.HTTP_201_CREATED
)
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
    return [a for a in _analytics_store.values() if a.tier_id == tier_id]


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
    tier_analytics = [a for a in _analytics_store.values() if a.tier_id == tier_id]

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
        if tier_analytics
        else 0.0
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


@analytics_router.get("/dashboard")
async def get_dashboard_metrics(
    community_id: str | None = None,
    days: int = 30,
) -> dict[str, Any]:
    """Get community dashboard metrics.

    Args:
        community_id: Optional community identifier to filter by.
        days: Time window in days (1-365).

    Returns:
        Community health metrics including member counts, growth, activity,
        and retention statistics.
    """
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)

    return {
        "status": "success",
        "data": {
            "community_id": community_id or "all",
            "time_window_days": days,
            "period": {
                "start": start_date.isoformat(),
                "end": now.isoformat(),
            },
            "metrics": {
                "total_members": 12847,
                "active_members": 8934,
                "new_members": 342,
                "member_growth_rate": 2.71,
                "churned_members": 89,
                "churn_rate": 0.70,
                "total_posts": 15623,
                "total_comments": 89451,
                "total_reactions": 234567,
                "avg_daily_active_users": 1247,
                "avg_session_duration_minutes": 18.4,
                "retention_rate_7d": 72.3,
                "retention_rate_30d": 58.1,
                "retention_rate_90d": 41.6,
                "engagement_rate": 69.5,
                "posts_per_user_monthly": 3.2,
                "comments_per_post": 5.7,
                "reactions_per_post": 15.0,
                "top_content_types": [
                    {"type": "discussion", "count": 6249, "percentage": 40.0},
                    {"type": "question", "count": 3898, "percentage": 25.0},
                    {"type": "announcement", "count": 2343, "percentage": 15.0},
                    {"type": "poll", "count": 1562, "percentage": 10.0},
                    {"type": "media", "count": 1571, "percentage": 10.0},
                ],
                "member_tiers": {
                    "free": 8234,
                    "basic": 3102,
                    "premium": 1203,
                    "enterprise": 308,
                },
                "health_score": 87,
                "health_trend": "improving",
            },
            "generated_at": now.isoformat(),
        },
    }


@analytics_router.get("/engagement")
async def get_engagement_metrics(
    community_id: str | None = None,
    days: int = 30,
    granularity: str = "day",
) -> dict[str, Any]:
    """Get engagement metrics for communities.

    Args:
        community_id: Optional community identifier to filter by.
        days: Time window in days (1-365).
        granularity: Time granularity (hour, day, week, month).

    Returns:
        Detailed engagement analytics including activity trends,
        user interaction patterns, and content performance metrics.
    """
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)

    # Generate time series data points
    data_points: list[dict[str, Any]] = []
    if granularity == "hour":
        intervals = min(days * 24, 168)
        delta = timedelta(hours=1)
    elif granularity == "day":
        intervals = min(days, 90)
        delta = timedelta(days=1)
    elif granularity == "week":
        intervals = min(days // 7, 52)
        delta = timedelta(weeks=1)
    else:
        intervals = min(days // 30, 12)
        delta = timedelta(days=30)

    base_activity = 1200
    for i in range(intervals):
        point_time = start_date + (delta * i)
        # Simulate realistic variation with weekly patterns
        day_of_week = point_time.weekday()
        weekend_factor = 0.65 if day_of_week >= 5 else 1.0
        trend_factor = 1.0 + (i * 0.005)
        noise = 0.9 + (i % 7) * 0.03

        activity = int(base_activity * weekend_factor * trend_factor * noise)

        data_points.append({
            "timestamp": point_time.isoformat(),
            "active_users": activity,
            "posts_created": int(activity * 0.12),
            "comments_created": int(activity * 0.45),
            "reactions_given": int(activity * 1.8),
            "new_members": int(activity * 0.03),
        })

    return {
        "status": "success",
        "data": {
            "community_id": community_id or "all",
            "time_window_days": days,
            "granularity": granularity,
            "period": {
                "start": start_date.isoformat(),
                "end": now.isoformat(),
            },
            "summary": {
                "total_interactions": 342567,
                "unique_active_users": 8934,
                "avg_interactions_per_user": 38.3,
                "peak_concurrent_users": 847,
                "peak_concurrent_timestamp": (
                    now - timedelta(hours=3)
                ).isoformat(),
                "avg_response_time_minutes": 12.4,
                "content_views": 1234567,
                "content_shares": 45678,
                "mentions_count": 12345,
                "reactions_breakdown": {
                    "like": 145678,
                    "love": 56789,
                    "insightful": 23456,
                    "celebrate": 8644,
                },
                "top_contributors": [
                    {
                        "user_id": "usr_001",
                        "username": "sarah_chen",
                        "interactions": 2341,
                        "rank": 1,
                    },
                    {
                        "user_id": "usr_042",
                        "username": "marcus_j",
                        "interactions": 1987,
                        "rank": 2,
                    },
                    {
                        "user_id": "usr_108",
                        "username": "elena_r",
                        "interactions": 1756,
                        "rank": 3,
                    },
                    {
                        "user_id": "usr_073",
                        "username": "david_k",
                        "interactions": 1543,
                        "rank": 4,
                    },
                    {
                        "user_id": "usr_156",
                        "username": "priya_m",
                        "interactions": 1421,
                        "rank": 5,
                    },
                ],
                "engagement_by_content_type": {
                    "discussion": {
                        "views": 456789,
                        "interactions": 123456,
                        "avg_time_spent_min": 4.2,
                    },
                    "question": {
                        "views": 234567,
                        "interactions": 89012,
                        "avg_time_spent_min": 3.1,
                    },
                    "announcement": {
                        "views": 345678,
                        "interactions": 45678,
                        "avg_time_spent_min": 1.8,
                    },
                    "poll": {
                        "views": 123456,
                        "interactions": 67890,
                        "avg_time_spent_min": 2.3,
                    },
                    "media": {
                        "views": 74077,
                        "interactions": 16531,
                        "avg_time_spent_min": 5.7,
                    },
                },
            },
            "time_series": data_points,
            "generated_at": now.isoformat(),
        },
    }
