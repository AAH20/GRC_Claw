"""Monetization Plans API endpoints."""
from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plans", tags=["plans"])


class PlanCreateRequest(BaseModel):
    """Request model for creating a monetization plan."""

    creator_id: str = Field(..., description="Creator identifier")
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    strategies: list[str] = Field(default_factory=list)
    target_monthly_revenue: float = Field(default=0.0, ge=0)
    currency: str = Field(default="USD")


class PlanUpdateRequest(BaseModel):
    """Request model for updating a monetization plan."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    strategies: list[str] | None = None
    target_monthly_revenue: float | None = Field(default=None, ge=0)
    is_active: bool | None = None


class PlanResponse(BaseModel):
    """Response model for monetization plan."""

    plan_id: str
    creator_id: str
    name: str
    description: str
    strategies: list[str]
    target_monthly_revenue: float
    current_monthly_revenue: float
    currency: str
    is_active: bool
    created_at: str
    updated_at: str


class PlanListResponse(BaseModel):
    """Response model for plan list."""

    plans: list[PlanResponse]
    total: int
    page: int
    page_size: int


_plans: dict[str, dict[str, Any]] = {}


def _get_plan_or_404(plan_id: str) -> dict[str, Any]:
    """Get a plan by ID or raise 404."""
    if plan_id not in _plans:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan '{plan_id}' not found",
        )
    return _plans[plan_id]


@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(request: PlanCreateRequest) -> PlanResponse:
    """Create a new monetization plan."""
    plan_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    plan = {
        "plan_id": plan_id,
        "creator_id": request.creator_id,
        "name": request.name,
        "description": request.description,
        "strategies": request.strategies,
        "target_monthly_revenue": request.target_monthly_revenue,
        "current_monthly_revenue": 0.0,
        "currency": request.currency,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }

    _plans[plan_id] = plan
    logger.info("Plan created", extra={"plan_id": plan_id})
    return PlanResponse(**plan)


@router.get("", response_model=PlanListResponse)
async def list_plans(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    creator_id: str | None = None,
) -> PlanListResponse:
    """List monetization plans with pagination and filtering."""
    plans = list(_plans.values())

    if creator_id:
        plans = [p for p in plans if p["creator_id"] == creator_id]

    total = len(plans)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = plans[start:end]

    return PlanListResponse(
        plans=[PlanResponse(**p) for p in paginated],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(plan_id: str) -> PlanResponse:
    """Get a monetization plan by ID."""
    plan = _get_plan_or_404(plan_id)
    return PlanResponse(**plan)


@router.patch("/{plan_id}", response_model=PlanResponse)
async def update_plan(plan_id: str, request: PlanUpdateRequest) -> PlanResponse:
    """Update a monetization plan."""
    plan = _get_plan_or_404(plan_id)

    update_data = request.model_dump(exclude_unset=True)
    for field_name, value in update_data.items():
        if value is not None:
            plan[field_name] = value

    plan["updated_at"] = datetime.now(UTC).isoformat()
    logger.info("Plan updated", extra={"plan_id": plan_id})
    return PlanResponse(**plan)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(plan_id: str) -> None:
    """Delete a monetization plan."""
    _get_plan_or_404(plan_id)
    del _plans[plan_id]
    logger.info("Plan deleted", extra={"plan_id": plan_id})


@router.post("/{plan_id}/optimize")
async def optimize_plan(plan_id: str) -> dict[str, Any]:
    """Trigger revenue optimization for a plan."""
    plan = _get_plan_or_404(plan_id)

    try:
        from creator_monetization.agents.revenue_optimizer import RevenueOptimizerAgent

        agent = RevenueOptimizerAgent()
        # In production, would fetch actual streams from database
        result = await agent.analyze_revenue_streams(
            creator_id=plan["creator_id"],
            streams=[],
        )
        return {"plan_id": plan_id, "optimization": result}
    except Exception as exc:
        logger.error("Plan optimization failed", exc_info=True, extra={"plan_id": plan_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization failed: {exc}",
        ) from exc
