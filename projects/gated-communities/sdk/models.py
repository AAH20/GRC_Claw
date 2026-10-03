"""Pydantic models for Gated Communities API request and response payloads.

All models use Pydantic v2 and include comprehensive validation,
serialization, and documentation.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

if TYPE_CHECKING:
    from datetime import datetime

T = TypeVar("T")


# ─── Enums ────────────────────────────────────────────────────────────────────


class CommunityVisibility(str, Enum):
    """Visibility level for a community."""

    PUBLIC = "public"
    PRIVATE = "private"
    HIDDEN = "hidden"


class MemberRole(str, Enum):
    """Role of a member within a community."""

    OWNER = "owner"
    ADMIN = "admin"
    MODERATOR = "moderator"
    MEMBER = "member"


class MemberStatus(str, Enum):
    """Status of a membership."""

    ACTIVE = "active"
    PENDING = "pending"
    SUSPENDED = "suspended"
    BANNED = "banned"


# ─── Base Models ───────────────────────────────────────────────────────────────


class BaseSchema(BaseModel):
    """Base model with common configuration for all schemas."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
        validate_assignment=True,
    )


class TimestampedSchema(BaseSchema):
    """Mixin adding created/updated timestamps."""

    created_at: datetime = Field(..., description="ISO 8601 creation timestamp")
    updated_at: datetime = Field(..., description="ISO 8601 last-update timestamp")


# ─── User ─────────────────────────────────────────────────────────────────────


class User(BaseSchema):
    """A user in the Gated Communities platform."""

    id: str = Field(..., description="Unique user identifier")
    username: str = Field(
        ..., min_length=1, max_length=50, description="Display username"
    )
    email: str = Field(..., description="User email address")
    display_name: str | None = Field(
        None, max_length=100, description="Optional display name"
    )
    avatar_url: str | None = Field(None, description="URL to user avatar image")
    is_active: bool = Field(True, description="Whether the user account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")


# ─── Community ─────────────────────────────────────────────────────────────────


class Community(TimestampedSchema):
    """A gated community."""

    id: str = Field(..., description="Unique community identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Community name")
    slug: str = Field(
        ..., min_length=1, max_length=100, description="URL-friendly slug"
    )
    description: str | None = Field(
        None, max_length=5000, description="Community description"
    )
    visibility: CommunityVisibility = Field(
        default=CommunityVisibility.PRIVATE,
        description="Community visibility level",
    )
    owner_id: str = Field(..., description="ID of the community owner")
    member_count: int = Field(default=0, ge=0, description="Number of members")
    tags: list[str] = Field(default_factory=list, description="Community tags")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary metadata key-value pairs"
    )


class CommunityCreate(BaseSchema):
    """Payload for creating a new community."""

    name: str = Field(..., min_length=1, max_length=100, description="Community name")
    slug: str = Field(
        ..., min_length=1, max_length=100, description="URL-friendly slug"
    )
    description: str | None = Field(
        None, max_length=5000, description="Community description"
    )
    visibility: CommunityVisibility = Field(
        default=CommunityVisibility.PRIVATE,
        description="Community visibility level",
    )
    tags: list[str] = Field(default_factory=list, description="Community tags")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary metadata key-value pairs"
    )

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Ensure slug contains only lowercase alphanumeric chars and hyphens."""
        import re

        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", v):
            raise ValueError(
                "Slug must contain only lowercase letters, numbers, and hyphens, "
                "and must not start or end with a hyphen."
            )
        return v


class CommunityUpdate(BaseSchema):
    """Payload for updating an existing community (all fields optional)."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=5000)
    visibility: CommunityVisibility | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None


# ─── Member ────────────────────────────────────────────────────────────────────


class Member(BaseSchema, TimestampedSchema):
    """A member of a community."""

    id: str = Field(..., description="Unique membership identifier")
    community_id: str = Field(..., description="ID of the community")
    user_id: str = Field(..., description="ID of the user")
    role: MemberRole = Field(default=MemberRole.MEMBER, description="Member role")
    status: MemberStatus = Field(
        default=MemberStatus.ACTIVE, description="Membership status"
    )
    joined_at: datetime = Field(..., description="When the user joined the community")
    user: User | None = Field(None, description="Embedded user object, if requested")


class MemberCreate(BaseSchema):
    """Payload for adding a member to a community."""

    user_id: str = Field(..., description="ID of the user to add")
    role: MemberRole = Field(default=MemberRole.MEMBER, description="Role to assign")


class MemberUpdate(BaseSchema):
    """Payload for updating a membership (all fields optional)."""

    role: MemberRole | None = None
    status: MemberStatus | None = None


# ─── Pagination ────────────────────────────────────────────────────────────────


class PaginatedResponse(BaseSchema, Generic[T]):
    """Generic paginated response wrapper."""

    data: list[T] = Field(..., description="List of result items")
    total: int = Field(..., ge=0, description="Total number of items across all pages")
    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    per_page: int = Field(..., ge=1, le=100, description="Items per page")
    has_more: bool = Field(..., description="Whether more pages are available")

    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        if self.per_page == 0:
            return 0
        return (self.total + self.per_page - 1) // self.per_page


# ─── API Key ──────────────────────────────────────────────────────────────────


class ApiKey(BaseSchema, TimestampedSchema):
    """An API key for programmatic access."""

    id: str = Field(..., description="Unique API key identifier")
    name: str = Field(
        ..., min_length=1, max_length=100, description="Human-readable key name"
    )
    prefix: str = Field(
        ..., description="Key prefix (first 8 chars, for identification)"
    )
    last_used_at: datetime | None = Field(None, description="Last usage timestamp")
    expires_at: datetime | None = Field(None, description="Expiration timestamp")
    is_active: bool = Field(True, description="Whether the key is active")
    scopes: list[str] = Field(default_factory=list, description="Granted OAuth scopes")
