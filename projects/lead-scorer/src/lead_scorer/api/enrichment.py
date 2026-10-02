"""API routes for lead enrichment endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from lead_scorer.agents.evidence import EvidenceAgent, EvidenceResult
from lead_scorer.agents.research import ResearchAgent, ResearchResult

router = APIRouter(prefix="/api/v1", tags=["enrichment"])


class EnrichmentRequest(BaseModel):
    """Request model for lead enrichment."""

    lead_id: str = Field(..., min_length=1, description="Unique lead identifier")
    domain: str = Field(..., min_length=1, description="Company domain")
    company_name: str = Field(default="", description="Company name")


class EnrichmentResponse(BaseModel):
    """Response model for enrichment result."""

    success: bool
    lead_id: str
    research: ResearchResult | None = None
    evidence: EvidenceResult | None = None


def get_research_agent() -> ResearchAgent:
    """Dependency to get research agent instance."""
    return ResearchAgent()


def get_evidence_agent() -> EvidenceAgent:
    """Dependency to get evidence agent instance."""
    return EvidenceAgent()


@router.post("/leads/{lead_id}/enrich", response_model=EnrichmentResponse)
async def enrich_lead(
    lead_id: str,
    request: EnrichmentRequest,
    research_agent: Annotated[ResearchAgent, Depends(get_research_agent)],
    evidence_agent: Annotated[EvidenceAgent, Depends(get_evidence_agent)],
) -> EnrichmentResponse:
    """Enrich a lead with research and evidence data.

    Args:
        lead_id: Unique lead identifier.
        request: Enrichment request with domain and company info.
        research_agent: Research agent instance.
        evidence_agent: Evidence agent instance.

    Returns:
        EnrichmentResponse with research and evidence data.

    Raises:
        HTTPException: If enrichment fails.
    """
    try:
        research = await research_agent.research(request.domain, request.company_name)
        evidence = await evidence_agent.collect(lead_id)

        return EnrichmentResponse(
            success=True,
            lead_id=lead_id,
            research=research,
            evidence=evidence,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enrichment failed: {str(exc)}",
        ) from exc
