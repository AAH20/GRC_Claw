"""Keyword API routes for PPC Manager."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ppc_manager.agents.keyword_research import KeywordResearchAgent

logger = structlog.get_logger(__name__)

router = APIRouter()


class KeywordResearchRequest(BaseModel):
    """Request model for keyword research.

    Attributes:
        seed_keyword: The seed keyword to research.
        language: Target language.
        location: Target location.
    """

    seed_keyword: str = Field(..., min_length=1, max_length=255)
    language: str = Field(default="en", min_length=2, max_length=10)
    location: str = Field(default="US", min_length=2, max_length=10)


class KeywordResponse(BaseModel):
    """Response model for a keyword.

    Attributes:
        keyword: The keyword phrase.
        search_volume: Estimated monthly search volume.
        competition: Competition level.
        cpc_estimate: Estimated CPC in USD.
        relevance_score: Relevance score (0.0–1.0).
        intent: Search intent category.
    """

    keyword: str
    search_volume: int = 0
    competition: str = "medium"
    cpc_estimate: float = 0.0
    relevance_score: float = 0.0
    intent: str = "informational"


# In-memory store for demo purposes
_keywords: dict[str, list[dict]] = {}


@router.get("")
async def list_keywords(campaign_id: str | None = None) -> list[dict]:
    """List keywords, optionally filtered by campaign.

    Args:
        campaign_id: Optional campaign ID to filter by.

    Returns:
        A list of keywords.
    """
    if campaign_id:
        return _keywords.get(campaign_id, [])
    all_keywords: list[dict] = []
    for kw_list in _keywords.values():
        all_keywords.extend(kw_list)
    return all_keywords


@router.post("/research", response_model=list[KeywordResponse])
async def research_keywords(request: KeywordResearchRequest) -> list[dict]:
    """Run keyword research from a seed keyword.

    Args:
        request: The keyword research request.

    Returns:
        A list of keyword suggestions.

    Raises:
        HTTPException: If the research fails.
    """
    agent = KeywordResearchAgent()
    try:
        result = await agent.research(
            seed_keyword=request.seed_keyword,
            language=request.language,
            location=request.location,
        )
        return [s.model_dump() for s in result.suggestions]
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Keyword research failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Keyword research failed",
        ) from exc
