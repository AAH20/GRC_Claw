"""API routes for campaign management."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ecommerce_marketing.agents.email import EmailAgent, EmailCampaignRequest

logger = structlog.get_logger(__name__)

router = APIRouter()


class CampaignCreateRequest(BaseModel):
    """Request model for creating a campaign."""

    name: str = Field(..., min_length=1, max_length=200, description="Campaign name")
    campaign_type: str = Field(..., description="Campaign type (email, social, cart_recovery)")
    segment: str = Field(default="all", description="Target customer segment")
    context: dict[str, Any] = Field(default_factory=dict, description="Campaign context")


class CampaignResponse(BaseModel):
    """Response model for campaign operations."""

    id: str = Field(..., description="Campaign identifier")
    name: str = Field(..., description="Campaign name")
    status: str = Field(..., description="Campaign status")
    message: str = Field(default="", description="Status message")


class CampaignListResponse(BaseModel):
    """Response model for listing campaigns."""

    campaigns: list[CampaignResponse] = Field(..., description="List of campaigns")
    total: int = Field(..., description="Total number of campaigns")


# In-memory store for demo purposes — replace with database in production
_campaigns: dict[str, dict[str, Any]] = {}


@router.post("/campaigns", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(request: CampaignCreateRequest) -> CampaignResponse:
    """Create a new marketing campaign.

    Args:
        request: Campaign creation request.

    Returns:
        Created campaign details.

    Raises:
        HTTPException: If campaign creation fails.
    """
    campaign_id = str(uuid.uuid4())
    logger.info("Creating campaign", campaign_id=campaign_id, name=request.name, type=request.campaign_type)

    try:
        _campaigns[campaign_id] = {
            "id": campaign_id,
            "name": request.name,
            "type": request.campaign_type,
            "segment": request.segment,
            "status": "created",
        }

        return CampaignResponse(
            id=campaign_id,
            name=request.name,
            status="created",
            message=f"Campaign '{request.name}' created successfully",
        )
    except Exception as exc:
        logger.error("Failed to create campaign", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create campaign: {exc}",
        ) from exc


@router.get("/campaigns", response_model=CampaignListResponse)
async def list_campaigns() -> CampaignListResponse:
    """List all campaigns.

    Returns:
        List of all campaigns.
    """
    campaigns = [
        CampaignResponse(
            id=c["id"],
            name=c["name"],
            status=c["status"],
        )
        for c in _campaigns.values()
    ]
    return CampaignListResponse(campaigns=campaigns, total=len(campaigns))


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: str) -> CampaignResponse:
    """Get a specific campaign by ID.

    Args:
        campaign_id: Campaign identifier.

    Returns:
        Campaign details.

    Raises:
        HTTPException: If campaign is not found.
    """
    campaign = _campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )

    return CampaignResponse(
        id=campaign["id"],
        name=campaign["name"],
        status=campaign["status"],
    )


@router.post("/campaigns/{campaign_id}/email", response_model=CampaignResponse)
async def create_email_campaign(
    campaign_id: str,
    request: EmailCampaignRequest,
) -> CampaignResponse:
    """Create an email campaign for a specific campaign.

    Args:
        campaign_id: Parent campaign identifier.
        request: Email campaign request.

    Returns:
        Created email campaign details.

    Raises:
        HTTPException: If campaign not found or creation fails.
    """
    if campaign_id not in _campaigns:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )

    try:
        agent = EmailAgent()
        email_campaign = await agent.create_campaign(request)

        _campaigns[campaign_id]["email_campaign"] = email_campaign.model_dump()
        _campaigns[campaign_id]["status"] = "email_created"

        return CampaignResponse(
            id=campaign_id,
            name=request.name,
            status="email_created",
            message=f"Email campaign '{request.name}' created",
        )
    except Exception as exc:
        logger.error("Failed to create email campaign", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create email campaign: {exc}",
        ) from exc


@router.get("/analytics/campaign/{campaign_id}")
async def get_campaign_analytics(campaign_id: str) -> dict[str, Any]:
    """Get analytics for a specific campaign.

    Args:
        campaign_id: Campaign identifier.

    Returns:
        Campaign analytics data.

    Raises:
        HTTPException: If campaign not found.
    """
    if campaign_id not in _campaigns:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )

    # Return placeholder analytics — integrate with real data source in production
    return {
        "campaign_id": campaign_id,
        "metrics": {
            "impressions": 0,
            "clicks": 0,
            "conversions": 0,
            "revenue": 0.0,
            "spend": 0.0,
        },
        "insights": [],
        "recommendations": [],
    }
