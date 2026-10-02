"""Campaign API routes for PPC Manager."""

from __future__ import annotations

from datetime import UTC
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

router = APIRouter()


class CampaignCreate(BaseModel):
    """Request model for creating a campaign.

    Attributes:
        name: Campaign name.
        platform: Ad platform (google, meta, linkedin, tiktok).
        budget: Daily budget in USD.
        status: Campaign status (active, paused, archived).
    """

    name: str = Field(..., min_length=1, max_length=255)
    platform: str = Field(..., pattern="^(google|meta|linkedin|tiktok)$")
    budget: float = Field(..., gt=0)
    status: str = Field(default="active", pattern="^(active|paused|archived)$")


class CampaignUpdate(BaseModel):
    """Request model for updating a campaign.

    Attributes:
        name: Campaign name.
        budget: Daily budget in USD.
        status: Campaign status.
    """

    name: str | None = Field(default=None, min_length=1, max_length=255)
    budget: float | None = Field(default=None, gt=0)
    status: str | None = Field(default=None, pattern="^(active|paused|archived)$")


class CampaignResponse(BaseModel):
    """Response model for a campaign.

    Attributes:
        id: Campaign identifier.
        name: Campaign name.
        platform: Ad platform.
        budget: Daily budget in USD.
        status: Campaign status.
        created_at: Creation timestamp.
    """

    id: str
    name: str
    platform: str
    budget: float
    status: str
    created_at: str


# In-memory store for demo purposes
_campaigns: dict[str, dict[str, Any]] = {}
_id_counter = 0


def _next_id() -> str:
    """Generate the next campaign ID.

    Returns:
        A unique campaign ID string.
    """
    global _id_counter
    _id_counter += 1
    return f"campaign_{_id_counter}"


@router.get("", response_model=list[CampaignResponse])
async def list_campaigns() -> list[dict[str, Any]]:
    """List all campaigns.

    Returns:
        A list of all campaigns.
    """
    logger.info("Listing campaigns", count=len(_campaigns))
    return list(_campaigns.values())


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(campaign: CampaignCreate) -> dict[str, Any]:
    """Create a new campaign.

    Args:
        campaign: The campaign creation data.

    Returns:
        The created campaign.
    """
    from datetime import datetime

    campaign_id = _next_id()
    new_campaign = {
        "id": campaign_id,
        "name": campaign.name,
        "platform": campaign.platform,
        "budget": campaign.budget,
        "status": campaign.status,
        "created_at": datetime.now(UTC).isoformat(),
    }
    _campaigns[campaign_id] = new_campaign
    logger.info("Campaign created", campaign_id=campaign_id, name=campaign.name)
    return new_campaign


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: str) -> dict[str, Any]:
    """Get a campaign by ID.

    Args:
        campaign_id: The campaign identifier.

    Returns:
        The campaign details.

    Raises:
        HTTPException: If the campaign is not found.
    """
    if campaign_id not in _campaigns:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )
    return _campaigns[campaign_id]


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(campaign_id: str, update: CampaignUpdate) -> dict[str, Any]:
    """Update a campaign.

    Args:
        campaign_id: The campaign identifier.
        update: The update data.

    Returns:
        The updated campaign.

    Raises:
        HTTPException: If the campaign is not found.
    """
    if campaign_id not in _campaigns:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )

    campaign = _campaigns[campaign_id]
    if update.name is not None:
        campaign["name"] = update.name
    if update.budget is not None:
        campaign["budget"] = update.budget
    if update.status is not None:
        campaign["status"] = update.status

    logger.info("Campaign updated", campaign_id=campaign_id)
    return campaign


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(campaign_id: str) -> None:
    """Delete a campaign.

    Args:
        campaign_id: The campaign identifier.

    Raises:
        HTTPException: If the campaign is not found.
    """
    if campaign_id not in _campaigns:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )
    del _campaigns[campaign_id]
    logger.info("Campaign deleted", campaign_id=campaign_id)
