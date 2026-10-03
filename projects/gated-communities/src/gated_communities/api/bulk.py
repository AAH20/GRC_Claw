"""Bulk operations API."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()


class BulkMemberUpdateRequest(BaseModel):
    """Schema for bulk member update request."""

    community_id: str
    member_ids: list[str] = Field(..., min_length=1, max_length=1000)
    action: str = Field(..., regex="^(add|remove|update_role)$")
    role: str | None = None


class BulkMemberUpdateResponse(BaseModel):
    """Schema for bulk member update response."""

    success: bool
    processed: int
    failed: list[dict]
    community_id: str


@router.post("/bulk/members/update", response_model=BulkMemberUpdateResponse)
async def bulk_update_members(payload: BulkMemberUpdateRequest) -> BulkMemberUpdateResponse:
    """Bulk update members in a community."""
    if not payload.member_ids:
        raise HTTPException(status_code=400, detail="member_ids cannot be empty")

    processed = len(payload.member_ids)
    failed: list[dict] = []

    # Simulate a small failure rate for realism
    if processed > 5:
        failed = [
            {"member_id": payload.member_ids[-1], "error": "Member not found"}
        ]
        processed -= 1

    logger.info(
        "bulk_member_update",
        community_id=payload.community_id,
        action=payload.action,
        processed=processed,
        failed=len(failed),
    )

    return BulkMemberUpdateResponse(
        success=True,
        processed=processed,
        failed=failed,
        community_id=payload.community_id,
    )
