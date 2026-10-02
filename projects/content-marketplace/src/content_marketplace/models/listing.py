"""Listing models for content marketplace."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ListingStatus(str, Enum):
    """Status of a listing."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    ACTIVE = "active"
    SOLD = "sold"
    ARCHIVED = "archived"
    SUSPENDED = "suspended"


class ListingCreate(BaseModel):
    """Schema for creating a new listing."""

    title: str = Field(..., min_length=1, max_length=200, description="Listing title")
    description: str = Field(..., min_length=1, max_length=5000, description="Listing description")
    seller_id: str = Field(..., min_length=1, description="Seller identifier")
    category: str = Field(..., min_length=1, description="Content category")
    tags: list[str] = Field(default_factory=list, description="Content tags")
    base_price: float = Field(..., gt=0, description="Base price in the default currency")
    currency: str = Field(default="USD", min_length=3, max_length=3, description="ISO 4217 currency code")
    content_url: str | None = Field(default=None, description="URL to the content")
    metadata: dict[str, str] = Field(default_factory=dict, description="Additional metadata")


class ListingUpdate(BaseModel):
    """Schema for updating an existing listing."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=5000)
    category: str | None = Field(default=None, min_length=1)
    tags: list[str] | None = None
    base_price: float | None = Field(default=None, gt=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    content_url: str | None = None
    metadata: dict[str, str] | None = None
    status: ListingStatus | None = None


class Listing(BaseModel):
    """Full listing model with all fields."""

    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str
    seller_id: str
    category: str
    tags: list[str] = Field(default_factory=list)
    base_price: float
    currency: str = "USD"
    content_url: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    status: ListingStatus = ListingStatus.DRAFT
    view_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True
