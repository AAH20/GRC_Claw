"""Campaign API endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/campaigns", tags=["campaigns"])


class CampaignCreateRequest(BaseModel):
    """Request model for creating a campaign."""

    name: str = Field(..., min_length=1, max_length=200, description="Campaign name")
    campaign_type: str = Field(..., description="Type: email, social, paid, content")
    target_audience: str = Field(..., description="Target audience segment")
    budget: float | None = Field(default=None, ge=0, description="Campaign budget in USD")
    start_date: datetime = Field(..., description="Campaign start date")
    end_date: datetime = Field(..., description="Campaign end date")
    goals: list[str] = Field(default_factory=list, description="Campaign goals")
    channels: list[str] = Field(default_factory=list, description="Marketing channels")


class CampaignResponse(BaseModel):
    """Response model for campaign operations."""

    id: str = Field(..., description="Campaign identifier")
    name: str = Field(..., description="Campaign name")
    campaign_type: str = Field(..., description="Campaign type")
    status: str = Field(default="draft", description="Campaign status")
    target_audience: str = Field(..., description="Target audience")
    budget: float | None = Field(default=None, description="Budget in USD")
    start_date: datetime = Field(..., description="Start date")
    end_date: datetime = Field(..., description="End date")
    goals: list[str] = Field(default_factory=list, description="Campaign goals")
    channels: list[str] = Field(default_factory=list, description="Channels")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )


# In-memory store for development (replace with database in production)
_campaigns: dict[str, CampaignResponse] = {}


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(request: CampaignCreateRequest) -> CampaignResponse:
    """Create a new marketing campaign.

    Args:
        request: Campaign creation parameters.

    Returns:
        The created campaign.

    Raises:
        HTTPException: If end_date is before start_date.
    """
    if request.end_date <= request.start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_date must be after start_date",
        )

    campaign_id = str(uuid4())
    campaign = CampaignResponse(
        id=campaign_id,
        name=request.name,
        campaign_type=request.campaign_type,
        status="draft",
        target_audience=request.target_audience,
        budget=request.budget,
        start_date=request.start_date,
        end_date=request.end_date,
        goals=request.goals,
        channels=request.channels,
    )

    _campaigns[campaign_id] = campaign

    logger.info("campaign_created", campaign_id=campaign_id, name=request.name)

    return campaign


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: str) -> CampaignResponse:
    """Get a campaign by ID.

    Args:
        campaign_id: Campaign identifier.

    Returns:
        The requested campaign.

    Raises:
        HTTPException: If campaign is not found.
    """
    campaign = _campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )
    return campaign


@router.get("", response_model=list[CampaignResponse])
async def list_campaigns(
    status_filter: str | None = None,
    campaign_type: str | None = None,
) -> list[CampaignResponse]:
    """List all campaigns with optional filtering.

    Args:
        status_filter: Filter by campaign status.
        campaign_type: Filter by campaign type.

    Returns:
        List of campaigns matching the filters.
    """
    campaigns = list(_campaigns.values())

    if status_filter:
        campaigns = [c for c in campaigns if c.status == status_filter]
    if campaign_type:
        campaigns = [c for c in campaigns if c.campaign_type == campaign_type]

    return campaigns


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(campaign_id: str, updates: dict) -> CampaignResponse:
    """Update a campaign.

    Args:
        campaign_id: Campaign identifier.
        updates: Fields to update.

    Returns:
        The updated campaign.

    Raises:
        HTTPException: If campaign is not found.
    """
    campaign = _campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )

    for key, value in updates.items():
        if hasattr(campaign, key):
            setattr(campaign, key, value)

    campaign.updated_at = datetime.utcnow()
    _campaigns[campaign_id] = campaign

    logger.info("campaign_updated", campaign_id=campaign_id)

    return campaign


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(campaign_id: str) -> None:
    """Delete a campaign.

    Args:
        campaign_id: Campaign identifier.

    Raises:
        HTTPException: If campaign is not found.
    """
    if campaign_id not in _campaigns:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )

    del _campaigns[campaign_id]
    logger.info("campaign_deleted", campaign_id=campaign_id)
