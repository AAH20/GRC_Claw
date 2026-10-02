"""Compliance score API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from compliance_monitor.api.dependencies import get_compliance_scorer
from compliance_monitor.api.store import store
from compliance_monitor.agents import ComplianceScorerAgent
from compliance_monitor.models.schemas import ComplianceScore, ScoreRequest

router = APIRouter()


@router.get("", response_model=list[ComplianceScore])
async def list_scores() -> list[ComplianceScore]:
    """List all compliance scores.

    Returns:
        List of all compliance scores.
    """
    return store.list_scores()


@router.post("", response_model=ComplianceScore, status_code=status.HTTP_201_CREATED)
async def compute_score(
    data: ScoreRequest,
    agent: ComplianceScorerAgent = Depends(get_compliance_scorer),
) -> ComplianceScore:
    """Compute a compliance score.

    Args:
        data: Score request data.
        agent: Compliance scorer agent.

    Returns:
        Computed compliance score.
    """
    score = await agent.run(data)
    return store.create_score(score)


@router.get("/{score_id}", response_model=ComplianceScore)
async def get_score(score_id: UUID) -> ComplianceScore:
    """Get a compliance score by ID.

    Args:
        score_id: Compliance score identifier.

    Returns:
        Compliance score details.

    Raises:
        HTTPException: If score not found.
    """
    score = store.get_score(score_id)
    if not score:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compliance score not found")
    return score
