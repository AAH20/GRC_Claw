"""Rule models for community governance."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class RuleCategory(StrEnum):
    """Categories of governance rules."""

    CONTENT_MODERATION = "content_moderation"
    USER_CONDUCT = "user_conduct"
    PRIVACY = "privacy"
    SECURITY = "security"
    ACCESS_CONTROL = "access_control"
    COMPLIANCE = "compliance"
    CUSTOM = "custom"


class RuleSeverity(StrEnum):
    """Severity levels for rule violations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Rule(BaseModel):
    """Governance rule model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4, description="Unique rule identifier")
    name: str = Field(..., min_length=1, max_length=200, description="Rule name")
    description: str = Field(..., min_length=1, description="Rule description")
    category: RuleCategory = Field(..., description="Rule category")
    severity: RuleSeverity = Field(default=RuleSeverity.MEDIUM, description="Rule severity")
    conditions: dict[str, Any] = Field(
        default_factory=dict, description="Rule conditions for evaluation"
    )
    actions: list[str] = Field(
        default_factory=list, description="Actions to take on violation"
    )
    is_active: bool = Field(default=True, description="Whether the rule is active")
    priority: int = Field(default=0, ge=0, le=100, description="Rule priority (0-100)")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    created_by: str | None = Field(default=None, description="Creator identifier")
    version: int = Field(default=1, ge=1, description="Rule version")


class RuleCreate(BaseModel):
    """Model for creating a new rule."""

    name: str = Field(..., min_length=1, max_length=200, description="Rule name")
    description: str = Field(..., min_length=1, description="Rule description")
    category: RuleCategory = Field(..., description="Rule category")
    severity: RuleSeverity = Field(default=RuleSeverity.MEDIUM, description="Rule severity")
    conditions: dict[str, Any] = Field(
        default_factory=dict, description="Rule conditions for evaluation"
    )
    actions: list[str] = Field(
        default_factory=list, description="Actions to take on violation"
    )
    priority: int = Field(default=0, ge=0, le=100, description="Rule priority (0-100)")
    created_by: str | None = Field(default=None, description="Creator identifier")


class RuleUpdate(BaseModel):
    """Model for updating an existing rule."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1)
    category: RuleCategory | None = None
    severity: RuleSeverity | None = None
    conditions: dict[str, Any] | None = None
    actions: list[str] | None = None
    is_active: bool | None = None
    priority: int | None = Field(default=None, ge=0, le=100)


class RuleEnforcementResult(BaseModel):
    """Result of enforcing a rule against an action."""

    model_config = ConfigDict(from_attributes=True)

    rule_id: UUID = Field(..., description="ID of the evaluated rule")
    rule_name: str = Field(..., description="Name of the evaluated rule")
    action_id: UUID = Field(..., description="ID of the evaluated action")
    is_violation: bool = Field(..., description="Whether the action violates the rule")
    severity: RuleSeverity = Field(..., description="Severity of the violation")
    message: str = Field(..., description="Human-readable enforcement result")
    details: dict[str, Any] = Field(
        default_factory=dict, description="Additional enforcement details"
    )
    enforced_at: datetime = Field(
        default_factory=datetime.utcnow, description="Enforcement timestamp"
    )
    recommended_actions: list[str] = Field(
        default_factory=list, description="Recommended follow-up actions"
    )
