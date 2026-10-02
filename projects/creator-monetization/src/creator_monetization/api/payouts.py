"""Payouts API endpoints."""
from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from creator_monetization.models.schemas import Payout, PayoutCreate, PayoutStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payouts", tags=["payouts"])


class PayoutResponse(BaseModel):
    """Response model for payout."""

    payout_id: str
    creator_id: str
    amount: str
    currency: str
    status: str
    period_start: str
    period_end: str
    payment_method: str
    created_at: str
    paid_at: str | None = None


class PayoutListResponse(BaseModel):
    """Response model for payout list."""

    payouts: list[PayoutResponse]
    total: int
    page: int
    page_size: int


class BatchProcessRequest(BaseModel):
    """Request model for batch payout processing."""

    payout_ids: list[str] = Field(..., min_length=1)


_payouts: dict[str, dict[str, Any]] = {}


def _get_payout_or_404(payout_id: str) -> dict[str, Any]:
    """Get a payout by ID or raise 404."""
    if payout_id not in _payouts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payout '{payout_id}' not found",
        )
    return _payouts[payout_id]


@router.post("", response_model=PayoutResponse, status_code=status.HTTP_201_CREATED)
async def create_payout(request: PayoutCreateRequest) -> PayoutResponse:
    """Create a new payout."""
    payout_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    payout = {
        "payout_id": payout_id,
        "creator_id": request.creator_id,
        "amount": str(request.amount),
        "currency": request.currency,
        "status": PayoutStatus.PENDING.value,
        "period_start": request.period_start.isoformat(),
        "period_end": request.period_end.isoformat(),
        "payment_method": request.payment_method,
        "created_at": now,
        "paid_at": None,
    }

    _payouts[payout_id] = payout
    logger.info("Payout created", extra={"payout_id": payout_id})
    return PayoutResponse(**payout)


@router.get("", response_model=PayoutListResponse)
async def list_payouts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    creator_id: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
) -> PayoutListResponse:
    """List payouts with pagination and filtering."""
    payouts = list(_payouts.values())

    if creator_id:
        payouts = [p for p in payouts if p["creator_id"] == creator_id]
    if status_filter:
        payouts = [p for p in payouts if p["status"] == status_filter]

    total = len(payouts)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = payouts[start:end]

    return PayoutListResponse(
        payouts=[PayoutResponse(**p) for p in paginated],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{payout_id}", response_model=PayoutResponse)
async def get_payout(payout_id: str) -> PayoutResponse:
    """Get a payout by ID."""
    payout = _get_payout_or_404(payout_id)
    return PayoutResponse(**payout)


@router.post("/{payout_id}/process", response_model=PayoutResponse)
async def process_payout(payout_id: str) -> PayoutResponse:
    """Process a pending payout."""
    payout = _get_payout_or_404(payout_id)

    if payout["status"] != PayoutStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payout is not pending (status: {payout['status']})",
        )

    payout["status"] = PayoutStatus.COMPLETED.value
    payout["paid_at"] = datetime.now(UTC).isoformat()
    logger.info("Payout processed", extra={"payout_id": payout_id})
    return PayoutResponse(**payout)


@router.post("/{payout_id}/fail", response_model=PayoutResponse)
async def fail_payout(payout_id: str, reason: str = "Processing failed") -> PayoutResponse:
    """Mark a payout as failed."""
    payout = _get_payout_or_404(payout_id)
    payout["status"] = PayoutStatus.FAILED.value
    payout["failure_reason"] = reason
    logger.warning("Payout failed", extra={"payout_id": payout_id, "reason": reason})
    return PayoutResponse(**payout)


@router.post("/batch-process")
async def batch_process_payouts(request: BatchProcessRequest) -> dict[str, Any]:
    """Process multiple payouts in batch."""
    results: dict[str, Any] = {
        "total": len(request.payout_ids),
        "successful": 0,
        "failed": 0,
        "errors": [],
    }

    for payout_id in request.payout_ids:
        try:
            payout = _get_payout_or_404(payout_id)
            if payout["status"] == PayoutStatus.PENDING.value:
                payout["status"] = PayoutStatus.COMPLETED.value
                payout["paid_at"] = datetime.now(UTC).isoformat()
                results["successful"] += 1
            else:
                results["failed"] += 1
                results["errors"].append(
                    {"payout_id": payout_id, "error": "Not in pending status"}
                )
        except HTTPException as exc:
            results["failed"] += 1
            results["errors"].append({"payout_id": payout_id, "error": exc.detail})

    logger.info(
        "Batch processing complete",
        extra={
            "total": results["total"],
            "successful": results["successful"],
            "failed": results["failed"],
        },
    )
    return results


@router.get("/creator/{creator_id}/balance")
async def get_creator_balance(creator_id: str) -> dict[str, Any]:
    """Get payout balance for a creator."""
    creator_payouts = [
        p for p in _payouts.values() if p["creator_id"] == creator_id
    ]
    total_paid = sum(
        Decimal(p["amount"]) for p in creator_payouts
        if p["status"] == PayoutStatus.COMPLETED.value
    )
    total_pending = sum(
        Decimal(p["amount"]) for p in creator_payouts
        if p["status"] == PayoutStatus.PENDING.value
    )

    return {
        "creator_id": creator_id,
        "total_paid": str(total_paid),
        "total_pending": str(total_pending),
        "payout_count": len(creator_payouts),
    }