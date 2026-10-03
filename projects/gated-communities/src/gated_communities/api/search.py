"""Full-text search API."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class SearchResult(BaseModel):
    """Schema for search results."""

    id: str
    type: str
    title: str
    description: str
    score: float


class SearchResponse(BaseModel):
    """Schema for search response."""

    results: list[SearchResult]
    total: int
    query: str


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    type: str | None = Query(None, description="Filter by type"),  # noqa: A002
    limit: int = Query(20, ge=1, le=100),
) -> SearchResponse:
    """Full-text search across communities, members, and content."""
    # Sample results - replace with actual database search
    results = [
        SearchResult(
            id="1",
            type="community",
            title="Python Developers",
            description="A community for Python developers",
            score=0.95,
        ),
        SearchResult(
            id="2",
            type="member",
            title="Alice Johnson",
            description="Python developer and contributor",
            score=0.85,
        ),
    ]
    return SearchResponse(results=results, total=len(results), query=q)
