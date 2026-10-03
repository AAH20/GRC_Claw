"""TikTok integration for creator analytics."""

from __future__ import annotations

from typing import Any

import structlog

from ugc_marketplace.integrations.creator_analytics.base import BaseIntegration

logger = structlog.get_logger(__name__)


class TikTokIntegration(BaseIntegration):
    """Integration with TikTok API for creator analytics."""

    def __init__(self, access_token: str) -> None:
        """Initialize TikTok integration.

        Args:
            access_token: TikTok access token.
        """
        super().__init__(access_token, "https://open-api.tiktok.com")

    async def fetch_analytics(self, creator_id: str) -> dict[str, Any]:
        """Fetch TikTok analytics for a creator.

        Args:
            creator_id: TikTok user ID.

        Returns:
            Analytics data.
        """
        logger.info("Fetching TikTok analytics", creator_id=creator_id)
        return {
            "creator_id": creator_id,
            "followers": 0,
            "videos": 0,
            "total_likes": 0,
        }

    async def fetch_content_performance(self, content_ids: list[str]) -> list[dict[str, Any]]:
        """Fetch performance data for videos.

        Args:
            content_ids: List of video IDs.

        Returns:
            List of video performance data.
        """
        logger.info("Fetching TikTok content performance", count=len(content_ids))
        return [{"video_id": vid, "views": 0, "likes": 0} for vid in content_ids]
