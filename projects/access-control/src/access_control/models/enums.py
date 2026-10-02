"""Enumerations used across the access control service."""

from __future__ import annotations

from enum import StrEnum


class AccessDecision(StrEnum):
    """Possible outcomes of an access evaluation."""

    ALLOW = "allow"
    DENY = "deny"
    CONDITIONAL = "conditional"
    ABSTAIN = "abstain"


class AuditSeverity(StrEnum):
    """Severity levels for audit entries."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class PolicyEffect(StrEnum):
    """Effect of a policy rule."""

    ALLOW = "allow"
    DENY = "deny"


class RoleStatus(StrEnum):
    """Lifecycle status of a role."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    PENDING = "pending"
