"""Campaign API endpoints.

RESTful API for campaign management including creation, video assignment,
analytics aggregation, and lifecycle management.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class CampaignCreateRequest(BaseModel):
    """Request model for creating a campaign."""

    name: str = Field(..., min_length=1, max_length=200, description="Campaign name")
    description: str = Field(default="", max_length=5000)
    start_date: str | None = Field(default=None, description="ISO 8601 start date")
    end_date: str | None = Field(default=None, description="ISO 8601 end date")
    budget: float = Field(default=0.0, ge=0)
    target_audience: str = Field(default="", max_length=500)
    goals: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class CampaignUpdateRequest(BaseModel):
    """Request model for updating a campaign."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: str | None = None
    end_date: str | None = None
    budget: float | None = Field(default=None, ge=0)


class AddVideoRequest(BaseModel):
    """Request model for adding a video to a campaign."""

    video_id: str = Field(..., description="Video ID to add")


class CampaignResponse(BaseModel):
    """Response model for campaign data."""

    id: str
    name: str
    description: str
    status: str
    video_count: int = 0
    video_ids: list[str] = Field(default_factory=list)
    start_date: str | None = None
    end_date: str | None = None
    budget: float = 0.0
    target_audience: str = ""
    goals: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class CampaignListResponse(BaseModel):
    """Response model for campaign list."""

    campaigns: list[CampaignResponse]
    total: int
    page: int
    page_size: int


class CampaignAnalyticsResponse(BaseModel):
    """Response model for campaign analytics."""

    campaign_id: str
    video_count: int
    total_views: int
    total_watch_time_hours: float
    total_likes: int
    total_comments: int
    total_shares: int
    total_subscribers_gained: int
    total_revenue: float
    overall_engagement_rate: float
    platform_breakdown: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# In-memory store (replace with database in production)
# ---------------------------------------------------------------------------

_campaigns: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _get_campaign_or_404(campaign_id: str) -> dict[str, Any]:
    """Get a campaign by ID or raise 404."""
    if campaign_id not in _campaigns:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign '{campaign_id}' not found",
        )
    return _campaigns[campaign_id]


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(request: CampaignCreateRequest) -> CampaignResponse:
    """Create a new marketing campaign."""
    campaign_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    campaign = {
        "id": campaign_id,
        "name": request.name,
        "description": request.description,
        "status": "draft",
        "video_ids": [],
        "start_date": request.start_date,
        "end_date": request.end_date,
        "budget": request.budget,
        "target_audience": request.target_audience,
        "goals": request.goals,
        "tags": request.tags,
        "created_at": now,
        "updated_at": now,
        "metadata": {},
    }

    _campaigns[campaign_id] = campaign
    logger.info("Campaign created", extra={"campaign_id": campaign_id, "name": request.name})
    return CampaignResponse(**campaign)


@router.get("", response_model=CampaignListResponse)
async def list_campaigns(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
) -> CampaignListResponse:
    """List campaigns with pagination and filtering."""
    campaigns = list(_campaigns.values())

    if status_filter:
        campaigns = [c for c in campaigns if c["status"] == status_filter]

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


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: str) -> CampaignResponse:
    """Get a campaign by ID."""
    campaign = _get_campaign_or_404(campaign_id)
    return CampaignResponse(**campaign)


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(campaign_id: str, request: CampaignUpdateRequest) -> CampaignResponse:
    """Update a campaign."""
    campaign = _get_campaign_or_404(campaign_id)

    update_data = request.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        if value is not None:
            campaign[field_name] = value

    campaign["updated_at"] = datetime.now(UTC).isoformat()
    logger.info("Campaign updated", extra={"campaign_id": campaign_id})
    return CampaignResponse(**campaign)


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(campaign_id: str) -> None:
    """Delete a campaign."""
    _get_campaign_or_404(campaign_id)
    del _campaigns[campaign_id]
    logger.info("Campaign deleted", extra={"campaign_id": campaign_id})


