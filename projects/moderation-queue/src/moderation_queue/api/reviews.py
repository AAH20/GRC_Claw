"""Review API routes for human review decisions."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field

from moderation_queue.api.dependencies import get_logger
from moderation_queue.models import ModerationStatus, ReviewDecision

router = APIRouter(prefix="/reviews", tags=["reviews"])


class SubmitReviewRequest(BaseModel):
    """Request model for submitting a review decision."""

    item_id: UUID = Field(..., description="Item being reviewed")
    reviewer_id: str = Field(..., description="Reviewer ID")
    decision: str = Field(..., description="Decision: approve, reject, escalate, request_info")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Reviewer confidence")
    notes: str = Field(default="", description="Review notes")
    categories: list[str] = Field(default_factory=list, description="Violation categories")


class ReviewResponse(BaseModel):
    """Response model for review submission."""

    success: bool = Field(..., description="Whether review was recorded")
    item_id: UUID = Field(..., description="Item ID")
    new_status: ModerationStatus = Field(..., description="New item status")


@router.post(
    "",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a review decision",
    description="Submit a human reviewer's decision on a moderation item",
)
async def submit_review(
    request: SubmitReviewRequest,
    logger=Depends(get_logger),
) -> ReviewResponse:
    """Submit a human review decision.

    Args:
        request: Review submission request.
        logger: Request logger.

    Returns:
        ReviewResponse: Review result.
    """
    # Map decision to status
    status_map = {
        "approve": ModerationStatus.APPROVED,
        "reject": ModerationStatus.REJECTED,
        "escalate": ModerationStatus.ESCALATED,
        "request_info": ModerationStatus.IN_REVIEW,
    }

    new_status = status_map.get(request.decision, ModerationStatus.IN_REVIEW)

    logger.info(
        "Review submitted",
        item_id=str(request.item_id),
        reviewer_id=request.reviewer_id,
        decision=request.decision,
    )

    return ReviewResponse(
        success=True,
        item_id=request.item_id,
        new_status=new_status,
    )


@router.get(
    "/pending",
    summary="List pending reviews",
    description="Get items awaiting human review",
)
async def list_pending_reviews(
    reviewer_id: str | None = None,
    logger=Depends(get_logger),
) -> dict:
    """List items pending human review.

    Args:
        reviewer_id: Optional reviewer filter.
        logger: Request logger.

    Returns:
        dict: Pending reviews list.
    """
    # Placeholder - would query database in production
    return {"items": [], "total": 0}
