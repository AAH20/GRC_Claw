"""Twitter/X API v2 client."""

from __future__ import annotations

from typing import Any

from social_media_manager.integrations.base import BasePlatformClient


class TwitterClient(BasePlatformClient):
    """Client for the Twitter/X v2 API."""

    platform = "twitter"
    base_url = "https://api.twitter.com/2"

    async def post_tweet(self, text: str) -> dict[str, Any]:
        """Publish a tweet.

        Args:
            text: Tweet body (max 280 characters).

        Returns:
            API response containing the new tweet id.

        Raises:
            ValueError: If ``text`` is empty or exceeds the limit.
        """
        text = text.strip()
        if not text:
            raise ValueError("Tweet text cannot be empty")
        if len(text) > 280:
            raise ValueError(f"Tweet exceeds 280 characters ({len(text)})")
        return await self._request("POST", "/tweets", json={"text": text})

    async def get_user(self, username: str) -> dict[str, Any]:
        """Fetch a user profile by username."""
        username = username.lstrip("@").strip()
        if not username:
            raise ValueError("username is required")
        return await self._request(
            "GET",
            f"/users/by/username/{username}",
            params={"user.fields": "public_metrics,description"},
        )

    async def get_user_tweets(self, user_id: str, max_results: int = 10) -> dict[str, Any]:
        """Fetch recent tweets for a user id."""
        if not user_id:
            raise ValueError("user_id is required")
        max_results = max(5, min(int(max_results), 100))
        return await self._request(
            "GET",
            f"/users/{user_id}/tweets",
            params={"max_results": max_results, "tweet.fields": "public_metrics,created_at"},
        )

    async def search_recent(self, query: str, max_results: int = 10) -> dict[str, Any]:
        """Search recent tweets matching a query."""
        if not query.strip():
            raise ValueError("query is required")
        return await self._request(
            "GET",
            "/tweets/search/recent",
            params={"query": query, "max_results": max(10, min(int(max_results), 100))},
        )
