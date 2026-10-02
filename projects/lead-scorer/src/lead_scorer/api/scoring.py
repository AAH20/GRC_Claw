"""API routes for scoring endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from lead_scorer.agents.evidence import EvidenceAgent, EvidenceResult
from lead_scorer.agents.research import ResearchAgent, ResearchResult
from lead_scorer.agents.scoring import ScoringAgent, ScoringResult

router = APIRouter(prefix="/api/v1/scoring", tags=["scoring"])


class ScoreRequest(BaseModel):
    """Request model for scoring a lead."""

    lead_id: str = Field(..., min_length=1, description="Unique lead identifier")
    domain: str = Field(default="", description="Company domain for research")
    company_name: str = Field(default="", description="Company name")
    budget: float | None = Field(default=None, ge=0, description="Available budget")
    authority: bool | None = Field(default=None, description="Has decision authority")
    need: bool | None = Field(default=None, description="Clear need identified")
    timeline_days: int | None = Field(default=None, ge=0, description="Timeline in days")


class BatchScoreRequest(BaseModel):
    """Request model for batch scoring."""

    leads: list[ScoreRequest] = Field(..., min_length=1, max_length=100)


class ScoreResponse(BaseModel):
    """Response model for scoring result."""

    success: bool
    data: ScoringResult


class BatchScoreResponse(BaseModel):
    """Response model for batch scoring results."""

    success: bool
    results: list[ScoringResult]
    total: int


def get_scoring_agent() -> ScoringAgent:
    """Dependency to get scoring agent instance."""
    return ScoringAgent()


def get_research_agent() -> ResearchAgent:
    """Dependency to get research agent instance."""
    return ResearchAgent()


def get_evidence_agent() -> EvidenceAgent:
    """Dependency to get evidence agent instance."""
    return EvidenceAgent()


@router.post("/batch", response_model=BatchScoreResponse)
async def batch_score(
    request: BatchScoreRequest,
    scoring_agent: Annotated[ScoringAgent, Depends(get_scoring_agent)],
    research_agent: Annotated[ResearchAgent, Depends(get_research_agent)],
    evidence_agent: Annotated[EvidenceAgent, Depends(get_evidence_agent)],
) -> BatchScoreResponse:
    """Score multiple leads in batch.

    Args:
        request: Batch scoring request with list of leads.
        scoring_agent: Scoring agent instance.
        research_agent: Research agent instance.
        evidence_agent: Evidence agent instance.

    Returns:
        BatchScoreResponse with results for all leads.

    Raises:
        HTTPException: If batch size exceeds limit or scoring fails.
    """
    results: list[ScoringResult] = []

    for lead in request.leads:
        try:
            research: ResearchResult | None = None
            evidence: EvidenceResult | None = None

            if lead.domain:
                research = await research_agent.research(lead.domain, lead.company_name)

            evidence = await evidence_agent.collect(lead.lead_id)

            scoring_result = await scoring_agent.score(
                lead_id=lead.lead_id,
                research=research,
                evidence=evidence,
            )
            results.append(scoring_result)

        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to score lead {lead.lead_id}: {str(exc)}",
            ) from exc

    return BatchScoreResponse(success=True, results=results, total=len(results))
