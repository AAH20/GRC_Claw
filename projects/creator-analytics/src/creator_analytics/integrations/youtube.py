"""YouTube platform integration."""

from typing import Any
import structlog

from creator_analytics.integrations.base import BaseIntegration

logger = structlog.get_logger(__name__)


class YouTubeIntegration(BaseIntegration):
    """YouTube Data API integration."""

    def __init__(self, api_key: str) -> None:
        """Initialize YouTube integration.

        Args:
            api_key: YouTube Data API key.
        """
        super().__init__(api_key=api_key, base_url="https://www.googleapis.com/youtube/v3")

    async def fetch_analytics(self, creator_id: str) -> dict[str, Any]:
        """Fetch YouTube channel analytics.

        Args:
            creator_id: YouTube channel ID.

        Returns:
            Channel analytics data.
        """
        try:
            client = await self._get_client()
            response = await client.get(
                "/channels",
                params={
                    "part": "snippet,statistics",
                    "id": creator_id,
                },
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("items"):
                logger.warning(f"No YouTube channel found for {creator_id}")
                return {}

            channel = data["items"][0]
            return {
                "platform": "youtube",
                "creator_id": creator_id,
                "title": channel["snippet"]["title"],
                "subscriber_count": int(channel["statistics"].get("subscriberCount", 0)),
                "video_count": int(channel["statistics"].get("videoCount", 0)),
                "view_count": int(channel["statistics"].get("viewCount", 0)),
            }
        except Exception as e:
            logger.error(f"Failed to fetch YouTube analytics: {e}")
            raise

    async def fetch_content_performance(self, content_ids: list[str]) -> list[dict[str, Any]]:
        """Fetch YouTube video performance data.

        Args:
            content_ids: List of YouTube video IDs.

        Returns:
            List of video performance data.
        """
        try:
            client = await self._get_client()
            ids = ",".join(content_ids)
            response = await client.get(
                "/videos",
                params={
                    "part": "snippet,statistics",
                    "id": ids,
                },
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get("items", []):
                results.append({
                    "content_id": item["id"],
                    "title": item["snippet"]["title"],
                    "views": int(item["statistics"].get("viewCount", 0)),
                    "likes": int(item["statistics"].get("likeCount", 0)),
                    "comments": int(item["statistics"].get("commentCount", 0)),
                })
            return results
        except Exception as e:
            logger.error(f"Failed to fetch YouTube content performance: {e}")
            raise
