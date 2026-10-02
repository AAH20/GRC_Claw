"""TikTok platform integration."""

from typing import Any

import structlog

from creator_analytics.integrations.base import BaseIntegration

logger = structlog.get_logger(__name__)


class TikTokIntegration(BaseIntegration):
    """TikTok API integration."""

    def __init__(self, access_token: str) -> None:
        """Initialize TikTok integration.

        Args:
            access_token: TikTok API access token.
        """
        super().__init__(api_key=access_token, base_url="https://open-api.tiktok.com")

    async def fetch_analytics(self, creator_id: str) -> dict[str, Any]:
        """Fetch TikTok account analytics.

        Args:
            creator_id: TikTok user ID.

        Returns:
            Account analytics data.
        """
        try:
            client = await self._get_client()
            response = await client.get(
                "/user/info/",
                params={
                    "fields": "open_id,union_id,avatar_url,display_name",
                },
            )
            response.raise_for_status()
            data = response.json()

            user_data = data.get("data", {}).get("user", {})
            return {
                "platform": "tiktok",
                "creator_id": creator_id,
                "display_name": user_data.get("display_name", ""),
                "follower_count": user_data.get("follower_count", 0),
                "following_count": user_data.get("following_count", 0),
                "video_count": user_data.get("video_count", 0),
            }
        except Exception as e:
            logger.error(f"Failed to fetch TikTok analytics: {e}")
            raise

    async def fetch_content_performance(self, content_ids: list[str]) -> list[dict[str, Any]]:
        """Fetch TikTok video performance data.

        Args:
            content_ids: List of TikTok video IDs.

        Returns:
            List of video performance data.
        """
        try:
            client = await self._get_client()
            results = []

            for video_id in content_ids:
                response = await client.get(
                    "/video/data/",
                    params={
                        "item_ids": [video_id],
                        "fields": "id,title,like_count,comment_count,share_count,view_count",
                    },
                )
                response.raise_for_status()
                data = response.json()

                for item in data.get("data", {}).get("videos", []):
                    results.append({
                        "content_id": item["id"],
                        "title": item.get("title", ""),
                        "views": item.get("view_count", 0),
                        "likes": item.get("like_count", 0),
                        "comments": item.get("comment_count", 0),
                        "shares": item.get("share_count", 0),
                    })

            return results
        except Exception as e:
            logger.error(f"Failed to fetch TikTok content performance: {e}")
            raise
