"""Integration clients for external services."""

from __future__ import annotations

import time
from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger()


class VectorStoreClient:
    """Client for vector similarity search backend."""

    def __init__(self, base_url: str, api_key: str | None = None) -> None:
        """Initialize the vector store client.

        Args:
            base_url: Base URL of the vector store service.
            api_key: Optional API key for authentication.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            headers=self._build_headers(),
        )

    def _build_headers(self) -> dict[str, str]:
        """Build request headers.

        Returns:
            dict[str, str]: Request headers.
        """
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search the vector store for similar content.

        Args:
            query: Search query text.
            limit: Maximum number of results.
            filters: Optional metadata filters.

        Returns:
            list[dict[str, Any]]: Search results.
        """
        try:
            response = await self._client.post(
                "/search",
                json={
                    "query": query,
                    "limit": limit,
                    "filters": filters or {},
                },
            )
            response.raise_for_status()
            return response.json().get("results", [])
        except httpx.HTTPError as exc:
            logger.error("vector_store_search_failed", error=str(exc))
            return []

    async def upsert(self, documents: list[dict[str, Any]]) -> bool:
        """Insert or update documents in the vector store.

        Args:
            documents: Documents to upsert.

        Returns:
            bool: True if successful.
        """
        try:
            response = await self._client.post("/upsert", json={"documents": documents})
            response.raise_for_status()
            return True
        except httpx.HTTPError as exc:
            logger.error("vector_store_upsert_failed", error=str(exc))
            return False

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()


class UserProfileClient:
    """Client for user profile and history data."""

    def __init__(self, redis_url: str) -> None:
        """Initialize the user profile client.

        Args:
            redis_url: Redis connection URL.
        """
        self.redis_url = redis_url
        self._client: Any = None

    async def _get_client(self) -> Any:
        """Get or create Redis client.

        Returns:
            Any: Redis client instance.
        """
        if self._client is None:
            import redis.asyncio as aioredis

            self._client = aioredis.from_url(self.redis_url, decode_responses=True)
        return self._client

    async def get_history(
        self, user_id: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get user's content interaction history.

        Args:
            user_id: User identifier.
            limit: Maximum number of history items.

        Returns:
            list[dict[str, Any]]: User history items.
        """
        try:
            client = await self._get_client()
            key = f"user:{user_id}:history"
            items = await client.lrange(key, 0, limit - 1)
            import json

            return [json.loads(item) for item in items if item]
        except Exception as exc:
            logger.error("get_history_failed", user_id=user_id, error=str(exc))
            return []

    async def add_history(self, user_id: str, item: dict[str, Any]) -> bool:
        """Add an item to user's history.

        Args:
            user_id: User identifier.
            item: History item to add.

        Returns:
            bool: True if successful.
        """
        try:
            client = await self._get_client()
            key = f"user:{user_id}:history"
            import json

            await client.lpush(key, json.dumps(item))
            await client.ltrim(key, 0, 99)  # Keep last 100 items
            return True
        except Exception as exc:
            logger.error("add_history_failed", user_id=user_id, error=str(exc))
            return False

    async def get_similar_users(self, user_id: str, limit: int = 10) -> list[str]:
        """Find users with similar preferences.

        Args:
            user_id: Target user identifier.
            limit: Maximum number of similar users.

        Returns:
            list[str]: Similar user IDs.
        """
        try:
            client = await self._get_client()
            key = f"user:{user_id}:similar"
            return await client.smembers(key)
        except Exception as exc:
            logger.error("get_similar_users_failed", user_id=user_id, error=str(exc))
            return []

    async def get_candidates(
        self,
        topics: list[str],
        content_types: list[str],
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get candidate content based on topics and content types.

        Args:
            topics: Topics to match.
            content_types: Content types to match.
            limit: Maximum number of candidates.

        Returns:
            list[dict[str, Any]]: Candidate content items.
        """
        try:
            client = await self._get_client()
            results = []
            for topic in topics:
                key = f"topic:{topic}"
                items = await client.smembers(key)
                for item_id in list(items)[:limit]:
                    data = await client.hgetall(f"content:{item_id}")
                    if data:
                        results.append(data)
            return results[:limit]
        except Exception as exc:
            logger.error("get_candidates_failed", error=str(exc))
            return []

    async def close(self) -> None:
        """Close the Redis client."""
        if self._client:
            await self._client.close()


class AnalyticsClient:
    """Client for analytics and metrics data."""

    def __init__(self, base_url: str) -> None:
        """Initialize the analytics client.

        Args:
            base_url: Base URL of the analytics service.
        """
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def get_volume(
        self, topic: str, days: int = 7
    ) -> list[dict[str, Any]]:
        """Get search volume data for a topic.

        Args:
            topic: Topic or keyword.
            days: Number of days to analyze.

        Returns:
            list[dict[str, Any]]: Daily volume data points.
        """
        try:
            response = await self._client.get(
                "/volume",
                params={"topic": topic, "days": days},
            )
            response.raise_for_status()
            return response.json().get("data", [])
        except httpx.HTTPError as exc:
            logger.error("get_volume_failed", topic=topic, error=str(exc))
            return []

    async def get_related_topics(self, topic: str) -> list[str]:
        """Get topics related to a given topic.

        Args:
            topic: Base topic.

        Returns:
            list[str]: Related topic strings.
        """
        try:
            response = await self._client.get(
                "/related",
                params={"topic": topic},
            )
            response.raise_for_status()
            return response.json().get("topics", [])
        except httpx.HTTPError as exc:
            logger.error("get_related_topics_failed", topic=topic, error=str(exc))
            return []

    async def get_top_topics(self, days: int = 7, limit: int = 20) -> list[str]:
        """Get top trending topics.

        Args:
            days: Analysis window in days.
            limit: Maximum number of topics.

        Returns:
            list[str]: Top topic strings.
        """
        try:
            response = await self._client.get(
                "/top",
                params={"days": days, "limit": limit},
            )
            response.raise_for_status()
            return response.json().get("topics", [])
        except httpx.HTTPError as exc:
            logger.error("get_top_topics_failed", error=str(exc))
            return []

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()


class ContentClient:
    """Client for content data and features."""

    def __init__(self, base_url: str) -> None:
        """Initialize the content client.

        Args:
            base_url: Base URL of the content service.
        """
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def get_features(self, content_id: str) -> dict[str, Any]:
        """Get features and metadata for a content item.

        Args:
            content_id: Content identifier.

        Returns:
            dict[str, Any]: Content features.
        """
        try:
            response = await self._client.get(f"/content/{content_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            logger.error("get_features_failed", content_id=content_id, error=str(exc))
            return {}

    async def get_by_tags(
        self, tags: list[str], limit: int = 20
    ) -> list[dict[str, Any]]:
        """Get content items by tags.

        Args:
            tags: Tags to match.
            limit: Maximum number of items.

        Returns:
            list[dict[str, Any]]: Content items.
        """
        try:
            response = await self._client.post(
                "/content/search",
                json={"tags": tags, "limit": limit},
            )
            response.raise_for_status()
            return response.json().get("results", [])
        except httpx.HTTPError as exc:
            logger.error("get_by_tags_failed", error=str(exc))
            return []

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
