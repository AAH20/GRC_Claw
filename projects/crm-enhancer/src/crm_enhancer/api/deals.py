"""Deal API endpoints."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from crm_enhancer.agents.deal_scoring import DealData, DealScoringAgent

logger = structlog.get_logger(__name__)

router = APIRouter()


class ScoreDealRequest(BaseModel):
    """Request model for deal scoring."""

    deal_id: str
    title: str
    value: float
    stage: str
    contact_email: str
    company: str | None = None
    days_in_stage: int = 0
    activities_count: int = 0
    last_activity_days: int | None = None
    source: str | None = None


class ScoreDealResponse(BaseModel):
    """Response model for deal scoring."""

    deal_id: str
    total_score: float
    factors: list[dict[str, Any]]
    priority: str
    win_probability: float
    recommendation: str


class DealResponse(BaseModel):
    """Response model for deal."""

    deal_id: str
    title: str
    value: float
    stage: str
    contact_email: str
    company: str | None = None
    score: float | None = None
    priority: str | None = None


_agent: DealScoringAgent | None = None


def _get_agent() -> DealScoringAgent:
    """Get or create the deal scoring agent."""
    global _agent
    if _agent is None:
        _agent = DealScoringAgent()
    return _agent


@router.post("/score", response_model=ScoreDealResponse)
async def score_deal(request: ScoreDealRequest) -> ScoreDealResponse:
    """Score a deal using the deal scoring agent."""
    agent = _get_agent()
    deal = DealData(
        deal_id=request.deal_id,
        title=request.title,
        value=request.value,
        stage=request.stage,
        contact_email=request.contact_email,
        company=request.company,
        days_in_stage=request.days_in_stage,
        activities_count=request.activities_count,
        last_activity_days=request.last_activity_days,
        source=request.source,
    )
    try:
        result = await agent.score_deal(deal)
        return ScoreDealResponse(
            deal_id=result.deal_id,
            total_score=result.total_score,
            factors=[f.model_dump() for f in result.factors],
            priority=result.priority,
            win_probability=result.win_probability,
            recommendation=result.recommendation,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Deal scoring failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Scoring failed",
        ) from exc


@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(deal_id: str) -> DealResponse:
    """Get a deal by ID."""
    # In production, this would query the database
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Deal retrieval not yet implemented",
    )


@router.get("/", response_model=list[DealResponse])
async def list_deals(
    stage: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[DealResponse]:
    """List deals with optional filtering."""
    # In production, this would query the database
    return []
