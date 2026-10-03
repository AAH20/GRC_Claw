"""Pydantic schemas for access control API requests and responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, Literal, TypeVar
from uuid import UUID, uuid4

from access_control.models.enums import AccessDecision, AuditSeverity, PolicyEffect, RoleStatus
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Permission
# ---------------------------------------------------------------------------


class Permission(BaseModel):
    """A single permission grant within a role or policy."""

    model_config = ConfigDict(frozen=True)

    resource: str = Field(
        ..., description="Resource identifier (e.g. 'documents', 'api/users')"
    )
    action: str = Field(..., description="Action verb (e.g. 'read', 'write', 'delete')")
    conditions: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional conditions (e.g. time-based, IP-based)",
    )
    effect: PolicyEffect = Field(
        default=PolicyEffect.ALLOW, description="Allow or deny this permission"
    )


# ---------------------------------------------------------------------------
# Role
# ---------------------------------------------------------------------------


class Role(BaseModel):
    """A role groups permissions and can be assigned to users or agents."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4, description="Unique role identifier")
    name: str = Field(
        ..., min_length=1, max_length=128, description="Human-readable role name"
    )
    description: str = Field(default="", description="Role description")
    permissions: list[Permission] = Field(
        default_factory=list, description="Permissions granted by this role"
    )
    status: RoleStatus = Field(
        default=RoleStatus.ACTIVE, description="Lifecycle status"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary metadata"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )


class RoleCreate(BaseModel):
    """Payload for creating a new role."""

    name: str = Field(..., min_length=1, max_length=128)
    description: str = Field(default="")
    permissions: list[Permission] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RoleUpdate(BaseModel):
    """Payload for updating an existing role (all fields optional)."""

    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = None
    permissions: list[Permission] | None = None
    status: RoleStatus | None = None
    metadata: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Access Request / Result
# ---------------------------------------------------------------------------


class AccessRequest(BaseModel):
    """A request to evaluate whether a principal may perform an action on a resource."""

    principal_id: str = Field(
        ..., description="Identifier of the user or agent requesting access"
    )
    resource: str = Field(..., description="Resource being accessed")
    action: str = Field(..., description="Action being attempted")
    context: dict[str, Any] = Field(
        default_factory=dict, description="Additional context (IP, time, device, etc.)"
    )
    roles: list[str] = Field(
        default_factory=list, description="Role IDs assigned to the principal"
    )


class AccessResult(BaseModel):
    """The outcome of evaluating an access request."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    request: AccessRequest
    decision: AccessDecision
    reason: str = Field(
        default="", description="Human-readable explanation for the decision"
    )
    obligations: list[str] = Field(
        default_factory=list,
        description="Actions the principal must perform (e.g. MFA)",
    )
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    policy_ids: list[str] = Field(
        default_factory=list, description="Policies that were evaluated"
    )
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Confidence score"
    )


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------


class Policy(BaseModel):
    """An access control policy consisting of rules."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=128)
    description: str = Field(default="")
    rules: list[Permission] = Field(default_factory=list)
    priority: int = Field(
        default=0, ge=0, description="Higher priority policies are evaluated first"
    )
    enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


class AccessAudit(BaseModel):
    """An audit log entry recording an access-related event."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    principal_id: str = Field(..., description="Who performed the action")
    action: str = Field(..., description="What action was performed")
    resource: str = Field(..., description="On what resource")
    decision: AccessDecision
    severity: AuditSeverity = Field(default=AuditSeverity.INFO)
    details: dict[str, Any] = Field(default_factory=dict)
    ip_address: str | None = Field(default=None)
    user_agent: str | None = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Recommendation
# ---------------------------------------------------------------------------


class AccessRecommendation(BaseModel):
    """A recommendation for access changes generated by the recommender agent."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    principal_id: str = Field(
        ..., description="User or agent the recommendation is for"
    )
    resource: str
    action: str
    recommendation: Literal["grant", "revoke", "modify", "review"]
    reason: str = Field(default="")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Paginated Response
# ---------------------------------------------------------------------------


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    pages: int = Field(..., ge=0)
