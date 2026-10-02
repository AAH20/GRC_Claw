"""Transaction models for content marketplace."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TransactionStatus(str, Enum):
    """Status of a transaction."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    DISPUTED = "disputed"


class TransactionCreate(BaseModel):
    """Schema for creating a new transaction."""

    listing_id: UUID = Field(..., description="Associated listing ID")
    buyer_id: str = Field(..., min_length=1, description="Buyer identifier")
    seller_id: str = Field(..., min_length=1, description="Seller identifier")
    amount: float = Field(..., gt=0, description="Transaction amount")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    payment_method: str = Field(..., min_length=1, description="Payment method identifier")
    metadata: dict[str, str] = Field(default_factory=dict)


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction."""

    status: Optional[TransactionStatus] = None
    payment_method: Optional[str] = None
    metadata: Optional[dict[str, str]] = None


class Transaction(BaseModel):
    """Full transaction model with all fields."""

    id: UUID = Field(default_factory=uuid4)
    listing_id: UUID
    buyer_id: str
    seller_id: str
    amount: float
    currency: str = "USD"
    payment_method: str
    status: TransactionStatus = TransactionStatus.PENDING
    platform_fee: float = Field(default=0.0, ge=0, description="Platform fee deducted from seller payout")
    net_amount: float = Field(default=0.0, ge=0, description="Net amount after fees")
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
