"""Analytics API routes — aggregate stored posts into metrics."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from fastapi import APIRouter, HTTPException

from social_media_manager.agents.performance_analytics import PerformanceAnalyticsAgent
from social_media_manager.api.store import post_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

_analytics_agent = PerformanceAnalyticsAgent()


@router.get("", response_model=dict)
async def get_overview() -> dict[str, Any]:
    """Return an analytics overview aggregated across all platforms."""
    posts = post_store.all_posts()
    by_platform: dict[str, int] = defaultdict(int)
    by_status: dict[str, int] = defaultdict(int)
    for post in posts:
        platform = post["platform"]
        by_platform[platform if isinstance(platform, str) else platform.value] += 1
        status_value = post["status"]
        by_status[status_value if isinstance(status_value, str) else status_value.value] += 1

    return {
        "total_posts": len(posts),
        "posts_by_platform": dict(by_platform),
        "posts_by_status": dict(by_status),
        "platforms_tracked": sorted(by_platform),
    }


@router.get("/{platform}", response_model=dict)
async def get_platform_analytics(platform: str) -> dict[str, Any]:
    """Return performance metrics for a specific platform."""
    platform_key = platform.lower()
    posts = [
        p
        for p in post_store.all_posts()
        if (p["platform"] if isinstance(p["platform"], str) else p["platform"].value)
        == platform_key
    ]
    if not posts:
        raise HTTPException(
            status_code=404, detail=f"No posts found for platform '{platform}'"
        )

    metrics = [
        {
            "impressions": (p.get("metadata") or {}).get("impressions", 0),
            "likes": (p.get("metadata") or {}).get("likes", 0),
            "comments": (p.get("metadata") or {}).get("comments", 0),
            "shares": (p.get("metadata") or {}).get("shares", 0),
        }
        for p in posts
    ]
    result = _analytics_agent.invoke({"posts": metrics, "platform": platform_key})
    if not result.success:
        logger.error("analytics_agent_failed platform=%s error=%s", platform_key, result.error)
        raise HTTPException(status_code=500, detail=result.error or "analytics failed")
    return result.to_dict()
