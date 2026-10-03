"""Search service for ugc-marketplace.

Provides full-text content search, creator search, and autocomplete suggestions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SearchFilters:
    """Filters applicable to search queries."""

    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    rating_min: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    sort_by: str = "relevance"
    limit: int = 20
    offset: int = 0

    def __post_init__(self) -> None:
        if self.limit < 1 or self.limit > 100:
            raise ValueError("limit must be between 1 and 100")
        if self.offset < 0:
            raise ValueError("offset must be non-negative")
        if self.min_price is not None and self.max_price is not None:
            if self.min_price > self.max_price:
                raise ValueError("min_price cannot exceed max_price")
        if self.rating_min is not None and not (0 <= self.rating_min <= 5):
            raise ValueError("rating_min must be between 0 and 5")


@dataclass
class SearchResult:
    """A single search result item."""

    id: str
    title: str
    type: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResponse:
    """Paginated search response."""

    results: List[SearchResult]
    total: int
    query: str
    filters: SearchFilters


@dataclass
class Suggestion:
    """An autocomplete suggestion."""

    text: str
    type: str
    highlight: Optional[str] = None


class SearchServiceError(Exception):
    """Base exception for search service errors."""


class SearchBackendError(SearchServiceError):
    """Raised when the search backend is unavailable or returns an error."""


class SearchService:
    """Service for searching content, creators, and providing suggestions."""

    def __init__(self, backend: Optional[Any] = None) -> None:
        """Initialize the search service.

        Args:
            backend: Optional search backend client (e.g., Elasticsearch, Algolia).
        """
        self._backend = backend

    def search_content(
        self, query: str, filters: Optional[SearchFilters] = None
    ) -> SearchResponse:
        """Perform full-text search over marketplace content.

        Args:
            query: The search query string.
            filters: Optional search filters.

        Returns:
            SearchResponse with matching content items.

        Raises:
            ValueError: If query is empty or invalid.
            SearchBackendError: If the search backend fails.
        """
        if not query or not query.strip():
            raise ValueError("query must be a non-empty string")

        filters = filters or SearchFilters()
        logger.info("Searching content: query=%r filters=%s", query, filters)

        try:
            raw_results = self._execute_content_search(query.strip(), filters)
        except SearchBackendError:
            raise
        except Exception as exc:
            logger.exception("Content search failed for query=%r", query)
            raise SearchBackendError(f"Content search failed: {exc}") from exc

        results = [
            SearchResult(
                id=item["id"],
                title=item["title"],
                type=item.get("type", "content"),
                score=float(item.get("score", 0.0)),
                metadata=item.get("metadata", {}),
            )
            for item in raw_results
        ]

        return SearchResponse(
            results=results,
            total=len(results),
            query=query,
            filters=filters,
        )

    def search_creators(
        self, query: str, filters: Optional[SearchFilters] = None
    ) -> SearchResponse:
        """Search for creators by name, bio, or skills.

        Args:
            query: The search query string.
            filters: Optional search filters.

        Returns:
            SearchResponse with matching creators.

        Raises:
            ValueError: If query is empty or invalid.
            SearchBackendError: If the search backend fails.
        """
        if not query or not query.strip():
            raise ValueError("query must be a non-empty string")

        filters = filters or SearchFilters()
        logger.info("Searching creators: query=%r filters=%s", query, filters)

        try:
            raw_results = self._execute_creator_search(query.strip(), filters)
        except SearchBackendError:
            raise
        except Exception as exc:
            logger.exception("Creator search failed for query=%r", query)
            raise SearchBackendError(f"Creator search failed: {exc}") from exc

        results = [
            SearchResult(
                id=item["id"],
                title=item["name"],
                type="creator",
                score=float(item.get("score", 0.0)),
                metadata=item.get("metadata", {}),
            )
            for item in raw_results
        ]

        return SearchResponse(
            results=results,
            total=len(results),
            query=query,
            filters=filters,
        )

    def get_search_suggestions(self, query: str) -> List[Suggestion]:
        """Get autocomplete suggestions for a partial query.

        Args:
            query: The partial query string.

        Returns:
            List of Suggestion objects.

        Raises:
            ValueError: If query is empty.
            SearchBackendError: If the suggestion backend fails.
        """
        if not query or not query.strip():
            raise ValueError("query must be a non-empty string")

        logger.debug("Fetching suggestions for query=%r", query)

        try:
            raw_suggestions = self._execute_suggestions(query.strip())
        except SearchBackendError:
            raise
        except Exception as exc:
            logger.exception("Suggestion fetch failed for query=%r", query)
            raise SearchBackendError(f"Suggestion fetch failed: {exc}") from exc

        return [
            Suggestion(
                text=s["text"],
                type=s.get("type", "content"),
                highlight=s.get("highlight"),
            )
            for s in raw_suggestions
        ]

    # ------------------------------------------------------------------
    # Backend interaction (override or inject a real backend)
    # ------------------------------------------------------------------

    def _execute_content_search(
        self, query: str, filters: SearchFilters
    ) -> List[Dict[str, Any]]:
        """Execute content search against the backend."""
        if self._backend is None:
            return []
        return self._backend.search_content(query, filters.__dict__)

    def _execute_creator_search(
        self, query: str, filters: SearchFilters
    ) -> List[Dict[str, Any]]:
        """Execute creator search against the backend."""
        if self._backend is None:
            return []
        return self._backend.search_creators(query, filters.__dict__)

    def _execute_suggestions(self, query: str) -> List[Dict[str, Any]]:
        """Execute suggestion fetch against the backend."""
        if self._backend is None:
            return []
        return self._backend.suggestions(query)


# Module-level convenience functions using a default service instance
_default_service = SearchService()


def search_content(
    query: str, filters: Optional[SearchFilters] = None
) -> SearchResponse:
    """Perform full-text search over marketplace content.

    Args:
        query: The search query string.
        filters: Optional search filters.

    Returns:
        SearchResponse with matching content items.

    Raises:
        ValueError: If query is empty or invalid.
        SearchBackendError: If the search backend fails.
    """
    return _default_service.search_content(query, filters)


def search_creators(
    query: str, filters: Optional[SearchFilters] = None
) -> SearchResponse:
    """Search for creators by name, bio, or skills.

    Args:
        query: The search query string.
        filters: Optional search filters.

    Returns:
        SearchResponse with matching creators.

    Raises:
        ValueError: If query is empty or invalid.
        SearchBackendError: If the search backend fails.
    """
    return _default_service.search_creators(query, filters)


def get_search_suggestions(query: str) -> List[Suggestion]:
    """Get autocomplete suggestions for a partial query.

    Args:
        query: The partial query string.

    Returns:
        List of Suggestion objects.

    Raises:
        ValueError: If query is empty.
        SearchBackendError: If the suggestion backend fails.
    """
    return _default_service.get_search_suggestions(query)
