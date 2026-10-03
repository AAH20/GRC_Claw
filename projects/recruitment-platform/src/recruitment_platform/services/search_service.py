"""Search service for recruitment platform.

Provides full-text search for candidates and jobs, plus autocomplete suggestions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SearchFilters:
    """Common filters applicable to search queries."""

    location: Optional[str] = None
    skills: List[str] = field(default_factory=list)
    experience_min: Optional[int] = None
    experience_max: Optional[int] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    status: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    limit: int = 20
    offset: int = 0

    def __post_init__(self) -> None:
        if self.limit < 1 or self.limit > 100:
            raise ValueError("limit must be between 1 and 100")
        if self.offset < 0:
            raise ValueError("offset must be non-negative")


@dataclass
class SearchResult:
    """Generic search result container."""

    items: List[Dict[str, Any]]
    total: int
    query: str
    filters: SearchFilters


class SearchServiceError(Exception):
    """Raised when a search operation fails."""


class SearchService:
    """Service for searching candidates and jobs."""

    def __init__(self, db_session: Any = None) -> None:
        self._db = db_session

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search_candidates(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
    ) -> SearchResult:
        """Full-text search for candidates.

        Args:
            query: Free-text search string.
            filters: Optional search filters.

        Returns:
            SearchResult with matching candidates.

        Raises:
            SearchServiceError: If the search backend fails.
            ValueError: If query is empty or filters are invalid.
        """
        if not query or not query.strip():
            raise ValueError("query must be a non-empty string")

        filters = filters or SearchFilters()

        try:
            items, total = self._execute_candidate_search(query, filters)
        except Exception as exc:
            logger.error("Candidate search failed: %s", exc)
            raise SearchServiceError(f"Candidate search failed: {exc}") from exc

        return SearchResult(items=items, total=total, query=query, filters=filters)

    def search_jobs(
        self,
        query: str,
        filters: Optional[SearchFilters] = None,
    ) -> SearchResult:
        """Full-text search for jobs.

        Args:
            query: Free-text search string.
            filters: Optional search filters.

        Returns:
            SearchResult with matching jobs.

        Raises:
            SearchServiceError: If the search backend fails.
            ValueError: If query is empty or filters are invalid.
        """
        if not query or not query.strip():
            raise ValueError("query must be a non-empty string")

        filters = filters or SearchFilters()

        try:
            items, total = self._execute_job_search(query, filters)
        except Exception as exc:
            logger.error("Job search failed: %s", exc)
            raise SearchServiceError(f"Job search failed: {exc}") from exc

        return SearchResult(items=items, total=total, query=query, filters=filters)

    def get_search_suggestions(self, query: str) -> List[str]:
        """Return autocomplete suggestions for a partial query.

        Args:
            query: Partial search string.

        Returns:
            List of suggestion strings (max 10).

        Raises:
            SearchServiceError: If the suggestion backend fails.
        """
        if not query or not query.strip():
            return []

        try:
            suggestions = self._fetch_suggestions(query.strip())
        except Exception as exc:
            logger.error("Suggestion fetch failed: %s", exc)
            raise SearchServiceError(f"Suggestion fetch failed: {exc}") from exc

        return suggestions[:10]

    # ------------------------------------------------------------------
    # Internal helpers (override or wire to real backend)
    # ------------------------------------------------------------------

    def _execute_candidate_search(
        self, query: str, filters: SearchFilters
    ) -> tuple[List[Dict[str, Any]], int]:
        """Execute candidate search against the backend.

        Replace with actual DB / search-engine call.
        """
        # Placeholder: integrate with ORM or search engine here
        return [], 0

    def _execute_job_search(
        self, query: str, filters: SearchFilters
    ) -> tuple[List[Dict[str, Any]], int]:
        """Execute job search against the backend.

        Replace with actual DB / search-engine call.
        """
        # Placeholder: integrate with ORM or search engine here
        return [], 0

    def _fetch_suggestions(self, query: str) -> List[str]:
        """Fetch autocomplete suggestions from the backend.

        Replace with actual DB / search-engine call.
        """
        # Placeholder: integrate with ORM or search engine here
        return []


# Module-level convenience functions ------------------------------------------------

_default_service = SearchService()


def search_candidates(
    query: str, filters: Optional[SearchFilters] = None
) -> SearchResult:
    """Convenience wrapper around SearchService.search_candidates."""
    return _default_service.search_candidates(query, filters)


def search_jobs(
    query: str, filters: Optional[SearchFilters] = None
) -> SearchResult:
    """Convenience wrapper around SearchService.search_jobs."""
    return _default_service.search_jobs(query, filters)


def get_search_suggestions(query: str) -> List[str]:
    """Convenience wrapper around SearchService.get_search_suggestions."""
    return _default_service.get_search_suggestions(query)
