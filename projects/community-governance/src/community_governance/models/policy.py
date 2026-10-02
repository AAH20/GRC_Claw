"""Policy models for community governance."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class PolicyStatus(StrEnum):
    """Status of a governance policy."""

    DRAFT = "draft"
    ACTIVE = "active"
    UNDER_REVIEW = "under_review"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class PolicyScope(StrEnum):
    """Scope of a governance policy."""

    GLOBAL = "global"
    COMMUNITY = "community"
    CATEGORY = "category"
    USER = "user"
    CUSTOM = "custom"


class Policy(BaseModel):
    """Governance policy model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4, description="Unique policy identifier")
    name: str = Field(..., min_length=1, max_length=200, description="Policy name")
    description: str = Field(..., min_length=1, description="Policy description")
    status: PolicyStatus = Field(default=PolicyStatus.DRAFT, description="Policy status")
    scope: PolicyScope = Field(..., description="Policy scope")
    scope_target: str | None = Field(
        default=None, description="Target of the policy scope"
    )
    rules: list[UUID] = Field(
        default_factory=list, description="IDs of associated rules"
    )
    guidelines: list[str] = Field(
        default_factory=list, description="Policy guidelines"
    )
    enforcement_level: str = Field(
        default="standard", description="Enforcement level"
    )
    effective_date: datetime | None = Field(
        default=None, description="Policy effective date"
    )
    expiration_date: datetime | None = Field(
        default=None, description="Policy expiration date"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional policy metadata"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    created_by: str | None = Field(default=None, description="Creator identifier")
    version: int = Field(default=1, ge=1, description="Policy version")


class PolicyCreate(BaseModel):
    """Model for creating a new policy."""

    name: str = Field(..., min_length=1, max_length=200, description="Policy name")
    description: str = Field(..., min_length=1, description="Policy description")
    scope: PolicyScope = Field(..., description="Policy scope")
    scope_target: str | None = Field(
        default=None, description="Target of the policy scope"
    )
    rules: list[UUID] = Field(
        default_factory=list, description="IDs of associated rules"
    )
    guidelines: list[str] = Field(
        default_factory=list, description="Policy guidelines"
    )
    enforcement_level: str = Field(
        default="standard", description="Enforcement level"
    )
    effective_date: datetime | None = Field(
        default=None, description="Policy effective date"
    )
    expiration_date: datetime | None = Field(
        default=None, description="Policy expiration date"
    )
    created_by: str | None = Field(default=None, description="Creator identifier")


class PolicyUpdate(BaseModel):
    """Model for updating an existing policy."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1)
    status: PolicyStatus | None = None
    scope: PolicyScope | None = None
    scope_target: str | None = None
    rules: list[UUID] | None = None
    guidelines: list[str] | None = None
    enforcement_level: str | None = None
    effective_date: datetime | None = None
    expiration_date: datetime | None = None
