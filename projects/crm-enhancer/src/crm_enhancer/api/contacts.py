"""Contact API endpoints."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from crm_enhancer.agents.contact_enrichment import ContactData, ContactEnrichmentAgent

logger = structlog.get_logger(__name__)

router = APIRouter()


class EnrichContactRequest(BaseModel):
    """Request model for contact enrichment."""

    email: str
    first_name: str | None = None
    last_name: str | None = None
    company: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None


class EnrichContactResponse(BaseModel):
    """Response model for contact enrichment."""

    contact: dict[str, Any]
    company_domain: str | None = None
    company_size: str | None = None
    industry: str | None = None
    revenue: str | None = None
    technologies: list[str] = Field(default_factory=list)
    social_profiles: dict[str, str] = Field(default_factory=dict)
    confidence_score: float = 0.0
    sources: list[str] = Field(default_factory=list)


_agent: ContactEnrichmentAgent | None = None


def _get_agent() -> ContactEnrichmentAgent:
    """Get or create the contact enrichment agent."""
    global _agent
    if _agent is None:
        _agent = ContactEnrichmentAgent()
    return _agent


@router.post("/enrich", response_model=EnrichContactResponse)
async def enrich_contact(request: EnrichContactRequest) -> EnrichContactResponse:
    """Enrich a contact record with additional data."""
    agent = _get_agent()
    contact = ContactData(
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
        company=request.company,
        phone=request.phone,
        linkedin_url=request.linkedin_url,
    )
    try:
        result = await agent.enrich(contact)
        return EnrichContactResponse(
            contact=result.contact.model_dump(),
            company_domain=result.company_domain,
            company_size=result.company_size,
            industry=result.industry,
            revenue=result.revenue,
            technologies=result.technologies,
            social_profiles=result.social_profiles,
            confidence_score=result.confidence_score,
            sources=result.sources,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Contact enrichment failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Enrichment failed",
        ) from exc
