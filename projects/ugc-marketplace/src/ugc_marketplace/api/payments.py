"""
Payments API endpoints for UGC Marketplace.

Provides endpoints for listing payments and initiating payouts.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/payments", tags=["payments"])


# ─── Pydantic Schemas ────────────────────────────────────────────────────────

class PaymentSchema(BaseModel):
    """Schema for a single payment record."""
    id: str
    creator_id: str
    campaign_id: str
    amount: float
    currency: str
    status: str  # pending, processing, completed, failed
    payout_method: str  # bank_transfer, paypal, stripe
    created_at: str
    updated_at: Optional[str] = None
    completed_at: Optional[str] = None
    transaction_id: Optional[str] = None
    failure_reason: Optional[str] = None


class PaymentListResponse(BaseModel):
    """Paginated list of payments."""
    data: List[PaymentSchema]
    total: int
    page: int
    page_size: int
    total_pages: int


class PayoutRequest(BaseModel):
    """Request body for initiating a payout."""
    creator_id: str
    amount: float = Field(..., gt=0, description="Payout amount must be positive")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    payout_method: str = Field(..., description="One of: bank_transfer, paypal, stripe")
    destination_id: str = Field(..., description="ID of the saved payout destination")


class PayoutResponse(BaseModel):
    """Response after initiating a payout."""
    id: str
    creator_id: str
    amount: float
    currency: str
    status: str
    payout_method: str
    estimated_arrival: str
    created_at: str


# ─── Mock Data Helpers ───────────────────────────────────────────────────────

def _generate_mock_payments(page: int = 1, page_size: int = 10) -> PaymentListResponse:
    """Generate realistic mock payment data."""
    statuses = ["pending", "processing", "completed", "failed"]
    payout_methods = ["bank_transfer", "paypal", "stripe"]
    currencies = ["USD", "EUR", "GBP"]

    total = 47  # Simulate 47 total payments in the system
    total_pages = (total + page_size - 1) // page_size

    # Generate deterministic mock records for the requested page
    start_idx = (page - 1) * page_size
    data: List[PaymentSchema] = []

    for i in range(start_idx, min(start_idx + page_size, total)):
        idx = i + 1
        status = statuses[idx % len(statuses)]
        method = payout_methods[idx % len(payout_methods)]
        currency = currencies[idx % len(currencies)]
        amount = round(25.0 + (idx * 13.37), 2)

        created = datetime(2026, 9, 1, 10, 0, 0) + timedelta(days=idx, hours=idx % 12)
        updated = created + timedelta(hours=2) if status != "pending" else None
        completed = created + timedelta(days=1) if status == "completed" else None

        data.append(PaymentSchema(
            id=f"pay_{idx:06d}",
            creator_id=f"usr_creator_{idx:04d}",
            campaign_id=f"cmp_{idx:05d}",
            amount=amount,
            currency=currency,
            status=status,
            payout_method=method,
            created_at=created.isoformat(),
            updated_at=updated.isoformat() if updated else None,
            completed_at=completed.isoformat() if completed else None,
            transaction_id=f"txn_{idx:08d}" if status in ("completed", "processing") else None,
            failure_reason="Insufficient funds" if status == "failed" else None,
        ))

    return PaymentListResponse(
        data=data,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("", response_model=PaymentListResponse)
async def list_payments(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    creator_id: Optional[str] = Query(default=None, description="Filter by creator ID"),
) -> PaymentListResponse:
    """
    List payments with pagination.

    Returns a paginated list of payment records. Supports filtering by status
    and creator_id.
    """
    response = _generate_mock_payments(page=page, page_size=page_size)

    # Apply filters if provided
    if status:
        response.data = [p for p in response.data if p.status == status]
    if creator_id:
        response.data = [p for p in response.data if p.creator_id == creator_id]

    return response


@router.post("/payout", response_model=PayoutResponse, status_code=201)
async def initiate_payout(payload: PayoutRequest) -> PayoutResponse:
    """
    Initiate a payout for a creator.

    Creates a new payout request. The payout will be processed asynchronously
    and the status can be tracked via the payment ID returned.
    """
    valid_methods = {"bank_transfer", "paypal", "stripe"}
    if payload.payout_method not in valid_methods:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid payout_method. Must be one of: {', '.join(valid_methods)}",
        )

    payout_id = f"pay_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{payload.creator_id[-4:]}"
    estimated = datetime.utcnow() + timedelta(days=3)

    return PayoutResponse(
        id=payout_id,
        creator_id=payload.creator_id,
        amount=payload.amount,
        currency=payload.currency,
        status="pending",
        payout_method=payload.payout_method,
        estimated_arrival=estimated.isoformat(),
        created_at=datetime.utcnow().isoformat(),
    )