@router.post("/{campaign_id}/videos", response_model=CampaignResponse)
async def add_video_to_campaign(campaign_id: str, request: AddVideoRequest) -> CampaignResponse:
    """Add a video to a campaign."""
    campaign = _get_campaign_or_404(campaign_id)

    if request.video_id not in campaign["video_ids"]:
        campaign["video_ids"].append(request.video_id)
        campaign["updated_at"] = datetime.now(UTC).isoformat()
        logger.info(
            "Video added to campaign",
            extra={"campaign_id": campaign_id, "video_id": request.video_id},
        )

    return CampaignResponse(**campaign)


@router.delete("/{campaign_id}/videos/{video_id}", response_model=CampaignResponse)
async def remove_video_from_campaign(campaign_id: str, video_id: str) -> CampaignResponse:
    """Remove a video from a campaign."""
    campaign = _get_campaign_or_404(campaign_id)

    if video_id in campaign["video_ids"]:
        campaign["video_ids"].remove(video_id)
        campaign["updated_at"] = datetime.now(UTC).isoformat()
        logger.info(
            "Video removed from campaign",
            extra={"campaign_id": campaign_id, "video_id": video_id},
        )

    return CampaignResponse(**campaign)


@router.post("/{campaign_id}/launch")
async def launch_campaign(campaign_id: str) -> dict[str, Any]:
    """Launch a campaign.

    Transitions campaign status to 'active' and triggers distribution
    for all associated videos.
    """
    campaign = _get_campaign_or_404(campaign_id)

    if campaign["status"] == "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign is already active",
        )

    campaign["status"] = "active"
    campaign["updated_at"] = datetime.now(UTC).isoformat()

    if campaign.get("start_date") is None:
        campaign["start_date"] = datetime.now(UTC).isoformat()

    logger.info("Campaign launched", extra={"campaign_id": campaign_id})

    return {
        "campaign_id": campaign_id,
        "status": "active",
        "video_count": len(campaign["video_ids"]),
        "launched_at": campaign["updated_at"],
    }


@router.post("/{campaign_id}/pause")
async def pause_campaign(campaign_id: str) -> dict[str, Any]:
    """Pause an active campaign."""
    campaign = _get_campaign_or_404(campaign_id)

    if campaign["status"] != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only active campaigns can be paused",
        )

    campaign["status"] = "paused"
    campaign["updated_at"] = datetime.now(UTC).isoformat()

    logger.info("Campaign paused", extra={"campaign_id": campaign_id})

    return {
        "campaign_id": campaign_id,
        "status": "paused",
        "paused_at": campaign["updated_at"],
    }


@router.get("/{campaign_id}/analytics", response_model=CampaignAnalyticsResponse)
async def get_campaign_analytics(campaign_id: str) -> CampaignAnalyticsResponse:
    """Get aggregated analytics for a campaign."""
    campaign = _get_campaign_or_404(campaign_id)

    try:
        from video_marketing.agents.analytics import AnalyticsAgent

        agent = AnalyticsAgent()
        analytics = await agent.aggregate_campaign(
            campaign_id=campaign_id,
            video_ids=campaign["video_ids"],
        )

        return CampaignAnalyticsResponse(
            campaign_id=campaign_id,
            video_count=len(campaign["video_ids"]),
            total_views=analytics.total_views,
            total_watch_time_hours=analytics.total_watch_time_hours,
            total_likes=analytics.total_likes,
            total_comments=analytics.total_comments,
            total_shares=analytics.total_shares,
            total_subscribers_gained=analytics.total_subscribers_gained,
            total_revenue=analytics.total_revenue,
            overall_engagement_rate=analytics.overall_engagement_rate,
            platform_breakdown=analytics.platform_breakdown,
        )
    except Exception as exc:
        logger.error("Campaign analytics failed", exc_info=True, extra={"campaign_id": campaign_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get campaign analytics: {exc}",
        ) from exc
