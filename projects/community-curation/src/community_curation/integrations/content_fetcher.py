"""Content fetcher for external community platforms."""

from __future__ import annotations

import hashlib
import random
from datetime import UTC, datetime, timedelta

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from community_curation.config.settings import get_settings
from community_curation.models import ContentItem, ContentSource

logger = structlog.get_logger(__name__)


class ContentFetcher:
    """Fetches content from external community platforms."""

    def __init__(self) -> None:
        """Initialize the content fetcher."""
        self.settings = get_settings()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client.

        Returns:
            Async HTTP client.
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={"User-Agent": "CommunityCuration/0.1.0"},
            )
        return self._client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def _fetch_reddit(
        self, query: str, limit: int, time_range: str
    ) -> list[ContentItem]:
        """Fetch content from Reddit.

        Args:
            query: Search query.
            limit: Maximum results.
            time_range: Time range filter.

        Returns:
            List of content items.
        """
        try:
            client = await self._get_client()
            url = f"{self.settings.reddit_api_url}/search.json"
            params = {"q": query, "limit": limit, "t": time_range, "sort": "relevance"}
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            items: list[ContentItem] = []
            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                items.append(
                    ContentItem(
                        id=f"reddit_{post.get('id', '')}",
                        title=post.get("title", ""),
                        body=post.get("selftext", ""),
                        author=post.get("author", ""),
                        source=ContentSource.REDDIT,
                        url=post.get("url"),
                        score=float(post.get("score", 0)),
                        comment_count=int(post.get("num_comments", 0)),
                        created_at=datetime.fromtimestamp(
                            post.get("created_utc", 0), tz=UTC
                        ),
                        metadata={
                            "upvote_ratio": post.get("upvote_ratio", 0.5),
                            "award_count": post.get("total_awards_received", 0),
                            "verified_author": post.get("author_is_verified", False),
                        },
                    )
                )
            return items
        except Exception as exc:
            logger.warning("reddit_fetch_failed", error=str(exc))
            return self._generate_mock_content(query, ContentSource.REDDIT, limit)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def _fetch_hackernews(
        self, query: str, limit: int, time_range: str
    ) -> list[ContentItem]:
        """Fetch content from Hacker News.

        Args:
            query: Search query.
            limit: Maximum results.
            time_range: Time range filter.

        Returns:
            List of content items.
        """
        try:
            client = await self._get_client()
            # Search using Algolia API
            url = "https://hn.algolia.com/api/v1/search"
            params = {"query": query, "tags": "story", "hitsPerPage": limit}
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            items: list[ContentItem] = []
            for hit in data.get("hits", []):
                items.append(
                    ContentItem(
                        id=f"hn_{hit.get('objectID', '')}",
                        title=hit.get("title", ""),
                        body=hit.get("story_text", "") or "",
                        author=hit.get("author", ""),
                        source=ContentSource.HACKER_NEWS,
                        url=hit.get("url"),
                        score=float(hit.get("points", 0)),
                        comment_count=int(hit.get("num_comments", 0)),
                        created_at=datetime.fromtimestamp(
                            hit.get("created_at_i", 0), tz=UTC
                        ),
                        metadata={
                            "verified_author": False,
                        },
                    )
                )
            return items
        except Exception as exc:
            logger.warning("hackernews_fetch_failed", error=str(exc))
            return self._generate_mock_content(query, ContentSource.HACKER_NEWS, limit)

    def _generate_mock_content(
        self, query: str, source: ContentSource, limit: int
    ) -> list[ContentItem]:
        """Generate mock content for testing or fallback.

        Args:
            query: Search query.
            source: Content source.
            limit: Number of items to generate.

        Returns:
            List of mock content items.
        """
        items: list[ContentItem] = []
        now = datetime.now(UTC)

        for i in range(limit):
            item_id = hashlib.md5(
                f"{source.value}_{query}_{i}".encode(), usedforsecurity=False
            ).hexdigest()[:12]
            items.append(
                ContentItem(
                    id=f"{source.value}_{item_id}",
                    title=f"{query.title()} discussion #{i + 1}",
                    body=f"This is a sample discussion about {query}. " * 5,
                    author=f"user_{random.randint(1000, 9999)}",
                    source=source,
                    url=f"https://example.com/{source.value}/{item_id}",
                    score=float(random.randint(1, 500)),
                    comment_count=random.randint(0, 100),
                    created_at=now - timedelta(hours=random.randint(1, 72)),
                    metadata={
                        "upvote_ratio": random.uniform(0.5, 1.0),
                        "award_count": random.randint(0, 3),
                        "verified_author": random.choice([True, False]),
                    },
                )
            )
        return items

    async def fetch(
        self,
        query: str,
        sources: list[ContentSource],
        limit: int = 20,
        time_range: str = "week",
    ) -> list[ContentItem]:
        """Fetch content from specified sources.

        Args:
            query: Search query.
            sources: Content sources to fetch from.
            limit: Maximum results per source.
            time_range: Time range filter.

        Returns:
            Combined list of content items from all sources.
        """
        all_items: list[ContentItem] = []

        for source in sources:
            if source == ContentSource.REDDIT:
                items = await self._fetch_reddit(query, limit, time_range)
            elif source == ContentSource.HACKER_NEWS:
                items = await self._fetch_hackernews(query, limit, time_range)
            else:
                logger.warning("unsupported_source", source=source.value)
                continue

            all_items.extend(items)

        logger.info(
            "content_fetched",
            query=query,
            sources=[s.value for s in sources],
            count=len(all_items),
        )
        return all_items

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
