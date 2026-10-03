"""Search API endpoints."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Query

from recruitment_platform.search.search_service import search_service

router = APIRouter()


@router.get("/search/jobs")
async def search_jobs(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """Search jobs."""
    return await search_service.search_jobs(q, limit=limit, offset=offset)


@router.get("/search/candidates")
async def search_candidates(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """Search candidates."""
    return await search_service.search_candidates(q, limit=limit, offset=offset)


@router.get("/search/skills")
async def search_skills(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, ge=1, le=100),
) -> list[dict[str, Any]]:
    """Search skills with autocomplete."""
    return await search_service.search_skills(q, limit=limit)


@router.get("/search/autocomplete")
async def autocomplete(
    q: str = Query(..., description="Search query"),
    entity_type: str = Query("job", description="Entity type"),
    limit: int = Query(10, ge=1, le=50),
) -> list[dict[str, Any]]:
    """Autocomplete suggestions."""
    return await search_service.autocomplete(q, entity_type, limit=limit)
