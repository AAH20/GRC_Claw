"""
Transactions API endpoints for UGC Marketplace.

Provides:
  GET  /transactions  — list with pagination, filtering by status/date
  POST /transactions  — create with validation
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/transactions", tags=["transactions"])


# ─── Mock Data Store ────────────────────────────────────────────────────────

MOCK_TRANSACTIONS = [
    {
        "id": "txn_001",
        "order_id": "ord_1001",
        "buyer_id": "usr_501",
        "seller_id": "usr_701",
        "amount": 49.99,
        "currency": "USD",
        "status": "completed",
        "payment_method": "stripe",
        "created_at": "2026-09-15T10:30:00Z",
        "updated_at": "2026-09-15T10:30:05Z",
    },
    {
        "id": "txn_002",
        "order_id": "ord_1002",
        "buyer_id": "usr_502",
        "seller_id": "usr_702",
        "amount": 129.50,
        "currency": "USD",
        "status": "pending",
        "payment_method": "paypal",
        "created_at": "2026-09-20T14:15:00Z",
        "updated_at": "2026-09-20T14:15:00Z",
    },
    {
        "id": "txn_003",
        "order_id": "ord_1003",
        "buyer_id": "usr_503",
        "seller_id": "usr_703",
        "amount": 250.00,
        "currency": "USD",
        "status": "completed",
        "payment_method": "stripe",
        "created_at": "2026-09-25T09:00:00Z",
        "updated_at": "2026-09-25T09:00:03Z",
    },
    {
        "id": "txn_004",
        "order_id": "ord_1004",
        "buyer_id": "usr_504",
        "seller_id": "usr_704",
        "amount": 75.25,
        "currency": "USD",
        "status": "failed",
        "payment_method": "stripe",
        "created_at": "2026-09-28T16:45:00Z",
        "updated_at": "2026-09-28T16:45:10Z",
    },
    {
        "id": "txn_005",
        "order_id": "ord_1005",
        "buyer_id": "usr_505",
        "seller_id": "usr_705",
        "amount": 310.00,
        "currency": "USD",
        "status": "refunded",
        "payment_method": "paypal",
        "created_at": "2026-10-01T11:20:00Z",
        "updated_at": "2026-10-02T08:00:00Z",
    },
    {
        "id": "txn_006",
        "order_id": "ord_1006",
        "buyer_id": "usr_506",
        "seller_id": "usr_706",
        "amount": 89.99,
        "currency": "USD",
        "status": "completed",
        "payment_method": "stripe",
        "created_at": "2026-10-02T13:00:00Z",
        "updated_at": "2026-10-02T13:00:02Z",
    },
    {
        "id": "txn_007",
        "order_id": "ord_1007",
        "buyer_id": "usr_507",
        "seller_id": "usr_707",
        "amount": 199.00,
        "currency": "USD",
        "status": "pending",
        "payment_method": "paypal",
        "created_at": "2026-10-03T07:30:00Z",
        "updated_at": "2026-10-03T07:30:00Z",
    },
    {
        "id": "txn_008",
        "order_id": "ord_1008",
        "buyer_id": "usr_508",
        "seller_id": "usr_708",
        "amount": 59.99,
        "currency": "USD",
        "status": "completed",
        "payment_method": "stripe",
        "created_at": "2026-09-10T12:00:00Z",
        "updated_at": "2026-09-10T12:00:04Z",
    },
    {
        "id": "txn_009",
        "order_id": "ord_1009",
        "buyer_id": "usr_509",
        "seller_id": "usr_709",
        "amount": 450.00,
        "currency": "USD",
        "status": "completed",
        "payment_method": "stripe",
        "created_at": "2026-09-05T18:00:00Z",
        "updated_at": "2026-09-05T18:00:06Z",
    },
    {
        "id": "txn_010",
        "order_id": "ord_1010",
        "buyer_id": "usr_510",
        "seller_id": "usr_710",
        "amount": 35.00,
        "currency": "USD",
        "status": "failed",
        "payment_method": "paypal",
        "created_at": "2026-09-01T20:00:00Z",
        "updated_at": "2026-09-01T20:00:08Z",
    },
]


# ─── Pydantic Schemas ────────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    order_id: str = Field(..., min_length=1, description="Associated order ID")
    buyer_id: str = Field(..., min_length=1, description="Buyer user ID")
    seller_id: str = Field(..., min_length=1, description="Seller user ID")
    amount: float = Field(..., gt=0, description="Transaction amount (must be positive)")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="ISO 4217 currency code")
    payment_method: str = Field(..., description="Payment method (stripe, paypal, etc.)")

    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "ord_1011",
                "buyer_id": "usr_511",
                "seller_id": "usr_711",
                "amount": 149.99,
                "currency": "USD",
                "payment_method": "stripe",
            }
        }


class TransactionResponse(BaseModel):
    id: str
    order_id: str
    buyer_id: str
    seller_id: str
    amount: float
    currency: str
    status: str
    payment_method: str
    created_at: str
    updated_at: str


class TransactionListResponse(BaseModel):
    data: list[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("/", response_model=TransactionListResponse)
async def list_transactions(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(
        default=None,
        description="Filter by status",
        pattern="^(completed|pending|failed|refunded)$",
    ),
    start_date: Optional[str] = Query(
        default=None,
        description="Filter transactions created on or after this date (ISO 8601)",
    ),
    end_date: Optional[str] = Query(
        default=None,
        description="Filter transactions created on or before this date (ISO 8601)",
    ),
):
    """
    List transactions with pagination and optional filtering by status and date range.
    """
    filtered = MOCK_TRANSACTIONS.copy()

    # Filter by status
    if status:
        filtered = [t for t in filtered if t["status"] == status]

    # Filter by date range
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            filtered = [
                t for t in filtered
                if datetime.fromisoformat(t["created_at"].replace("Z", "+00:00")) >= start_dt
            ]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO 8601.")

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            filtered = [
                t for t in filtered
                if datetime.fromisoformat(t["created_at"].replace("Z", "+00:00")) <= end_dt
            ]
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO 8601.")

    # Pagination
    total = len(filtered)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated = filtered[start_idx:end_idx]

    return TransactionListResponse(
        data=paginated,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("/", response_model=TransactionResponse, status_code=201)
async def create_transaction(payload: TransactionCreate):
    """
    Create a new transaction with validation.
    """
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    new_id = f"txn_{len(MOCK_TRANSACTIONS) + 1:03d}"

    transaction = {
        "id": new_id,
        "order_id": payload.order_id,
        "buyer_id": payload.buyer_id,
        "seller_id": payload.seller_id,
        "amount": payload.amount,
        "currency": payload.currency.upper(),
        "status": "pending",
        "payment_method": payload.payment_method,
        "created_at": now,
        "updated_at": now,
    }

    MOCK_TRANSACTIONS.append(transaction)

    return TransactionResponse(**transaction)
