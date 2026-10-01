"""Enforcement-related schemas."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Verdict(str, Enum):
    """Enforcement decision verdict."""

    ALLOW = "ALLOW"
    ALLOW_WITH_REDACTION = "ALLOW_WITH_REDACTION"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    DENY = "DENY"
    QUARANTINE = "QUARANTINE"


class RedactionRule(BaseModel):
    """Redaction rule for ALLOW_WITH_REDACTION verdict."""

    field: str
    strategy: str  # "mask", "remove", "hash", "tokenize"
    pattern: str | None = None


class DecideRequest(BaseModel):
    """Single enforcement decision request."""

    agent_id: str
    action: str
    resource: str
    context: dict[str, Any] | None = None
    policy_ids: list[str] | None = None
    include_evidence: bool = True


class BatchDecideRequest(BaseModel):
    """Batch enforcement decision request."""

    decisions: list[DecideRequest]


class EnforcementDecision(BaseModel):
    """Enforcement decision response."""

    decision_id: str
    verdict: Verdict
    policy_id: str
    policy_version: str
    agent_id: str
    action: str
    resource: str
    context: dict[str, Any] | None = None
    evidence_hash: str | None = None
    timestamp: datetime
    ttl: int = 300
    signature: str | None = None
    matched_rules: list[str] = Field(default_factory=list)
    evaluation_time_ms: float
    reason: str | None = None
    redaction_rules: list[RedactionRule] | None = None


class BatchDecisionResult(BaseModel):
    """Single batch decision result."""

    decision_id: str
    verdict: Verdict
    policy_id: str
    evaluation_time_ms: float
    reason: str | None = None


class BatchDecisionSummary(BaseModel):
    """Batch decision summary."""

    total: int
    allowed: int
    denied: int
    avg_evaluation_time_ms: float


class BatchDecideResponse(BaseModel):
    """Batch enforcement decision response."""

    results: list[BatchDecisionResult]
    summary: BatchDecisionSummary


class DecisionFilter(BaseModel):
    """Decision list filter parameters."""

    agent_id: str | None = None
    policy_id: str | None = None
    verdict: Verdict | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
