"""Campaign API routes — CRUD operations and optimization triggers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

router = APIRouter()


# ─── Request/Response Models ────────────────────────────────────────


class CampaignCreateRequest(BaseModel):
    """Request model for creating a campaign."""

    name: str = Field(..., min_length=1, max_length=200)
    business_goal: str = Field(..., min_length=1, max_length=1000)
    total_budget: float = Field(..., gt=0)
    duration_days: int = Field(..., gt=0, le=365)
    platforms: list[str] = Field(default=["meta", "google", "linkedin"])
    constraints: dict[str, Any] | None = None


class CampaignUpdateRequest(BaseModel):
    """Request model for updating a campaign."""

    name: str | None = Field(None, min_length=1, max_length=200)
    status: str | None = None
    total_budget: float | None = Field(None, gt=0)
    duration_days: int | None = Field(None, gt=0, le=365)


class CampaignResponse(BaseModel):
    """Response model for campaign data."""

    id: str
    name: str
    business_goal: str
    total_budget: float
    duration_days: int
    platforms: list[str]
    status: str
    created_at: str
    updated_at: str


class OptimizationResponse(BaseModel):
    """Response model for optimization results."""

    campaign_id: str
    status: str
    recommendations: list[dict[str, Any]]
    timestamp: str


# ─── In-Memory Store (replace with database in production) ──────────

_campaigns: dict[str, dict[str, Any]] = {}


# ─── Routes ─────────────────────────────────────────────────────────


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(request: CampaignCreateRequest) -> CampaignResponse:
    """Create a new advertising campaign.

    Args:
        request: Campaign creation parameters.

    Returns:
        The created campaign.

    Raises:
        HTTPException: If campaign creation fails.
    """
    campaign_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    campaign: dict[str, Any] = {
        "id": campaign_id,
        "name": request.name,
        "business_goal": request.business_goal,
        "total_budget": request.total_budget,
        "duration_days": request.duration_days,
        "platforms": request.platforms,
        "status": "draft",
        "constraints": request.constraints,
        "created_at": now,
        "updated_at": now,
    }

    _campaigns[campaign_id] = campaign
    logger.info("Campaign created", campaign_id=campaign_id, name=request.name)

    return CampaignResponse(**campaign)


@router.get("", response_model=list[CampaignResponse])
async def list_campaigns() -> list[CampaignResponse]:
    """List all campaigns.

    Returns:
        List of all campaigns.
    """
    return [CampaignResponse(**c) for c in _campaigns.values()]


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: str) -> CampaignResponse:
    """Get a specific campaign by ID.

    Args:
        campaign_id: The campaign identifier.

    Returns:
        The campaign details.

    Raises:
        HTTPException: If campaign is not found.
    """
    campaign = _campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )
    return CampaignResponse(**campaign)


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(campaign_id: str, request: CampaignUpdateRequest) -> CampaignResponse:
    """Update an existing campaign.

    Args:
        campaign_id: The campaign identifier.
        request: Campaign update parameters.

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

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            campaign[key] = value

    campaign["updated_at"] = datetime.now(UTC).isoformat()
    logger.info("Campaign updated", campaign_id=campaign_id)

    return CampaignResponse(**campaign)


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(campaign_id: str) -> None:
    """Delete a campaign.

    Args:
        campaign_id: The campaign identifier.

    Raises:
        HTTPException: If campaign is not found.
    """
    if campaign_id not in _campaigns:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )
    del _campaigns[campaign_id]
    logger.info("Campaign deleted", campaign_id=campaign_id)


@router.post("/{campaign_id}/optimize", response_model=OptimizationResponse)
async def optimize_campaign(campaign_id: str) -> OptimizationResponse:
    """Trigger an optimization cycle for a campaign.

    Args:
        campaign_id: The campaign identifier.

    Returns:
        Optimization results with recommendations.

    Raises:
        HTTPException: If campaign is not found.
    """
    campaign = _campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )

    logger.info("Optimization triggered", campaign_id=campaign_id)

    # In production, this would invoke the multi-agent orchestration
    recommendations = [
        {
            "agent": "bidding",
            "action": "increase_bid",
            "platform": "meta",
            "value": 1.10,
            "reason": "Strong ROAS performance",
        },
        {
            "agent": "creative",
            "action": "refresh_creative",
            "platform": "google",
            "reason": "CTR declining — creative fatigue detected",
        },
    ]

    return OptimizationResponse(
        campaign_id=campaign_id,
        status="completed",
        recommendations=recommendations,
        timestamp=datetime.now(UTC).isoformat(),
    )
