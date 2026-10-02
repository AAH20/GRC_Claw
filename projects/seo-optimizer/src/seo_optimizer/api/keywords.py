"""API routes for keyword research endpoints."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from seo_optimizer.agents.keyword_research import KeywordResearchAgent
from seo_optimizer.config import get_settings

router = APIRouter()


class KeywordResearchRequest(BaseModel):
    """Request model for keyword research.

    Attributes:
        domain: Target domain to research keywords for.
        seed_keywords: Optional list of seed keywords to expand from.
        country: Country code for localized results.
        max_results: Maximum number of keywords to return.
        min_search_volume: Minimum search volume threshold.
        max_difficulty: Maximum keyword difficulty threshold.
    """

    domain: str = Field(..., description="Target domain", min_length=1)
    seed_keywords: list[str] = Field(default_factory=list, description="Seed keywords")
    country: str = Field(default="us", description="Country code")
    max_results: int = Field(default=50, ge=1, le=200)
    min_search_volume: int = Field(default=100, ge=0)
    max_difficulty: int = Field(default=70, ge=0, le=100)


class KeywordResearchResponse(BaseModel):
    """Response model for keyword research.

    Attributes:
        task_id: Unique task identifier.
        status: Current status of the research.
        result: Research results if completed.
    """

    task_id: str
    status: str
    result: dict[str, Any] | None = None


# In-memory task store (replace with Redis/DB in production)
_tasks: dict[str, dict[str, Any]] = {}


@router.post(
    "/research",
    response_model=KeywordResearchResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def research_keywords(
    request: KeywordResearchRequest,
) -> KeywordResearchResponse:
    """Start a keyword research task.

    Args:
        request: Keyword research parameters.

    Returns:
        Task acceptance response with task ID.
    """
    import uuid

    settings = get_settings()
    task_id = str(uuid.uuid4())
    agent = KeywordResearchAgent(config=settings.model_dump())

    _tasks[task_id] = {
        "status": "pending",
        "agent": agent,
        "request": request,
        "result": None,
    }

    return KeywordResearchResponse(
        task_id=task_id,
        status="pending",
    )


@router.get("/{task_id}", response_model=KeywordResearchResponse)
async def get_research_results(task_id: str) -> KeywordResearchResponse:
    """Get keyword research results by task ID.

    Args:
        task_id: The task identifier.

    Returns:
        Research results if available.

    Raises:
        HTTPException: If task ID is not found.
    """
    if task_id not in _tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    task = _tasks[task_id]
    return KeywordResearchResponse(
        task_id=task_id,
        status=task["status"],
        result=task.get("result"),
    )
