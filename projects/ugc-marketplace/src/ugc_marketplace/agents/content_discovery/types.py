"""Type definitions for content discovery agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SearchRequest:
    """Represents a search request."""

    query: str
    user_id: str | None = None
    filters: dict[str, Any] = field(default_factory=dict)
    limit: int = 20
    offset: int = 0


@dataclass
class SearchResponse:
    """Represents a search response."""

    results: list[dict[str, Any]] = field(default_factory=list)
    total_count: int = 0
    query_time_ms: float = 0.0
    facets: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchExplanation:
    """Represents an explanation of search results."""

    query: str
    explanation: str
    suggested_queries: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
