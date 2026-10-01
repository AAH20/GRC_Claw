"""Policy-related schemas."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PolicyStatus(str, Enum):
    """Policy lifecycle status."""

    DRAFT = "draft"
    REVIEW = "review"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class PolicyCategory(str, Enum):
    """Policy category."""

    ETHICS = "ethics"
    SAFETY = "safety"
    PRIVACY = "privacy"
    FAIRNESS = "fairness"


class PolicyBase(BaseModel):
    """Base policy attributes."""

    policy_key: str = Field(..., pattern=r"^[A-Z0-9-]+$", max_length=100)
    name: str = Field(..., max_length=255)
    description: str | None = None
    category: PolicyCategory
    framework_tags: list[str] = Field(default_factory=list)
    cedar_policy: str | None = None
    metadata: dict[str, Any] | None = None


class PolicyCreate(PolicyBase):
    """Create policy request."""

    pass


class PolicyUpdate(BaseModel):
    """Update policy request."""

    name: str | None = None
    description: str | None = None
    cedar_policy: str | None = None
    metadata: dict[str, Any] | None = None


class PolicyInDB(PolicyBase):
    """Policy as stored in database."""

    id: str
    status: PolicyStatus
    version: str
    effective_date: datetime | None = None
    expiry_date: datetime | None = None
    owner_id: str
    agent_bindings: list[str] = Field(default_factory=list)
    rego_policy: str | None = None
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str

    model_config = {"from_attributes": True}


class PolicyResponse(PolicyInDB):
    """Policy response model."""

    pass


class PolicyVersion(BaseModel):
    """Policy version entry."""

    version: str
    status: str
    change_summary: str | None = None
    created_at: datetime
    created_by: str


class PolicyDependency(BaseModel):
    """Policy dependency entry."""

    target_policy_id: str
    target_policy_name: str
    relation_type: str
    description: str | None = None


class PolicyDependencyResponse(BaseModel):
    """Policy dependency graph response."""

    policy_id: str
    dependencies: list[PolicyDependency]
    dependents: list[PolicyDependency]


class CompilePolicyResponse(BaseModel):
    """Policy compilation response."""

    policy_id: str
    compilation_status: str
    rego_policy: str | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    compiled_at: datetime


class DryRunInput(BaseModel):
    """Single dry-run test input."""

    principal: dict[str, Any]
    action: str
    resource: dict[str, Any]
    context: dict[str, Any] | None = None


class DryRunRequest(BaseModel):
    """Dry-run policy request."""

    test_inputs: list[DryRunInput]


class DryRunResult(BaseModel):
    """Single dry-run result."""

    input_index: int
    decision: str
    matched_rules: list[str] = Field(default_factory=list)
    evaluation_time_ms: float
    reason: str | None = None


class DryRunSummary(BaseModel):
    """Dry-run summary."""

    total: int
    allowed: int
    denied: int
    avg_evaluation_time_ms: float


class DryRunResponse(BaseModel):
    """Dry-run policy response."""

    policy_id: str
    dry_run_results: list[DryRunResult]
    summary: DryRunSummary


class PolicyFilter(BaseModel):
    """Policy list filter parameters."""

    status: PolicyStatus | None = None
    category: PolicyCategory | None = None
    framework: str | None = None
    agent_id: str | None = None
