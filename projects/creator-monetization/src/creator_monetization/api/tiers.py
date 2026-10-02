"""Tiers API endpoints."""
from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from creator_monetization.models.schemas import Tier, TierCreate, TierLevel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tiers", tags=["tiers"])


class TierResponse(BaseModel):
    """Response model for tier."""

    tier_id: str
    name: str
    level: str
    monthly_price: str
    yearly_price: str
    benefits: list[str]
    min_subscribers: int
    max_subscribers: int | None
    revenue_share: str
    is_active: bool
    created_at: str
    updated_at: str


class TierListResponse(BaseModel):
    """Response model for tier list."""

    tiers: list[TierResponse]
    total: int
    page: int
    page_size: int


class TierRecommendationRequest(BaseModel):
    """Request model for tier recommendation."""

    creator_id: str = Field(..., description="Creator identifier")
    subscriber_count: int = Field(..., ge=0)
    monthly_revenue: float = Field(..., ge=0)
    content_category: str = Field(default="")
    engagement_rate: float = Field(default=0.0, ge=0, le=1)


class TierRecommendationResponse(BaseModel):
    """Response model for tier recommendation."""

    recommendation_id: str
    recommended_tier: str
    confidence: float
    reasoning: str
    suggested_price: str
    expected_conversion_rate: float


_tiers: dict[str, dict[str, Any]] = {}


def _get_tier_or_404(tier_id: str) -> dict[str, Any]:
    """Get a tier by ID or raise 404."""
    if tier_id not in _tiers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tier '{tier_id}' not found",
        )
    return _tiers[tier_id]


@router.post("", response_model=TierResponse, status_code=status.HTTP_201_CREATED)
async def create_tier(request: TierCreate) -> TierResponse:
    """Create a new tier."""
    tier_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    tier = {
        "tier_id": tier_id,
        "name": request.name,
        "level": request.level.value,
        "monthly_price": str(request.monthly_price),
        "yearly_price": str(request.yearly_price),
        "benefits": request.benefits,
        "min_subscribers": request.min_subscribers,
        "max_subscribers": request.max_subscribers,
        "revenue_share": str(request.revenue_share),
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }

    _tiers[tier_id] = tier
    logger.info("Tier created", extra={"tier_id": tier_id})
    return TierResponse(**tier)


@router.get("", response_model=TierListResponse)
async def list_tiers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    level: str | None = None,
) -> TierListResponse:
    """List tiers with pagination and filtering."""
    tiers = list(_tiers.values())

    if level:
        tiers = [t for t in tiers if t["level"] == level]

    total = len(tiers)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = tiers[start:end]

    return TierListResponse(
        tiers=[TierResponse(**t) for t in paginated],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{tier_id}", response_model=TierResponse)
async def get_tier(tier_id: str) -> TierResponse:
    """Get a tier by ID."""
    tier = _get_tier_or_404(tier_id)
    return TierResponse(**tier)


@router.patch("/{tier_id}", response_model=TierResponse)
async def update_tier(tier_id: str, request: TierCreate) -> TierResponse:
    """Update a tier."""
    tier = _get_tier_or_404(tier_id)

    tier["name"] = request.name
    tier["level"] = request.level.value
    tier["monthly_price"] = str(request.monthly_price)
    tier["yearly_price"] = str(request.yearly_price)
    tier["benefits"] = request.benefits
    tier["min_subscribers"] = request.min_subscribers
    tier["max_subscribers"] = request.max_subscribers
    tier["revenue_share"] = str(request.revenue_share)
    tier["updated_at"] = datetime.now(UTC).isoformat()

    logger.info("Tier updated", extra={"tier_id": tier_id})
    return TierResponse(**tier)


@router.delete("/{tier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tier(tier_id: str) -> None:
    """Delete a tier."""
    _get_tier_or_404(tier_id)
    del _tiers[tier_id]
    logger.info("Tier deleted", extra={"tier_id": tier_id})


@router.post("/recommend", response_model=TierRecommendationResponse)
async def recommend_tier(
    request: TierRecommendationRequest,
) -> TierRecommendationResponse:
    """Get a tier recommendation for a creator."""
    try:
        from creator_monetization.agents.tier_recommender import (
            CreatorProfile,
            TierRecommenderAgent,
        )

        agent = TierRecommenderAgent()
        profile = CreatorProfile(
            creator_id=request.creator_id,
            subscriber_count=request.subscriber_count,
            monthly_revenue=Decimal(str(request.monthly_revenue)),
            content_category=request.content_category,
            engagement_rate=request.engagement_rate,
        )
        recommendation = await agent.recommend_tier(profile)

        return TierRecommendationResponse(
            recommendation_id=recommendation.recommendation_id,
            recommended_tier=recommendation.recommended_tier.value,
            confidence=recommendation.confidence,
            reasoning=recommendation.reasoning,
            suggested_price=str(recommendation.suggested_price),
            expected_conversion_rate=recommendation.expected_conversion_rate,
        )
    except Exception as exc:
        logger.error("Tier recommendation failed", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation failed: {exc}",
        ) from exc


@router.post("/compare")
async def compare_tiers(tier_ids: list[str]) -> dict[str, Any]:
    """Compare multiple tiers."""
    tiers = []
    for tier_id in tier_ids:
        if tier_id in _tiers:
            tiers.append(_tiers[tier_id])

    if not tiers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No valid tiers found",
        )

    comparisons = []
    for tier in tiers:
        benefit_score = len(tier["benefits"]) * 10
        price_score = 100 - float(tier["monthly_price"]) * 2
        value_score = benefit_score + max(0, price_score)

        comparisons.append(
            {
                "tier_id": tier["tier_id"],
                "name": tier["name"],
                "level": tier["level"],
                "monthly_price": tier["monthly_price"],
                "benefit_count": len(tier["benefits"]),
                "value_score": round(value_score, 2),
            }
        )

    comparisons.sort(key=lambda x: x["value_score"], reverse=True)

    return {
        "tier_count": len(tiers),
        "rankings": comparisons,
        "best_value": comparisons[0]["tier_id"] if comparisons else None,
    }