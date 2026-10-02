"""API routes for prospect management."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from sales_automator.agents.prospecting import Prospect, ProspectingAgent

logger = structlog.get_logger(__name__)
router = APIRouter()

# In-memory store for demo purposes — replace with database in production
_prospects: dict[str, Prospect] = {}
_agent = ProspectingAgent()


class CreateProspectRequest(BaseModel):
    """Request model for creating a prospect."""

    name: str = Field(..., min_length=1, description="Prospect full name")
    company: str = Field(..., min_length=1, description="Company name")
    title: str | None = Field(None, description="Job title")
    email: str | None = Field(None, description="Email address")
    linkedin_url: str | None = Field(None, description="LinkedIn profile URL")
    company_size: int | None = Field(None, description="Number of employees")
    industry: str | None = Field(None, description="Industry sector")
    source: str = Field("api", description="Discovery source")
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProspectResponse(BaseModel):
    """Response model for a prospect."""

    id: str
    name: str
    company: str
    title: str | None = None
    email: str | None = None
    linkedin_url: str | None = None
    company_size: int | None = None
    industry: str | None = None
    source: str = "unknown"
    score: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


@router.post("/prospects", response_model=ProspectResponse, status_code=status.HTTP_201_CREATED)
async def create_prospect(request: CreateProspectRequest) -> ProspectResponse:
    """Create a new prospect.

    Args:
        request: Prospect creation data.

    Returns:
        The created prospect.
    """
    import uuid

    prospect_id = str(uuid.uuid4())
    prospect = Prospect(
        id=prospect_id,
        name=request.name,
        company=request.company,
        title=request.title,
        email=request.email,
        linkedin_url=request.linkedin_url,
        company_size=request.company_size,
        industry=request.industry,
        source=request.source,
        metadata=request.metadata,
    )
    _prospects[prospect_id] = prospect
    logger.info("Created prospect", prospect_id=prospect_id, company=request.company)
    return ProspectResponse(**prospect.model_dump())


@router.get("/prospects", response_model=list[ProspectResponse])
async def list_prospects(
    skip: int = 0,
    limit: int = 100,
) -> list[ProspectResponse]:
    """List all prospects.

    Args:
        skip: Number of prospects to skip.
        limit: Maximum number to return.

    Returns:
        List of prospects.
    """
    prospects = list(_prospects.values())[skip : skip + limit]
    return [ProspectResponse(**p.model_dump()) for p in prospects]


@router.get("/prospects/{prospect_id}", response_model=ProspectResponse)
async def get_prospect(prospect_id: str) -> ProspectResponse:
    """Get a prospect by ID.

    Args:
        prospect_id: The prospect ID.

    Returns:
        The prospect.

    Raises:
        HTTPException: If prospect not found.
    """
    prospect = _prospects.get(prospect_id)
    if not prospect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prospect {prospect_id} not found",
        )
    return ProspectResponse(**prospect.model_dump())


@router.post("/prospects/{prospect_id}/score", response_model=dict[str, Any])
async def score_prospect(prospect_id: str) -> dict[str, Any]:
    """Score a prospect.

    Args:
        prospect_id: The prospect ID.

    Returns:
        Prospect score breakdown.

    Raises:
        HTTPException: If prospect not found.
    """
    prospect = _prospects.get(prospect_id)
    if not prospect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prospect {prospect_id} not found",
        )
    score = await _agent.score(prospect)
    return score.model_dump()
