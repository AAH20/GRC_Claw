"""Enumerations used across the access control service."""

from __future__ import annotations

from enum import Enum


class AccessDecision(str, Enum):
    """Possible outcomes of an access evaluation."""

    ALLOW = "allow"
    DENY = "deny"
    CONDITIONAL = "conditional"
    ABSTAIN = "abstain"


class AuditSeverity(str, Enum):
    """Severity levels for audit entries."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class PolicyEffect(str, Enum):
    """Effect of a policy rule."""

    ALLOW = "allow"
    DENY = "deny"


class RoleStatus(str, Enum):
    """Lifecycle status of a role."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    PENDING = "pending"
