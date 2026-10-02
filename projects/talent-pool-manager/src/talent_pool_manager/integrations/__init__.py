"""External service integrations for talent pool manager."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Protocol

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from talent_pool_manager.config import get_settings
from talent_pool_manager.config.logging_config import get_logger

logger = get_logger(__name__)


class SearchResult(Protocol):
    """Protocol for search results from external sources."""

    name: str
    email: str | None
    profile_url: str | None
    source: str
    metadata: dict[str, Any]


class BaseIntegration(ABC):
    """Base class for external service integrations."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create an async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                headers=self._get_headers(),
            )
        return self._client

    @abstractmethod
    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for API requests."""
        ...

    @abstractmethod
    async def search(
        self, query: str, max_results: int = 50, **kwargs: Any
    ) -> list[dict[str, Any]]:
        """Search for candidates on the external platform."""
        ...

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


class LinkedInIntegration(BaseIntegration):
    """LinkedIn API integration for candidate discovery."""

    BASE_URL = "https://api.linkedin.com/v2"

    def _get_headers(self) -> dict[str, str]:
        """Get LinkedIn API headers."""
        return {
            "Authorization": f"Bearer {self.settings.linkedin_api_key or ''}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def search(
        self, query: str, max_results: int = 50, **kwargs: Any
    ) -> list[dict[str, Any]]:
        """Search for candidates on LinkedIn.

        Args:
            query: Search query string.
            max_results: Maximum number of results to return.
            **kwargs: Additional search parameters.

        Returns:
            List of candidate profiles.
        """
        client = await self._get_client()
        try:
            response = await client.get(
                f"{self.BASE_URL}/search",
                params={
                    "q": query,
                    "count": min(max_results, 100),
                    "start": kwargs.get("offset", 0),
                },
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_results(data)
        except httpx.HTTPStatusError as e:
            logger.error("LinkedIn API error", status=e.response.status_code, query=query)
            return []

    def _parse_results(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Parse LinkedIn search results into standardized format."""
        results = []
        for element in data.get("elements", []):
            profile = element.get("profile", {})
            results.append({
                "name": profile.get("name", ""),
                "email": profile.get("email"),
                "profile_url": profile.get("url"),
                "headline": profile.get("headline"),
                "location": profile.get("location"),
                "source": "linkedin",
                "metadata": profile.get("metadata", {}),
            })
        return results


class GitHubIntegration(BaseIntegration):
    """GitHub API integration for candidate discovery."""

    BASE_URL = "https://api.github.com"

    def _get_headers(self) -> dict[str, str]:
        """Get GitHub API headers."""
        return {
            "Authorization": f"token {self.settings.github_token or ''}",
            "Accept": "application/vnd.github.v3+json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def search(
        self, query: str, max_results: int = 50, **kwargs: Any
    ) -> list[dict[str, Any]]:
        """Search for developers on GitHub.

        Args:
            query: Search query string.
            max_results: Maximum number of results to return.
            **kwargs: Additional search parameters.

        Returns:
            List of developer profiles.
        """
        client = await self._get_client()
        try:
            response = await client.get(
                f"{self.BASE_URL}/search/users",
                params={
                    "q": query,
                    "per_page": min(max_results, 100),
                    "page": kwargs.get("page", 1),
                },
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_results(data)
        except httpx.HTTPStatusError as e:
            logger.error("GitHub API error", status=e.response.status_code, query=query)
            return []

    def _parse_results(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Parse GitHub search results into standardized format."""
        results = []
        for item in data.get("items", []):
            results.append({
                "name": item.get("login", ""),
                "email": None,
                "profile_url": item.get("html_url"),
                "headline": None,
                "location": None,
                "source": "github",
                "metadata": {
                    "id": item.get("id"),
                    "avatar_url": item.get("avatar_url"),
                    "type": item.get("type"),
                },
            })
        return results


class IndeedIntegration(BaseIntegration):
    """Indeed API integration for candidate discovery."""

    BASE_URL = "https://api.indeed.com/ads/apisearch"

    def _get_headers(self) -> dict[str, str]:
        """Get Indeed API headers."""
        return {
            "Accept": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def search(
        self, query: str, max_results: int = 50, **kwargs: Any
    ) -> list[dict[str, Any]]:
        """Search for job seekers on Indeed.

        Args:
            query: Search query string.
            max_results: Maximum number of results to return.
            **kwargs: Additional search parameters.

        Returns:
            List of candidate profiles.
        """
        client = await self._get_client()
        try:
            response = await client.get(
                self.BASE_URL,
                params={
                    "q": query,
                    "limit": min(max_results, 25),
                    "format": "json",
                    "publisher": self.settings.indeed_api_key or "",
                },
            )
            response.raise_for_status()
            data = response.json()
            return self._parse_results(data)
        except httpx.HTTPStatusError as e:
            logger.error("Indeed API error", status=e.response.status_code, query=query)
            return []

    def _parse_results(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Parse Indeed search results into standardized format."""
        results = []
        for result in data.get("results", []):
            results.append({
                "name": result.get("company", ""),
                "email": None,
                "profile_url": result.get("url"),
                "headline": result.get("jobtitle"),
                "location": result.get("formattedLocation"),
                "source": "indeed",
                "metadata": {
                    "job_key": result.get("jobkey"),
                    "company": result.get("company"),
                },
            })
        return results


class IntegrationManager:
    """Manager for all external service integrations."""

    def __init__(self) -> None:
        self._integrations: dict[str, BaseIntegration] = {}
        self._initialize_integrations()

    def _initialize_integrations(self) -> None:
        """Initialize all available integrations."""
        if self.settings.linkedin_api_key:
            self._integrations["linkedin"] = LinkedInIntegration()
        if self.settings.github_token:
            self._integrations["github"] = GitHubIntegration()
        if self.settings.indeed_api_key:
            self._integrations["indeed"] = IndeedIntegration()

    async def search_all(
        self,
        query: str,
        sources: list[str] | None = None,
        max_results: int = 50,
    ) -> dict[str, list[dict[str, Any]]]:
        """Search across all configured integrations.

        Args:
            query: Search query string.
            sources: List of sources to search. If None, searches all.
            max_results: Maximum results per source.

        Returns:
            Dictionary mapping source names to results.
        """
        sources = sources or list(self._integrations.keys())
        tasks = []
        source_names = []

        for source in sources:
            if source in self._integrations:
                integration = self._integrations[source]
                tasks.append(integration.search(query, max_results))
                source_names.append(source)

        if not tasks:
            return {}

        results = await asyncio.gather(*tasks, return_exceptions=True)

        output: dict[str, list[dict[str, Any]]] = {}
        for source, result in zip(source_names, results, strict=False):
            if isinstance(result, Exception):
                logger.error("Search failed", source=source, error=str(result))
                output[source] = []
            else:
                output[source] = result

        return output

    async def close_all(self) -> None:
        """Close all integration connections."""
        await asyncio.gather(
            *[integration.close() for integration in self._integrations.values()],
            return_exceptions=True,
        )
