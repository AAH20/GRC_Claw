"""SerpAPI integration for search engine results and competitor research."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class SerpAPIClient:
    """Client for interacting with the SerpAPI service.

    Provides methods to fetch search engine results, extract competitor
    data, and gather keyword information.
    """

    BASE_URL = "https://serpapi.com/search.json"

    def __init__(
        self,
        api_key: str,
        *,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the SerpAPI client.

        Args:
            api_key: SerpAPI API key.
            timeout: HTTP request timeout in seconds.
        """
        self._api_key = api_key
        self._timeout = timeout

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def search(
        self,
        query: str,
        *,
        location: str = "us",
        language: str = "en",
        num_results: int = 10,
    ) -> dict[str, Any]:
        """Perform a search via SerpAPI.

        Args:
            query: Search query string.
            location: Geographic location code.
            language: Language code.
            num_results: Number of results to return.

        Returns:
            Parsed JSON response from SerpAPI.

        Raises:
            ValueError: If the query is empty.
            RuntimeError: If the API request fails after retries.
        """
        if not query or not query.strip():
            raise ValueError("Search query must not be empty")

        params = {
            "q": query,
            "api_key": self._api_key,
            "num": num_results,
            "gl": location,
            "hl": language,
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error("SerpAPI HTTP error %s: %s", exc.response.status_code, exc.response.text)
            raise RuntimeError(f"SerpAPI request failed: {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            logger.error("SerpAPI request error: %s", exc)
            raise RuntimeError(f"SerpAPI request failed: {exc}") from exc

    async def get_related_searches(self, query: str, *, location: str = "us") -> list[str]:
        """Get related search queries for a given topic.

        Args:
            query: Base search query.
            location: Geographic location.

        Returns:
            List of related search query strings.
        """
        data = await self.search(query, location=location)
        related = data.get("related_searches", [])
        return [item["query"] for item in related if isinstance(item, dict) and "query" in item]

    async def get_people_also_ask(
        self, query: str, *, location: str = "us"
    ) -> list[dict[str, Any]]:
        """Get "People Also Ask" questions for a given topic.

        Args:
            query: Base search query.
            location: Geographic location.

        Returns:
            List of PAA dictionaries with question and answer.
        """
        data = await self.search(query, location=location)
        paa = data.get("people_also_ask", [])
        return [item for item in paa if isinstance(item, dict) and "question" in item]

    async def get_competitors(self, query: str, *, location: str = "us") -> list[dict[str, Any]]:
        """Get competitor information from organic search results.

        Args:
            query: Search query.
            location: Geographic location.

        Returns:
            List of competitor dictionaries with title, url, snippet, and position.
        """
        data = await self.search(query, location=location)
        organic = data.get("organic_results", [])

        competitors: list[dict[str, Any]] = []
        for result in organic[:10]:
            competitors.append(
                {
                    "title": result.get("title", ""),
                    "url": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "position": result.get("position", 0),
                }
            )

        return competitors
