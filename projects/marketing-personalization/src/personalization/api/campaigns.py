"""Campaign API routes."""

from __future__ import annotations

from datetime import UTC
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

router = APIRouter()


class CampaignCreate(BaseModel):
    """Campaign creation request model."""

    name: str
    description: str | None = None
    campaign_type: str = "email"
    segment_id: str | None = None
    budget: float = 0.0
    start_date: str | None = None
    end_date: str | None = None
    content: dict[str, Any] = Field(default_factory=dict)


class CampaignUpdate(BaseModel):
    """Campaign update request model."""

    name: str | None = None
    description: str | None = None
    status: str | None = None
    budget: float | None = None
    content: dict[str, Any] | None = None


class CampaignResponse(BaseModel):
    """Campaign response model."""

    campaign_id: str
    name: str
    status: str
    campaign_type: str
    segment_id: str | None = None
    budget: float = 0.0
    created_at: str
    updated_at: str


_campaigns: dict[str, dict[str, Any]] = {}


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(campaign: CampaignCreate) -> CampaignResponse:
    """Create a new marketing campaign."""
    import uuid
    from datetime import datetime

    campaign_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    campaign_data = {
        "campaign_id": campaign_id,
        "name": campaign.name,
        "status": "draft",
        "campaign_type": campaign.campaign_type,
        "segment_id": campaign.segment_id,
        "budget": campaign.budget,
        "created_at": now,
        "updated_at": now,
    }
    _campaigns[campaign_id] = campaign_data
    logger.info("Campaign created", campaign_id=campaign_id, name=campaign.name)
    return CampaignResponse(**campaign_data)


@router.get("", response_model=list[CampaignResponse])
async def list_campaigns() -> list[CampaignResponse]:
    """List all campaigns."""
    logger.info("Listing campaigns", count=len(_campaigns))
    return [CampaignResponse(**c) for c in _campaigns.values()]


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: str) -> CampaignResponse:
    """Get a campaign by ID."""
    if campaign_id not in _campaigns:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )
    return CampaignResponse(**_campaigns[campaign_id])


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(campaign_id: str, campaign: CampaignUpdate) -> CampaignResponse:
    """Update a campaign."""
    if campaign_id not in _campaigns:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )

    from datetime import datetime

    existing = _campaigns[campaign_id]
    update_data = campaign.model_dump(exclude_unset=True)
    existing.update(update_data)
    existing["updated_at"] = datetime.now(UTC).isoformat()
    logger.info("Campaign updated", campaign_id=campaign_id)
    return CampaignResponse(**existing)


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(campaign_id: str) -> None:
    """Delete a campaign."""
    if campaign_id not in _campaigns:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )
    del _campaigns[campaign_id]
    logger.info("Campaign deleted", campaign_id=campaign_id)
