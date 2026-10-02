"""Twitter/X platform integration."""

from typing import Any

import structlog

from creator_analytics.integrations.base import BaseIntegration

logger = structlog.get_logger(__name__)


class TwitterIntegration(BaseIntegration):
    """Twitter API v2 integration."""

    def __init__(self, bearer_token: str) -> None:
        """Initialize Twitter integration.

        Args:
            bearer_token: Twitter API bearer token.
        """
        super().__init__(api_key=bearer_token, base_url="https://api.twitter.com/2")

    def _get_headers(self) -> dict[str, str]:
        """Get request headers for Twitter API.

        Returns:
            Headers dictionary.
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def fetch_analytics(self, creator_id: str) -> dict[str, Any]:
        """Fetch Twitter account analytics.

        Args:
            creator_id: Twitter user ID.

        Returns:
            Account analytics data.
        """
        try:
            client = await self._get_client()
            response = await client.get(
                f"/users/{creator_id}",
                params={
                    "user.fields": "public_metrics,description,verified",
                },
            )
            response.raise_for_status()
            data = response.json()

            user = data.get("data", {})
            metrics = user.get("public_metrics", {})

            return {
                "platform": "twitter",
                "creator_id": creator_id,
                "username": user.get("username", ""),
                "followers_count": metrics.get("followers_count", 0),
                "following_count": metrics.get("following_count", 0),
                "tweet_count": metrics.get("tweet_count", 0),
                "listed_count": metrics.get("listed_count", 0),
            }
        except Exception as e:
            logger.error(f"Failed to fetch Twitter analytics: {e}")
            raise

    async def fetch_content_performance(self, content_ids: list[str]) -> list[dict[str, Any]]:
        """Fetch Twitter tweet performance data.

        Args:
            content_ids: List of tweet IDs.

        Returns:
            List of tweet performance data.
        """
        try:
            client = await self._get_client()
            ids = ",".join(content_ids)
            response = await client.get(
                "/tweets",
                params={
                    "ids": ids,
                    "tweet.fields": "public_metrics,created_at",
                },
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for tweet in data.get("data", []):
                metrics = tweet.get("public_metrics", {})
                results.append({
                    "content_id": tweet["id"],
                    "created_at": tweet.get("created_at", ""),
                    "retweet_count": metrics.get("retweet_count", 0),
                    "reply_count": metrics.get("reply_count", 0),
                    "like_count": metrics.get("like_count", 0),
                    "quote_count": metrics.get("quote_count", 0),
                })

            return results
        except Exception as e:
            logger.error(f"Failed to fetch Twitter content performance: {e}")
            raise
