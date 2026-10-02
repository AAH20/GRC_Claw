"""Budget API routes — Budget allocation and management."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

router = APIRouter()


# ─── Request/Response Models ────────────────────────────────────────


class BudgetAllocationRequest(BaseModel):
    """Request model for updating budget allocation."""

    campaign_id: str = Field(..., min_length=1)
    platform_allocations: dict[str, float] = Field(
        ..., description="Platform to budget amount mapping"
    )
    daily_budget: float | None = Field(None, gt=0)
    strategy: str | None = Field(None, description="Budget strategy (even, performance, etc.)")


class BudgetAllocationResponse(BaseModel):
    """Response model for budget allocation."""

    campaign_id: str
    total_budget: float
    platform_allocations: dict[str, float]
    daily_budget: float
    strategy: str
    updated_at: str


class BudgetStatusResponse(BaseModel):
    """Response model for budget status."""

    campaign_id: str
    total_budget: float
    spent_to_date: float
    remaining_budget: float
    spend_rate: float
    projected_spend: float
    on_track: bool


# ─── In-Memory Store (replace with database in production) ──────────

_budgets: dict[str, dict[str, Any]] = {}


# ─── Routes ─────────────────────────────────────────────────────────


@router.get("/{campaign_id}", response_model=BudgetAllocationResponse)
async def get_budget_allocation(campaign_id: str) -> BudgetAllocationResponse:
    """Get the budget allocation for a campaign.

    Args:
        campaign_id: The campaign identifier.

    Returns:
        Current budget allocation.

    Raises:
        HTTPException: If budget is not found.
    """
    budget = _budgets.get(campaign_id)
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget for campaign {campaign_id} not found",
        )
    return BudgetAllocationResponse(**budget)


@router.put("/{campaign_id}", response_model=BudgetAllocationResponse)
async def update_budget_allocation(
    campaign_id: str, request: BudgetAllocationRequest
) -> BudgetAllocationResponse:
    """Update the budget allocation for a campaign.

    Args:
        campaign_id: The campaign identifier.
        request: New budget allocation parameters.

    Returns:
        Updated budget allocation.

    Raises:
        HTTPException: If allocation is invalid.
    """
    total = sum(request.platform_allocations.values())
    if total <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Total budget allocation must be positive",
        )

    now = datetime.now(UTC).isoformat()
    budget: dict[str, Any] = {
        "campaign_id": campaign_id,
        "total_budget": total,
        "platform_allocations": request.platform_allocations,
        "daily_budget": request.daily_budget or (total / 30),
        "strategy": request.strategy or "performance",
        "updated_at": now,
    }

    _budgets[campaign_id] = budget
    logger.info("Budget updated", campaign_id=campaign_id, total=total)

    return BudgetAllocationResponse(**budget)


@router.get("/{campaign_id}/status", response_model=BudgetStatusResponse)
async def get_budget_status(campaign_id: str) -> BudgetStatusResponse:
    """Get the current budget status for a campaign.

    Args:
        campaign_id: The campaign identifier.

    Returns:
        Current budget status with spend tracking.

    Raises:
        HTTPException: If budget is not found.
    """
    budget = _budgets.get(campaign_id)
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget for campaign {campaign_id} not found",
        )

    # In production, this would query actual spend data from ad platforms
    spent = budget.get("spent_to_date", 0.0)
    total = budget["total_budget"]
    remaining = total - spent
    spend_rate = spent / total if total > 0 else 0.0

    return BudgetStatusResponse(
        campaign_id=campaign_id,
        total_budget=total,
        spent_to_date=spent,
        remaining_budget=remaining,
        spend_rate=round(spend_rate, 4),
        projected_spend=total,
        on_track=spend_rate < 0.8,
    )


@router.post("/{campaign_id}/reallocate", response_model=BudgetAllocationResponse)
async def reallocate_budget(
    campaign_id: str, request: BudgetAllocationRequest,
) -> BudgetAllocationResponse:
    """Reallocate budget across platforms based on performance.

    Args:
        campaign_id: The campaign identifier.
        request: New allocation parameters.

    Returns:
        Updated budget allocation.
    """
    return await update_budget_allocation(campaign_id, request)
