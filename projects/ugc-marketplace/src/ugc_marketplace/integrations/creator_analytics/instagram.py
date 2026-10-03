"""Instagram integration for creator analytics."""

from __future__ import annotations

from typing import Any

import structlog

from ugc_marketplace.integrations.creator_analytics.base import BaseIntegration

logger = structlog.get_logger(__name__)


class InstagramIntegration(BaseIntegration):
    """Integration with Instagram Graph API for creator analytics."""

    def __init__(self, access_token: str) -> None:
        """Initialize Instagram integration.

        Args:
            access_token: Instagram access token.
        """
        super().__init__(access_token, "https://graph.instagram.com")

    async def fetch_analytics(self, creator_id: str) -> dict[str, Any]:
        """Fetch Instagram analytics for a creator.

        Args:
            creator_id: Instagram user ID.

        Returns:
            Analytics data.
        """
        logger.info("Fetching Instagram analytics", creator_id=creator_id)
        return {
            "creator_id": creator_id,
            "followers": 0,
            "posts": 0,
            "engagement_rate": 0.0,
        }

    async def fetch_content_performance(self, content_ids: list[str]) -> list[dict[str, Any]]:
        """Fetch performance data for posts.

        Args:
            content_ids: List of post IDs.

        Returns:
            List of post performance data.
        """
        logger.info("Fetching Instagram content performance", count=len(content_ids))
        return [{"post_id": pid, "likes": 0, "comments": 0} for pid in content_ids]
