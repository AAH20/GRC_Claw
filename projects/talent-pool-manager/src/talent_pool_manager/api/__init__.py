"""API routes for talent pool management."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from talent_pool_manager.agents import AgentRegistry
from talent_pool_manager.config import get_settings
from talent_pool_manager.config.logging_config import get_logger
from talent_pool_manager.models import (
    CandidateCreate,
    CandidateListResponse,
    CandidateResponse,
    CandidateUpdate,
    DiscoveryRequest,
    DiscoveryResult,
    EngagementCreate,
    EngagementListResponse,
    EngagementResponse,
    EngagementUpdate,
    OutreachCampaignCreate,
    OutreachCampaignListResponse,
    OutreachCampaignResponse,
    OutreachCampaignUpdate,
    OutreachRequest,
    OutreachResult,
    OutreachTemplateCreate,
    OutreachTemplateResponse,
    OutreachTemplateUpdate,
    ScoringRequest,
    ScoringResult,
    SegmentCreate,
    SegmentListResponse,
    SegmentResponse,
    SegmentUpdate,
    SegmentationRequest,
    SegmentationResult,
    TalentPoolCreate,
    TalentPoolListResponse,
    TalentPoolResponse,
    TalentPoolStats,
    TalentPoolUpdate,
)

logger = get_logger(__name__)

# In-memory stores for demo purposes
# In production, these would be database repositories
_pools: dict[UUID, TalentPoolResponse] = {}
_candidates: dict[UUID, CandidateResponse] = {}
_segments: dict[UUID, SegmentResponse] = {}
_engagements: dict[UUID, EngagementResponse] = {}
_outreach_campaigns: dict[UUID, OutreachCampaignResponse] = {}
_outreach_templates: dict[UUID, OutreachTemplateResponse] = {}

# Agent registry
_agent_registry = AgentRegistry()


def get_agent_registry() -> AgentRegistry:
    """Dependency to get the agent registry."""
    return _agent_registry


router = APIRouter()


# ---------------------------------------------------------------------------
# Health & Info
# ---------------------------------------------------------------------------


@router.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@router.get("/info", tags=["system"])
async def api_info() -> dict[str, str]:
    """API information endpoint."""
    settings = get_settings()
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "Agentic AI talent pool management system",
    }


# ---------------------------------------------------------------------------
# Talent Pools
# ---------------------------------------------------------------------------


@router.post("/pools", response_model=TalentPoolResponse, status_code=status.HTTP_201_CREATED, tags=["pools"])
async def create_pool(pool: TalentPoolCreate) -> TalentPoolResponse:
    """Create a new talent pool."""
    from datetime import datetime
    from uuid import uuid4

    pool_id = uuid4()
    new_pool = TalentPoolResponse(
        id=pool_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        name=pool.name,
        description=pool.description,
        visibility=pool.visibility,
        tags=pool.tags,
        criteria=pool.criteria,
        auto_refresh=pool.auto_refresh,
        refresh_interval_hours=pool.refresh_interval_hours,
        organization_id=pool.organization_id,
    )
    _pools[pool_id] = new_pool
    logger.info("Created talent pool", pool_id=str(pool_id))
    return new_pool


@router.get("/pools", response_model=TalentPoolListResponse, tags=["pools"])
async def list_pools(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    organization_id: UUID | None = None,
) -> TalentPoolListResponse:
    """List all talent pools with pagination."""
    pools = list(_pools.values())
    if organization_id:
        pools = [p for p in pools if p.organization_id == organization_id]

    total = len(pools)
    start = (page - 1) * page_size
    end = start + page_size
    items = pools[start:end]
    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return TalentPoolListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/pools/{pool_id}", response_model=TalentPoolResponse, tags=["pools"])
async def get_pool(pool_id: UUID) -> TalentPoolResponse:
    """Get a specific talent pool by ID."""
    if pool_id not in _pools:
        raise HTTPException(status_code=404, detail="Talent pool not found")
    return _pools[pool_id]


@router.put("/pools/{pool_id}", response_model=TalentPoolResponse, tags=["pools"])
async def update_pool(pool_id: UUID, pool_update: TalentPoolUpdate) -> TalentPoolResponse:
    """Update a talent pool."""
    if pool_id not in _pools:
        raise HTTPException(status_code=404, detail="Talent pool not found")

    existing = _pools[pool_id]
    update_data = pool_update.model_dump(exclude_unset=True)
    updated = existing.model_copy(update=update_data)
    _pools[pool_id] = updated
    logger.info("Updated talent pool", pool_id=str(pool_id))
    return updated


@router.delete("/pools/{pool_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["pools"])
async def delete_pool(pool_id: UUID) -> None:
    """Delete a talent pool."""
    if pool_id not in _pools:
        raise HTTPException(status_code=404, detail="Talent pool not found")
    del _pools[pool_id]
    logger.info("Deleted talent pool", pool_id=str(pool_id))


@router.get("/pools/{pool_id}/stats", response_model=TalentPoolStats, tags=["pools"])
async def get_pool_stats(pool_id: UUID) -> TalentPoolStats:
    """Get statistics for a talent pool."""
    if pool_id not in _pools:
        raise HTTPException(status_code=404, detail="Talent pool not found")

    pool_candidates = [c for c in _candidates.values() if c.pool_id == pool_id]
    active = [c for c in pool_candidates if c.status.value not in ("rejected", "archived")]
    avg_score = sum(c.score for c in pool_candidates) / len(pool_candidates) if pool_candidates else 0.0

    status_breakdown: dict[str, int] = {}
    for c in pool_candidates:
        status_breakdown[c.status.value] = status_breakdown.get(c.status.value, 0) + 1

    return TalentPoolStats(
        pool_id=pool_id,
        total_candidates=len(pool_candidates),
        active_candidates=len(active),
        average_score=avg_score,
        top_skills=[],
        status_breakdown=status_breakdown,
        segment_distribution={},
    )


# ---------------------------------------------------------------------------
# Candidates
# ---------------------------------------------------------------------------


@router.post("/candidates", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED, tags=["candidates"])
async def create_candidate(candidate: CandidateCreate) -> CandidateResponse:
    """Add a candidate to a talent pool."""
    if candidate.pool_id not in _pools:
        raise HTTPException(status_code=404, detail="Talent pool not found")

    from datetime import datetime
    from uuid import uuid4

    candidate_id = uuid4()
    new_candidate = CandidateResponse(
        id=candidate_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        first_name=candidate.first_name,
        last_name=candidate.last_name,
        email=candidate.email,
        phone=candidate.phone,
        location=candidate.location,
        headline=candidate.headline,
        summary=candidate.summary,
        skills=candidate.skills,
        experience=candidate.experience,
        education=candidate.education,
        linkedin_url=candidate.linkedin_url,
        github_url=candidate.github_url,
        portfolio_url=candidate.portfolio_url,
        resume_url=candidate.resume_url,
        source=candidate.source,
        tags=candidate.tags,
        metadata=candidate.metadata,
        pool_id=candidate.pool_id,
    )
    _candidates[candidate_id] = new_candidate
    logger.info("Created candidate", candidate_id=str(candidate_id))
    return new_candidate


@router.get("/candidates", response_model=CandidateListResponse, tags=["candidates"])
async def list_candidates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    pool_id: UUID | None = None,
    status: str | None = None,
) -> CandidateListResponse:
    """List candidates with pagination and filtering."""
    candidates = list(_candidates.values())
    if pool_id:
        candidates = [c for c in candidates if c.pool_id == pool_id]
    if status:
        candidates = [c for c in candidates if c.status.value == status]

    total = len(candidates)
    start = (page - 1) * page_size
    end = start + page_size
    items = candidates[start:end]
    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return CandidateListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/candidates/{candidate_id}", response_model=CandidateResponse, tags=["candidates"])
async def get_candidate(candidate_id: UUID) -> CandidateResponse:
    """Get a specific candidate by ID."""
    if candidate_id not in _candidates:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return _candidates[candidate_id]


@router.put("/candidates/{candidate_id}", response_model=CandidateResponse, tags=["candidates"])
async def update_candidate(candidate_id: UUID, candidate_update: CandidateUpdate) -> CandidateResponse:
    """Update a candidate."""
    if candidate_id not in _candidates:
        raise HTTPException(status_code=404, detail="Candidate not found")

    existing = _candidates[candidate_id]
    update_data = candidate_update.model_dump(exclude_unset=True)
    updated = existing.model_copy(update=update_data)
    _candidates[candidate_id] = updated
    logger.info("Updated candidate", candidate_id=str(candidate_id))
    return updated


@router.delete("/candidates/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["candidates"])
async def delete_candidate(candidate_id: UUID) -> None:
    """Delete a candidate."""
    if candidate_id not in _candidates:
        raise HTTPException(status_code=404, detail="Candidate not found")
    del _candidates[candidate_id]
    logger.info("Deleted candidate", candidate_id=str(candidate_id))


# ---------------------------------------------------------------------------
# Segments
# ---------------------------------------------------------------------------


@router.post("/segments", response_model=SegmentResponse, status_code=status.HTTP_201_CREATED, tags=["segments"])
async def create_segment(segment: SegmentCreate) -> SegmentResponse:
    """Create a new segment within a talent pool."""
    if segment.pool_id not in _pools:
        raise HTTPException(status_code=404, detail="Talent pool not found")

    from datetime import datetime
    from uuid import uuid4

    segment_id = uuid4()
    new_segment = SegmentResponse(
        id=segment_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        name=segment.name,
        description=segment.description,
        segment_type=segment.segment_type,
        criteria=segment.criteria,
        is_dynamic=segment.is_dynamic,
        pool_id=segment.pool_id,
    )
    _segments[segment_id] = new_segment
    logger.info("Created segment", segment_id=str(segment_id))
    return new_segment


@router.get("/segments", response_model=SegmentListResponse, tags=["segments"])
async def list_segments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    pool_id: UUID | None = None,
) -> SegmentListResponse:
    """List segments with pagination."""
    segments = list(_segments.values())
    if pool_id:
        segments = [s for s in segments if s.pool_id == pool_id]

    total = len(segments)
    start = (page - 1) * page_size
    end = start + page_size
    items = segments[start:end]
    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return SegmentListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/segments/{segment_id}", response_model=SegmentResponse, tags=["segments"])
async def get_segment(segment_id: UUID) -> SegmentResponse:
    """Get a specific segment by ID."""
    if segment_id not in _segments:
        raise HTTPException(status_code=404, detail="Segment not found")
    return _segments[segment_id]


@router.put("/segments/{segment_id}", response_model=SegmentResponse, tags=["segments"])
async def update_segment(segment_id: UUID, segment_update: SegmentUpdate) -> SegmentResponse:
    """Update a segment."""
    if segment_id not in _segments:
        raise HTTPException(status_code=404, detail="Segment not found")

    existing = _segments[segment_id]
    update_data = segment_update.model_dump(exclude_unset=True)
    updated = existing.model_copy(update=update_data)
    _segments[segment_id] = updated
    logger.info("Updated segment", segment_id=str(segment_id))
    return updated


@router.delete("/segments/{segment_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["segments"])
async def delete_segment(segment_id: UUID) -> None:
    """Delete a segment."""
    if segment_id not in _segments:
        raise HTTPException(status_code=404, detail="Segment not found")
    del _segments[segment_id]
    logger.info("Deleted segment", segment_id=str(segment_id))


# ---------------------------------------------------------------------------
# Engagements
# ---------------------------------------------------------------------------


@router.post("/engagements", response_model=EngagementResponse, status_code=status.HTTP_201_CREATED, tags=["engagements"])
async def create_engagement(engagement: EngagementCreate) -> EngagementResponse:
    """Create a new engagement with a candidate."""
    if engagement.candidate_id not in _candidates:
        raise HTTPException(status_code=404, detail="Candidate not found")

    from datetime import datetime
    from uuid import uuid4

    engagement_id = uuid4()
    new_engagement = EngagementResponse(
        id=engagement_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        engagement_type=engagement.engagement_type,
        subject=engagement.subject,
        content=engagement.content,
        channel=engagement.channel,
        scheduled_at=engagement.scheduled_at,
        metadata=engagement.metadata,
        candidate_id=engagement.candidate_id,
    )
    _engagements[engagement_id] = new_engagement
    logger.info("Created engagement", engagement_id=str(engagement_id))
    return new_engagement


@router.get("/engagements", response_model=EngagementListResponse, tags=["engagements"])
async def list_engagements(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    candidate_id: UUID | None = None,
    status: str | None = None,
) -> EngagementListResponse:
    """List engagements with pagination."""
    engagements = list(_engagements.values())
    if candidate_id:
        engagements = [e for e in engagements if e.candidate_id == candidate_id]
    if status:
        engagements = [e for e in engagements if e.status.value == status]

    total = len(engagements)
    start = (page - 1) * page_size
    end = start + page_size
    items = engagements[start:end]
    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return EngagementListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/engagements/{engagement_id}", response_model=EngagementResponse, tags=["engagements"])
async def get_engagement(engagement_id: UUID) -> EngagementResponse:
    """Get a specific engagement by ID."""
    if engagement_id not in _engagements:
        raise HTTPException(status_code=404, detail="Engagement not found")
    return _engagements[engagement_id]


@router.put("/engagements/{engagement_id}", response_model=EngagementResponse, tags=["engagements"])
async def update_engagement(engagement_id: UUID, engagement_update: EngagementUpdate) -> EngagementResponse:
    """Update an engagement."""
    if engagement_id not in _engagements:
        raise HTTPException(status_code=404, detail="Engagement not found")

    existing = _engagements[engagement_id]
    update_data = engagement_update.model_dump(exclude_unset=True)
    updated = existing.model_copy(update=update_data)
    _engagements[engagement_id] = updated
    logger.info("Updated engagement", engagement_id=str(engagement_id))
    return updated


@router.delete("/engagements/{engagement_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["engagements"])
async def delete_engagement(engagement_id: UUID) -> None:
    """Delete an engagement."""
    if engagement_id not in _engagements:
        raise HTTPException(status_code=404, detail="Engagement not found")
    del _engagements[engagement_id]
    logger.info("Deleted engagement", engagement_id=str(engagement_id))


# ---------------------------------------------------------------------------
# Outreach Campaigns
# ---------------------------------------------------------------------------


@router.post("/outreach/campaigns", response_model=OutreachCampaignResponse, status_code=status.HTTP_201_CREATED, tags=["outreach"])
async def create_outreach_campaign(campaign: OutreachCampaignCreate) -> OutreachCampaignResponse:
    """Create a new outreach campaign."""
    from datetime import datetime
    from uuid import uuid4

    campaign_id = uuid4()
    new_campaign = OutreachCampaignResponse(
        id=campaign_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        name=campaign.name,
        description=campaign.description,
        template_id=campaign.template_id,
        segment_id=campaign.segment_id,
        pool_id=campaign.pool_id,
        scheduled_at=campaign.scheduled_at,
        metadata=campaign.metadata,
    )
    _outreach_campaigns[campaign_id] = new_campaign
    logger.info("Created outreach campaign", campaign_id=str(campaign_id))
    return new_campaign


@router.get("/outreach/campaigns", response_model=OutreachCampaignListResponse, tags=["outreach"])
async def list_outreach_campaigns(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
) -> OutreachCampaignListResponse:
    """List outreach campaigns with pagination."""
    campaigns = list(_outreach_campaigns.values())
    if status:
        campaigns = [c for c in campaigns if c.status.value == status]

    total = len(campaigns)
    start = (page - 1) * page_size
    end = start + page_size
    items = campaigns[start:end]
    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return OutreachCampaignListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/outreach/campaigns/{campaign_id}", response_model=OutreachCampaignResponse, tags=["outreach"])
async def get_outreach_campaign(campaign_id: UUID) -> OutreachCampaignResponse:
    """Get a specific outreach campaign by ID."""
    if campaign_id not in _outreach_campaigns:
        raise HTTPException(status_code=404, detail="Outreach campaign not found")
    return _outreach_campaigns[campaign_id]


@router.put("/outreach/campaigns/{campaign_id}", response_model=OutreachCampaignResponse, tags=["outreach"])
async def update_outreach_campaign(
    campaign_id: UUID, campaign_update: OutreachCampaignUpdate
) -> OutreachCampaignResponse:
    """Update an outreach campaign."""
    if campaign_id not in _outreach_campaigns:
        raise HTTPException(status_code=404, detail="Outreach campaign not found")

    existing = _outreach_campaigns[campaign_id]
    update_data = campaign_update.model_dump(exclude_unset=True)
    updated = existing.model_copy(update=update_data)
    _outreach_campaigns[campaign_id] = updated
    logger.info("Updated outreach campaign", campaign_id=str(campaign_id))
    return updated


@router.delete("/outreach/campaigns/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["outreach"])
async def delete_outreach_campaign(campaign_id: UUID) -> None:
    """Delete an outreach campaign."""
    if campaign_id not in _outreach_campaigns:
        raise HTTPException(status_code=404, detail="Outreach campaign not found")
    del _outreach_campaigns[campaign_id]
    logger.info("Deleted outreach campaign", campaign_id=str(campaign_id))


# ---------------------------------------------------------------------------
# Outreach Templates
# ---------------------------------------------------------------------------


@router.post("/outreach/templates", response_model=OutreachTemplateResponse, status_code=status.HTTP_201_CREATED, tags=["outreach"])
async def create_outreach_template(template: OutreachTemplateCreate) -> OutreachTemplateResponse:
    """Create a new outreach template."""
    from datetime import datetime
    from uuid import uuid4

    template_id = uuid4()
    new_template = OutreachTemplateResponse(
        id=template_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        name=template.name,
        subject_template=template.subject_template,
        body_template=template.body_template,
        channel=template.channel,
        tone=template.tone,
        variables=template.variables,
    )
    _outreach_templates[template_id] = new_template
    logger.info("Created outreach template", template_id=str(template_id))
    return new_template


@router.get("/outreach/templates", response_model=list[OutreachTemplateResponse], tags=["outreach"])
async def list_outreach_templates() -> list[OutreachTemplateResponse]:
    """List all outreach templates."""
    return list(_outreach_templates.values())


@router.get("/outreach/templates/{template_id}", response_model=OutreachTemplateResponse, tags=["outreach"])
async def get_outreach_template(template_id: UUID) -> OutreachTemplateResponse:
    """Get a specific outreach template by ID."""
    if template_id not in _outreach_templates:
        raise HTTPException(status_code=404, detail="Outreach template not found")
    return _outreach_templates[template_id]


@router.put("/outreach/templates/{template_id}", response_model=OutreachTemplateResponse, tags=["outreach"])
async def update_outreach_template(
    template_id: UUID, template_update: OutreachTemplateUpdate
) -> OutreachTemplateResponse:
    """Update an outreach template."""
    if template_id not in _outreach_templates:
        raise HTTPException(status_code=404, detail="Outreach template not found")

    existing = _outreach_templates[template_id]
    update_data = template_update.model_dump(exclude_unset=True)
    updated = existing.model_copy(update=update_data)
    _outreach_templates[template_id] = updated
    logger.info("Updated outreach template", template_id=str(template_id))
    return updated


@router.delete("/outreach/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["outreach"])
async def delete_outreach_template(template_id: UUID) -> None:
    """Delete an outreach template."""
    if template_id not in _outreach_templates:
        raise HTTPException(status_code=404, detail="Outreach template not found")
    del _outreach_templates[template_id]
    logger.info("Deleted outreach template", template_id=str(template_id))


# ---------------------------------------------------------------------------
# Agent Endpoints
# ---------------------------------------------------------------------------


@router.post("/agents/discover", response_model=DiscoveryResult, tags=["agents"])
async def discover_candidates(
    request: DiscoveryRequest,
    registry: AgentRegistry = Depends(get_agent_registry),
) -> DiscoveryResult:
    """Run candidate discovery agent."""
    agent = registry.discovery_agent
    return await agent.run(request)


@router.post("/agents/segment", response_model=SegmentationResult, tags=["agents"])
async def segment_pool(
    request: SegmentationRequest,
    registry: AgentRegistry = Depends(get_agent_registry),
) -> SegmentationResult:
    """Run pool segmentation agent."""
    agent = registry.segmentation_agent
    return await agent.run(request)


@router.post("/agents/score", response_model=ScoringResult, tags=["agents"])
async def score_candidates(
    request: ScoringRequest,
    registry: AgentRegistry = Depends(get_agent_registry),
) -> ScoringResult:
    """Run talent scoring agent."""
    agent = registry.scoring_agent
    return await agent.run(request)


@router.post("/agents/outreach", response_model=OutreachResult, tags=["agents"])
async def run_outreach(
    request: OutreachRequest,
    registry: AgentRegistry = Depends(get_agent_registry),
) -> OutreachResult:
    """Run outreach agent."""
    agent = registry.outreach_agent
    return await agent.run(request)


@router.post("/agents/optimize-engagement", response_model=EngagementOptimizationResult, tags=["agents"])
async def optimize_engagement(
    request: EngagementOptimizationRequest,
    registry: AgentRegistry = Depends(get_agent_registry),
) -> EngagementOptimizationResult:
    """Run engagement optimizer agent."""
    agent = registry.engagement_agent
    return await agent.run(request)
