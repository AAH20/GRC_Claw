"""Pydantic data models for the Real Estate Marketing platform."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PropertyType(str, Enum):
    """Types of real estate properties."""

    SINGLE_FAMILY = "single_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    MULTI_FAMILY = "multi_family"
    LAND = "land"
    COMMERCIAL = "commercial"


class PropertyStatus(str, Enum):
    """Listing status of a property."""

    ACTIVE = "active"
    PENDING = "pending"
    SOLD = "sold"
    EXPIRED = "expired"
    DRAFT = "draft"


class LeadStatus(str, Enum):
    """Status of a marketing lead."""

    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    NURTURING = "nurturing"
    CONVERTED = "converted"
    LOST = "lost"


class LeadSource(str, Enum):
    """Source of a marketing lead."""

    ZILLOW = "zillow"
    REALTOR = "realtor"
    WEBSITE = "website"
    REFERRAL = "referral"
    SOCIAL_MEDIA = "social_media"
    EMAIL_CAMPAIGN = "email_campaign"
    OPEN_HOUSE = "open_house"


class Address(BaseModel):
    """Physical address model."""

    model_config = ConfigDict(frozen=True)

    street: str = Field(..., min_length=1, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=2, max_length=2)
    zip_code: str = Field(..., min_length=5, max_length=10)
    country: str = Field(default="US", min_length=2, max_length=2)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, le=180, ge=-180)


class PropertyBase(BaseModel):
    """Base property model with common fields."""

    model_config = ConfigDict(from_attributes=True)

    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=5000)
    property_type: PropertyType
    status: PropertyStatus = PropertyStatus.DRAFT
    price: float = Field(..., gt=0)
    address: Address
    bedrooms: float | None = Field(default=None, ge=0)
    bathrooms: float | None = Field(default=None, ge=0)
    square_feet: float | None = Field(default=None, gt=0)
    lot_size: float | None = Field(default=None, gt=0)
    year_built: int | None = Field(default=None, ge=1800, le=2100)
    images: list[str] = Field(default_factory=list)
    amenities: list[str] = Field(default_factory=list)
    virtual_tour_url: str | None = None
    listing_agent: str | None = None
    mls_number: str | None = None


class PropertyCreate(PropertyBase):
    """Model for creating a new property listing."""

    pass


class PropertyUpdate(BaseModel):
    """Model for updating an existing property listing."""

    model_config = ConfigDict(from_attributes=True)

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1, max_length=5000)
    status: PropertyStatus | None = None
    price: float | None = Field(default=None, gt=0)
    images: list[str] | None = None
    amenities: list[str] | None = None
    virtual_tour_url: str | None = None


class Property(PropertyBase):
    """Full property model with database fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_published: bool = False
    view_count: int = 0
    lead_count: int = 0


class PropertyListResponse(BaseModel):
    """Response model for property list endpoint."""

    items: list[Property]
    total: int
    page: int
    page_size: int
    pages: int


class LeadBase(BaseModel):
    """Base lead model with common fields."""

    model_config = ConfigDict(from_attributes=True)

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    source: LeadSource = LeadSource.WEBSITE
    status: LeadStatus = LeadStatus.NEW
    budget_min: float | None = Field(default=None, gt=0)
    budget_max: float | None = Field(default=None, gt=0)
    preferred_location: str | None = None
    notes: str | None = Field(default=None, max_length=2000)
    tags: list[str] = Field(default_factory=list)
    assigned_agent: str | None = None
    score: float = Field(default=0.0, ge=0, le=100)


class LeadCreate(LeadBase):
    """Model for creating a new lead."""

    pass


class LeadUpdate(BaseModel):
    """Model for updating an existing lead."""

    model_config = ConfigDict(from_attributes=True)

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=20)
    status: LeadStatus | None = None
    budget_min: float | None = Field(default=None, gt=0)
    budget_max: float | None = Field(default=None, gt=0)
    preferred_location: str | None = None
    notes: str | None = Field(default=None, max_length=2000)
    tags: list[str] | None = None
    assigned_agent: str | None = None
    score: float | None = Field(default=None, ge=0, le=100)


class Lead(LeadBase):
    """Full lead model with database fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_contacted_at: datetime | None = None
    converted_at: datetime | None = None
    properties_viewed: list[UUID] = Field(default_factory=list)
    emails_sent: int = 0


class LeadListResponse(BaseModel):
    """Response model for lead list endpoint."""

    items: list[Lead]
    total: int
    page: int
    page_size: int
    pages: int


class NurtureRequest(BaseModel):
    """Request model for lead nurture workflow."""

    lead_id: UUID
    sequence_type: str = Field(default="standard", pattern="^(standard|aggressive|passive)$")
    custom_message: str | None = Field(default=None, max_length=2000)


class NurtureResponse(BaseModel):
    """Response model for lead nurture workflow."""

    lead_id: UUID
    status: str
    message: str
    next_action: str | None = None
    scheduled_at: datetime | None = None


class AnalyticsEvent(BaseModel):
    """Model for analytics tracking events."""

    model_config = ConfigDict(from_attributes=True)

    event_type: str = Field(..., min_length=1, max_length=50)
    property_id: UUID | None = None
    lead_id: UUID | None = None
    source: str | None = None
    medium: str | None = None
    campaign: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ReportRequest(BaseModel):
    """Request model for report generation."""

    report_type: str = Field(..., pattern="^(performance|attribution|roi|summary)$")
    start_date: datetime
    end_date: datetime
    property_ids: list[UUID] | None = None
    format: str = Field(default="pdf", pattern="^(pdf|csv|json|html)$")


class ReportResponse(BaseModel):
    """Response model for report generation."""

    report_id: UUID = Field(default_factory=uuid4)
    status: str
    download_url: str | None = None
    message: str


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: dict[str, str] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str
    detail: str | None = None
    code: str | None = None
