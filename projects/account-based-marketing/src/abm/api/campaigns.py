"""API routes for campaign management."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from abm.agents.channel_orchestrator import ChannelOrchestratorAgent
from abm.agents.content_personalization import ContentPersonalizationAgent, ContentType, PersonaType
from abm.agents.performance_analytics import PerformanceAnalyticsAgent

router = APIRouter()

# Agent instances (would use dependency injection in production)
content_agent = ContentPersonalizationAgent()
orchestrator_agent = ChannelOrchestratorAgent()
analytics_agent = PerformanceAnalyticsAgent()


class CampaignCreateRequest(BaseModel):
    """Request model for creating a campaign."""

    name: str = Field(..., min_length=1, max_length=200)
    account_ids: list[str] = Field(..., min_items=1)
    content_type: ContentType = ContentType.EMAIL
    persona: PersonaType = PersonaType.EXECUTIVE
    start_date: datetime | None = None
    budget: float | None = Field(default=None, gt=0)
    description: str | None = None


class CampaignResponse(BaseModel):
    """Response model for campaign details."""

    campaign_id: str
    name: str
    status: str
    account_count: int
    content_type: str
    persona: str
    created_at: str


@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(request: CampaignCreateRequest) -> CampaignResponse:
    """Create a new ABM campaign.

    Args:
        request: Campaign creation parameters.

    Returns:
        Created campaign details.

    Raises:
        HTTPException: If request is invalid.
    """
    campaign_id = f"campaign_{datetime.now(tz=timezone.utc).strftime('%Y%m%d%H%M%S')}"

    return CampaignResponse(
        campaign_id=campaign_id,
        name=request.name,
        status="draft",
        account_count=len(request.account_ids),
        content_type=request.content_type.value,
        persona=request.persona.value,
        created_at=datetime.now(tz=timezone.utc).isoformat(),
    )


@router.get("/{campaign_id}", response_model=dict[str, Any])
async def get_campaign(campaign_id: str) -> dict[str, Any]:
    """Get campaign details.

    Args:
        campaign_id: The campaign identifier.

    Returns:
        Campaign details.

    Raises:
        HTTPException: If campaign is not found.
    """
    if not campaign_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="campaign_id is required",
        )

    return {
        "campaign_id": campaign_id,
        "name": "Q1 ABM Campaign",
        "status": "active",
        "accounts": ["acc_001", "acc_002", "acc_003"],
        "channels": ["email", "linkedin_ads"],
        "start_date": "2024-01-01T00:00:00",
    }


@router.get("/{campaign_id}/analytics", response_model=dict[str, Any])
async def get_campaign_analytics(campaign_id: str) -> dict[str, Any]:
    """Get comprehensive analytics for a campaign.

    Args:
        campaign_id: The campaign identifier.

    Returns:
        Campaign analytics report.

    Raises:
        HTTPException: If campaign_id is invalid.
    """
    try:
        report = await analytics_agent.generate_report(campaign_id)
        return report
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post("/{campaign_id}/personalize", response_model=dict[str, Any])
async def personalize_campaign_content(campaign_id: str) -> dict[str, Any]:
    """Generate personalized content for all accounts in a campaign.

    Args:
        campaign_id: The campaign identifier.

    Returns:
        Generated content for each account.

    Raises:
        HTTPException: If campaign_id is invalid.
    """
    if not campaign_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="campaign_id is required",
        )

    # Mock account IDs - in production, fetch from campaign data
    account_ids = ["acc_001", "acc_002", "acc_003"]

    content = await content_agent.generate_campaign_content(
        account_ids=account_ids,
        content_type=ContentType.EMAIL,
        campaign_context={"campaign_id": campaign_id},
    )

    return {
        "campaign_id": campaign_id,
        "content_generated": len(content),
        "content": [
            {
                "content_id": c.content_id,
                "account_id": c.account_id,
                "content_type": c.content_type.value,
                "subject": c.subject,
                "body": c.body,
                "call_to_action": c.call_to_action,
            }
            for c in content
        ],
    }


@router.post("/{campaign_id}/orchestrate", response_model=dict[str, Any])
async def orchestrate_campaign(campaign_id: str) -> dict[str, Any]:
    """Trigger channel orchestration for a campaign.

    Args:
        campaign_id: The campaign identifier.

    Returns:
        Orchestration execution results.

    Raises:
        HTTPException: If campaign_id is invalid.
    """
    if not campaign_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="campaign_id is required",
        )

    account_ids = ["acc_001", "acc_002", "acc_003"]

    plan = await orchestrator_agent.create_plan(
        account_ids=account_ids,
        campaign_id=campaign_id,
    )

    results = await orchestrator_agent.execute_plan(plan)

    return {
        "campaign_id": campaign_id,
        "plan_id": plan.plan_id,
        "execution_results": results,
    }
