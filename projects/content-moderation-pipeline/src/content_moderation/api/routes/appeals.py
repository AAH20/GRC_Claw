"""Appeal management API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from content_moderation.agents import AppealHandlerAgent
from content_moderation.models.schemas import Appeal, AppealStatus, AppealSubmission

router = APIRouter()

# In-memory appeal store (replace with database in production)
_appeals: dict[UUID, Appeal] = {}
_appeal_agent: AppealHandlerAgent | None = None


def _get_appeal_agent() -> AppealHandlerAgent:
    """Lazy-initialize the appeal handler agent."""
    global _appeal_agent
    if _appeal_agent is None:
        _appeal_agent = AppealHandlerAgent()
    return _appeal_agent


@router.post("/appeals", response_model=Appeal, status_code=status.HTTP_201_CREATED)
async def submit_appeal(submission: AppealSubmission) -> Appeal:
    """Submit a new moderation appeal.

    Args:
        submission: Appeal submission data.

    Returns:
        Created appeal.
    """
    appeal = Appeal(
        moderation_result_id=submission.moderation_result_id,
        user_id=submission.user_id,
        reason=submission.reason,
        evidence=submission.evidence,
    )
    _appeals[appeal.id] = appeal
    return appeal


@router.get("/appeals/{appeal_id}", response_model=Appeal)
async def get_appeal(appeal_id: UUID) -> Appeal:
    """Get appeal status by ID.

    Args:
        appeal_id: Appeal identifier.

    Returns:
        Appeal details.

    Raises:
        HTTPException: If appeal not found.
    """
    appeal = _appeals.get(appeal_id)
    if appeal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appeal {appeal_id} not found",
        )
    return appeal


@router.post("/appeals/{appeal_id}/review", response_model=Appeal)
async def review_appeal(appeal_id: UUID, reviewer_notes: str = "") -> Appeal:
    """Review and process an appeal.

    Args:
        appeal_id: Appeal identifier.
        reviewer_notes: Optional reviewer notes.

    Returns:
        Updated appeal with review decision.

    Raises:
        HTTPException: If appeal not found.
    """
    appeal = _appeals.get(appeal_id)
    if appeal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Appeal {appeal_id} not found",
        )

    # Use appeal handler agent to review
    context = {
        "original_result": {"action": "block", "confidence": 0.9},
        "user_id": appeal.user_id,
        "reason": appeal.reason,
        "evidence": appeal.evidence,
    }

    result = await _get_appeal_agent().moderate(appeal.reason, str(appeal_id), context)

    # Map agent action to appeal status
    action_to_status = {
        "approve": AppealStatus.APPROVED,
        "reject": AppealStatus.REJECTED,
        "escalate": AppealStatus.ESCALATED,
    }

    appeal.status = action_to_status.get(result.action.value, AppealStatus.UNDER_REVIEW)
    appeal.reviewer_notes = reviewer_notes or "; ".join(result.reasons)

    return appeal
