"""Campaign management API routes."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from api.models.schemas import (
    CampaignCreateRequest,
    CampaignListResponse,
    CampaignResponse,
    CampaignStatus,
    CampaignUpdateRequest,
    OptimizationRequest,
    OptimizationResponse,
)
from core.exceptions import CampaignNotFoundError, CampaignValidationError
from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/campaigns", tags=["campaigns"])

# In-memory store for demonstration — replace with database in production
_campaigns: dict[str, dict[str, Any]] = {}


@router.post(
    "",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new campaign",
    description="Create a new marketing campaign with the specified configuration.",
)
async def create_campaign(request: CampaignCreateRequest) -> CampaignResponse:
    """Create a new campaign.

    Args:
        request: Campaign creation parameters.

    Returns:
        The created campaign.

    Raises:
        HTTPException: If validation fails.
    """
    campaign_id = f"camp_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow()

    campaign_data = {
        "id": campaign_id,
        "name": request.name,
        "description": request.description,
        "status": CampaignStatus.DRAFT.value,
        "goals": [g.value for g in request.goals],
        "total_budget": request.total_budget,
        "daily_budget": request.daily_budget,
        "channels": [c.value for c in request.channels],
        "duration_days": request.duration_days,
        "target_audience": request.target_audience,
        "brand_voice": request.brand_voice,
        "key_message": request.key_message,
        "industry": request.industry,
        "created_at": now,
        "updated_at": now,
        "performance_metrics": {},
    }

    _campaigns[campaign_id] = campaign_data

    logger.info("campaign_created", campaign_id=campaign_id, name=request.name)

    return CampaignResponse(**campaign_data)


@router.get(
    "",
    response_model=CampaignListResponse,
    summary="List all campaigns",
    description="Retrieve a paginated list of all campaigns.",
)
async def list_campaigns(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status_filter: CampaignStatus | None = Query(default=None, description="Filter by status"),
) -> CampaignListResponse:
    """List campaigns with pagination.

    Args:
        page: Page number.
        page_size: Items per page.
        status_filter: Optional status filter.

    Returns:
        Paginated list of campaigns.
    """
    campaigns = list(_campaigns.values())

    if status_filter:
        campaigns = [c for c in campaigns if c["status"] == status_filter.value]

    total = len(campaigns)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = campaigns[start:end]

    return CampaignListResponse(
        campaigns=[CampaignResponse(**c) for c in paginated],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{campaign_id}",
    response_model=CampaignResponse,
    summary="Get campaign details",
    description="Retrieve detailed information about a specific campaign.",
)
async def get_campaign(campaign_id: str) -> CampaignResponse:
    """Get a campaign by ID.

    Args:
        campaign_id: Campaign identifier.

    Returns:
        Campaign details.

    Raises:
        HTTPException: If campaign not found.
    """
    campaign = _campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )

    return CampaignResponse(**campaign)


@router.put(
    "/{campaign_id}",
    response_model=CampaignResponse,
    summary="Update campaign",
    description="Update an existing campaign's configuration.",
)
async def update_campaign(campaign_id: str, request: CampaignUpdateRequest) -> CampaignResponse:
    """Update a campaign.

    Args:
        campaign_id: Campaign identifier.
        request: Update parameters.

    Returns:
        Updated campaign.

    Raises:
        HTTPException: If campaign not found.
    """
    campaign = _campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "goals" and value is not None:
            campaign[key] = [g.value if hasattr(g, "value") else g for g in value]
        elif key == "channels" and value is not None:
            campaign[key] = [c.value if hasattr(c, "value") else c for c in value]
        elif key == "status" and value is not None:
            campaign[key] = value.value if hasattr(value, "value") else value
        else:
            campaign[key] = value

    campaign["updated_at"] = datetime.utcnow()

    logger.info("campaign_updated", campaign_id=campaign_id)

    return CampaignResponse(**campaign)


@router.delete(
    "/{campaign_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete campaign",
    description="Delete a campaign permanently.",
)
async def delete_campaign(campaign_id: str) -> None:
    """Delete a campaign.

    Args:
        campaign_id: Campaign identifier.

    Raises:
        HTTPException: If campaign not found.
    """
    if campaign_id not in _campaigns:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )

    del _campaigns[campaign_id]
    logger.info("campaign_deleted", campaign_id=campaign_id)


@router.post(
    "/{campaign_id}/optimize",
    response_model=OptimizationResponse,
    summary="Trigger optimization",
    description="Trigger an optimization cycle for the specified campaign.",
)
async def optimize_campaign(
    campaign_id: str, request: OptimizationRequest | None = None
) -> OptimizationResponse:
    """Trigger campaign optimization.

    Args:
        campaign_id: Campaign identifier.
        request: Optional optimization parameters.

    Returns:
        Optimization results.

    Raises:
        HTTPException: If campaign not found.
    """
    campaign = _campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )

    optimization_id = f"opt_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow()

    # In production, this would dispatch to the agent orchestration layer
    result = OptimizationResponse(
        campaign_id=campaign_id,
        optimization_id=optimization_id,
        status="completed",
        started_at=now,
        completed_at=now,
        results={
            "optimization_type": request.optimization_type if request else "full",
            "bid_adjustments": [],
            "budget_reallocation": [],
            "audience_updates": [],
            "creative_recommendations": [],
        },
        recommendations=[
            "Increase budget allocation to high-performing channels",
            "Expand lookalike audiences based on converters",
            "Test new creative variants for underperforming ad groups",
        ],
    )

    logger.info(
        "optimization_completed",
        campaign_id=campaign_id,
        optimization_id=optimization_id,
    )

    return result


@router.get(
    "/{campaign_id}/status",
    response_model=dict[str, Any],
    summary="Get campaign status",
    description="Get detailed status information for a campaign.",
)
async def get_campaign_status(campaign_id: str) -> dict[str, Any]:
    """Get campaign status.

    Args:
        campaign_id: Campaign identifier.

    Returns:
        Campaign status information.

    Raises:
        HTTPException: If campaign not found.
    """
    campaign = _campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )

    return {
        "campaign_id": campaign_id,
        "status": campaign["status"],
        "performance_metrics": campaign.get("performance_metrics", {}),
        "last_optimized": campaign.get("updated_at"),
        "active_agents": [],
    }
