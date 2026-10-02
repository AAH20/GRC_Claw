"""Researcher agent — gathers SERP data, competitor insights, and trending topics."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


@dataclass
class ResearchResult:
    """Output from the Researcher agent."""

    query: str
    serp_data: dict[str, Any] = field(default_factory=dict)
    competitors: list[dict[str, Any]] = field(default_factory=list)
    trending_topics: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    summary: str = ""


class ResearcherAgent:
    """Agent responsible for gathering research data via SerpAPI and web search.

    Uses SerpAPI to fetch search engine results, extract competitor insights,
    and identify trending topics relevant to the content brief.
    """

    SERPAPI_BASE_URL = "https://serpapi.com/search.json"

    def __init__(
        self,
        serpapi_key: str,
        *,
        max_results: int = 10,
        search_depth: str = "deep",
        timeout: float = 30.0,
    ) -> None:
        """Initialize the Researcher agent.

        Args:
            serpapi_key: SerpAPI API key.
            max_results: Maximum number of SERP results to fetch.
            search_depth: Search depth — 'basic' or 'deep'.
            timeout: HTTP request timeout in seconds.
        """
        self._serpapi_key = serpapi_key
        self._max_results = max_results
        self._search_depth = search_depth
        self._timeout = timeout

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def research(self, query: str, *, location: str = "us") -> ResearchResult:
        """Perform research for a given query.

        Args:
            query: The search query or topic to research.
            location: Geographic location for SERP results.

        Returns:
            ResearchResult containing SERP data, competitors, and keywords.

        Raises:
            ValueError: If the query is empty.
            RuntimeError: If the SerpAPI request fails after retries.
        """
        if not query or not query.strip():
            raise ValueError("Query must not be empty")

        logger.info("Starting research for query: %s", query)

        serp_data = await self._fetch_serp(query, location=location)
        competitors = self._extract_competitors(serp_data)
        trending_topics = self._extract_trending_topics(serp_data)
        keywords = self._extract_keywords(serp_data)
        summary = self._summarize(serp_data)

        result = ResearchResult(
            query=query,
            serp_data=serp_data,
            competitors=competitors,
            trending_topics=trending_topics,
            keywords=keywords,
            summary=summary,
        )

        logger.info(
            "Research complete: %d competitors, %d trending topics, %d keywords",
            len(competitors),
            len(trending_topics),
            len(keywords),
        )
        return result

    async def _fetch_serp(self, query: str, *, location: str) -> dict[str, Any]:
        """Fetch SERP data from SerpAPI.

        Args:
            query: Search query.
            location: Geographic location.

        Returns:
            Parsed JSON response from SerpAPI.

        Raises:
            RuntimeError: If the API request fails.
        """
        params = {
            "q": query,
            "api_key": self._serpapi_key,
            "num": self._max_results,
            "gl": location,
            "hl": "en",
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(self.SERPAPI_BASE_URL, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error("SerpAPI HTTP error: %s", exc.response.status_code)
            raise RuntimeError(f"SerpAPI request failed: {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            logger.error("SerpAPI request error: %s", exc)
            raise RuntimeError(f"SerpAPI request failed: {exc}") from exc

    def _extract_competitors(self, serp_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract competitor information from SERP data.

        Args:
            serp_data: Raw SERP API response.

        Returns:
            List of competitor dictionaries with title, url, and snippet.
        """
        competitors: list[dict[str, Any]] = []
        organic_results = serp_data.get("organic_results", [])

        for result in organic_results[:5]:
            competitors.append(
                {
                    "title": result.get("title", ""),
                    "url": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "position": result.get("position", 0),
                }
            )

        return competitors

    def _extract_trending_topics(self, serp_data: dict[str, Any]) -> list[str]:
        """Extract trending topics from SERP data.

        Args:
            serp_data: Raw SERP API response.

        Returns:
            List of trending topic strings.
        """
        topics: list[str] = []

        # Extract from related searches
        related = serp_data.get("related_searches", [])
        for item in related:
            if isinstance(item, dict) and "query" in item:
                topics.append(item["query"])

        # Extract from "people also ask"
        paa = serp_data.get("people_also_ask", [])
        for item in paa:
            if isinstance(item, dict) and "question" in item:
                topics.append(item["question"])

        return topics[:10]

    def _extract_keywords(self, serp_data: dict[str, Any]) -> list[str]:
        """Extract keywords from SERP data.

        Args:
            serp_data: Raw SERP API response.

        Returns:
            List of keyword strings.
        """
        keywords: list[str] = []

        # Extract from related searches
        related = serp_data.get("related_searches", [])
        for item in related:
            if isinstance(item, dict) and "query" in item:
                keywords.append(item["query"])

        # Extract from organic results titles
        organic = serp_data.get("organic_results", [])
        for result in organic:
            title = result.get("title", "")
            if title:
                # Simple keyword extraction from title
                words = title.split()
                keywords.extend(words[:3])

        return list(set(keywords))[:15]

    def _summarize(self, serp_data: dict[str, Any]) -> str:
        """Generate a brief summary of the research.

        Args:
            serp_data: Raw SERP API response.

        Returns:
            Summary string.
        """
        organic = serp_data.get("organic_results", [])
        if not organic:
            return "No results found."

        top_result = organic[0]
        return (
            f"Top result: {top_result.get('title', 'N/A')} — "
            f"{top_result.get('snippet', 'N/A')[:200]}"
        )
