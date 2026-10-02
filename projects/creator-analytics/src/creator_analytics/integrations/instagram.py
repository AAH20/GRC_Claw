"""Instagram platform integration."""

from typing import Any
import structlog

from creator_analytics.integrations.base import BaseIntegration

logger = structlog.get_logger(__name__)


class InstagramIntegration(BaseIntegration):
    """Instagram Graph API integration."""

    def __init__(self, access_token: str) -> None:
        """Initialize Instagram integration.

        Args:
            access_token: Instagram Graph API access token.
        """
        super().__init__(api_key=access_token, base_url="https://graph.instagram.com")

    async def fetch_analytics(self, creator_id: str) -> dict[str, Any]:
        """Fetch Instagram account analytics.

        Args:
            creator_id: Instagram user ID.

        Returns:
            Account analytics data.
        """
        try:
            client = await self._get_client()
            response = await client.get(
                f"/{creator_id}",
                params={
                    "fields": "id,username,media_count,followers_count,follows_count",
                },
            )
            response.raise_for_status()
            data = response.json()

            return {
                "platform": "instagram",
                "creator_id": creator_id,
                "username": data.get("username", ""),
                "media_count": data.get("media_count", 0),
                "followers_count": data.get("followers_count", 0),
                "follows_count": data.get("follows_count", 0),
            }
        except Exception as e:
            logger.error(f"Failed to fetch Instagram analytics: {e}")
            raise

    async def fetch_content_performance(self, content_ids: list[str]) -> list[dict[str, Any]]:
        """Fetch Instagram media performance data.

        Args:
            content_ids: List of Instagram media IDs.

        Returns:
            List of media performance data.
        """
        try:
            client = await self._get_client()
            results = []

            for media_id in content_ids:
                response = await client.get(
                    f"/{media_id}",
                    params={
                        "fields": "id,caption,media_type,like_count,comments_count",
                    },
                )
                response.raise_for_status()
                data = response.json()

                results.append({
                    "content_id": data["id"],
                    "media_type": data.get("media_type", ""),
                    "likes": data.get("like_count", 0),
                    "comments": data.get("comments_count", 0),
                })

            return results
        except Exception as e:
            logger.error(f"Failed to fetch Instagram content performance: {e}")
            raise
