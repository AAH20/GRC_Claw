"""
Error Taxonomy for GRC_Claw

Defines the classification system for all errors in the platform.
Every error is classified by category, severity, recoverability, and scope
to enable consistent handling, monitoring, and recovery.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ErrorCategory(str, Enum):
    """High-level error categories."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    RATE_LIMIT = "rate_limit"
    INTERNAL = "internal"
    EXTERNAL_SERVICE = "external_service"
    NETWORK = "network"
    TIMEOUT = "timeout"
    RESOURCE = "resource"
    CONFIGURATION = "configuration"
    POLICY = "policy"
    WORKFLOW = "workflow"
    DATA = "data"
    SECURITY = "security"
    DEPENDENCY = "dependency"
    UNKNOWN = "unknown"


class ErrorSeverity(str, Enum):
    """Error severity levels."""

    CRITICAL = "critical"  # System down, data loss risk
    HIGH = "high"  # Major feature broken, no workaround
    MEDIUM = "medium"  # Feature degraded, workaround exists
    LOW = "low"  # Minor issue, cosmetic
    INFO = "info"  # Informational, not a real error


class ErrorRecoverability(str, Enum):
    """Whether and how an error can be recovered from."""

    RETRYABLE = "retryable"  # Simple retry will likely succeed
    IDEMPOTENT_RETRY = "idempotent_retry"  # Safe to retry (idempotent operation)
    CIRCUIT_BREAK = "circuit_break"  # Stop calling, use fallback
    FALLBACK = "fallback"  # Use fallback/degraded mode
    MANUAL = "manual"  # Requires human intervention
    NON_RECOVERABLE = "non_recoverable"  # Cannot be recovered automatically


class ErrorScope(str, Enum):
    """Scope of impact for an error."""

    GLOBAL = "global"  # Affects entire platform
    TENANT = "tenant"  # Affects a single tenant
    USER = "user"  # Affects a single user
    REQUEST = "request"  # Affects a single request
    RESOURCE = "resource"  # Affects a specific resource
    AGENT = "agent"  # Affects a specific agent
    WORKFLOW = "workflow"  # Affects a specific workflow run


@dataclass
class ErrorClassification:
    """Complete classification of an error."""

    category: ErrorCategory
    severity: ErrorSeverity
    recoverability: ErrorRecoverability
    scope: ErrorScope
    http_status: int = 500
    retry_after_seconds: float | None = None
    alert_threshold: int = 10  # Errors per minute before alerting
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "recoverability": self.recoverability.value,
            "scope": self.scope.value,
            "http_status": self.http_status,
            "retry_after_seconds": self.retry_after_seconds,
            "alert_threshold": self.alert_threshold,
            "tags": self.tags,
            "metadata": self.metadata,
        }


# ── Classification Rules ──────────────────────────────────────────────────

_CLASSIFICATION_RULES: dict[str, ErrorClassification] = {
    # Authentication
    "UNAUTHENTICATED": ErrorClassification(
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.MEDIUM,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.REQUEST,
        http_status=401,
        tags=["auth", "security"],
    ),
    "TOKEN_EXPIRED": ErrorClassification(
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.MEDIUM,
        recoverability=ErrorRecoverability.RETRYABLE,
        scope=ErrorScope.USER,
        http_status=401,
        retry_after_seconds=0,
        tags=["auth", "token"],
    ),
    "TOKEN_INVALID": ErrorClassification(
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.MEDIUM,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.REQUEST,
        http_status=401,
        tags=["auth", "token"],
    ),
    "API_KEY_INVALID": ErrorClassification(
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.MEDIUM,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.REQUEST,
        http_status=401,
        tags=["auth", "api_key"],
    ),
    "API_KEY_EXPIRED": ErrorClassification(
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.MEDIUM,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.USER,
        http_status=401,
        tags=["auth", "api_key"],
    ),
    "OAUTH_TOKEN_FETCH_FAILED": ErrorClassification(
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.HIGH,
        recoverability=ErrorRecoverability.RETRYABLE,
        scope=ErrorScope.GLOBAL,
        http_status=502,
        retry_after_seconds=5,
        tags=["auth", "oauth"],
    ),
    "MTLS_VERIFICATION_FAILED": ErrorClassification(
        category=ErrorCategory.AUTHENTICATION,
        severity=ErrorSeverity.HIGH,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.REQUEST,
        http_status=401,
        tags=["auth", "mtls", "security"],
    ),
    # Authorization
    "FORBIDDEN": ErrorClassification(
        category=ErrorCategory.AUTHORIZATION,
        severity=ErrorSeverity.MEDIUM,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.REQUEST,
        http_status=403,
        tags=["authz"],
    ),
    "INSUFFICIENT_SCOPE": ErrorClassification(
        category=ErrorCategory.AUTHORIZATION,
        severity=ErrorSeverity.MEDIUM,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.REQUEST,
        http_status=403,
        tags=["authz", "scope"],
    ),
    "INSUFFICIENT_ROLE": ErrorClassification(
        category=ErrorCategory.AUTHORIZATION,
        severity=ErrorSeverity.MEDIUM,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.REQUEST,
        http_status=403,
        tags=["authz", "role"],
    ),
    "TENANT_ACCESS_DENIED": ErrorClassification(
        category=ErrorCategory.AUTHORIZATION,
        severity=ErrorSeverity.HIGH,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.TENANT,
        http_status=403,
        tags=["authz", "tenant"],
    ),
    # Validation
    "VALIDATION_ERROR": ErrorClassification(
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.LOW,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.REQUEST,
        http_status=400,
        tags=["validation"],
    ),
    "SCHEMA_VALIDATION_FAILED": ErrorClassification(
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.LOW,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.REQUEST,
        http_status=400,
        tags=["validation", "schema"],
    ),
    "INVALID_PARAMETER": ErrorClassification(
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.LOW,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.REQUEST,
        http_status=400,
        tags=["validation", "parameter"],
    ),
    "MISSING_REQUIRED_FIELD": ErrorClassification(
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.LOW,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.REQUEST,
        http_status=400,
        tags=["validation", "required"],
    ),
    "INVALID_FORMAT": ErrorClassification(
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.LOW,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.REQUEST,
        http_status=400,
        tags=["validation", "format"],
    ),
    # Not Found
    "NOT_FOUND": ErrorClassification(
        category=ErrorCategory.NOT_FOUND,
        severity=ErrorSeverity.LOW,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.RESOURCE,
        http_status=404,
        tags=["not_found"],
    ),
    "POLICY_NOT_FOUND": ErrorClassification(
        category=ErrorCategory.NOT_FOUND,
        severity=ErrorSeverity.LOW,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.RESOURCE,
        http_status=404,
        tags=["not_found", "policy"],
    ),
    "EVIDENCE_NOT_FOUND": ErrorClassification(
        category=ErrorCategory.NOT_FOUND,
        severity=ErrorSeverity.LOW,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.RESOURCE,
        http_status=404,
        tags=["not_found", "evidence"],
    ),
    "AGENT_NOT_FOUND": ErrorClassification(
        category=ErrorCategory.NOT_FOUND,
        severity=ErrorSeverity.LOW,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.AGENT,
        http_status=404,
        tags=["not_found", "agent"],
    ),
    "WORKFLOW_NOT_FOUND": ErrorClassification(
        category=ErrorCategory.NOT_FOUND,
        severity=ErrorSeverity.LOW,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.WORKFLOW,
        http_status=404,
        tags=["not_found", "workflow"],
    ),
    # Conflict
    "CONFLICT": ErrorClassification(
        category=ErrorCategory.CONFLICT,
        severity=ErrorSeverity.MEDIUM,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.RESOURCE,
        http_status=409,
        tags=["conflict"],
    ),
    "DUPLICATE_RESOURCE": ErrorClassification(
        category=ErrorCategory.CONFLICT,
        severity=ErrorSeverity.LOW,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.RESOURCE,
        http_status=409,
        tags=["conflict", "duplicate"],
    ),
    "RESOURCE_LOCKED": ErrorClassification(
        category=ErrorCategory.CONFLICT,
        severity=ErrorSeverity.MEDIUM,
        recoverability=ErrorRecoverability.RETRYABLE,
        scope=ErrorScope.RESOURCE,
        http_status=423,
        retry_after_seconds=30,
        tags=["conflict", "lock"],
    ),
    "OPTIMISTIC_LOCK_FAILURE": ErrorClassification(
        category=ErrorCategory.CONFLICT,
        severity=ErrorSeverity.LOW,
        recoverability=ErrorRecoverability.IDEMPOTENT_RETRY,
        scope=ErrorScope.RESOURCE,
        http_status=409,
        retry_after_seconds=1,
        tags=["conflict", "lock", "optimistic"],
    ),
    # Rate Limit
    "RATE_LIMIT_EXCEEDED": ErrorClassification(
        category=ErrorCategory.RATE_LIMIT,
        severity=ErrorSeverity.LOW,
        recoverability=ErrorRecoverability.RETRYABLE,
        scope=ErrorScope.USER,
        http_status=429,
        retry_after_seconds=30,
        tags=["rate_limit"],
    ),
    "QUOTA_EXCEEDED": ErrorClassification(
        category=ErrorCategory.RATE_LIMIT,
        severity=ErrorSeverity.MEDIUM,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.TENANT,
        http_status=429,
        tags=["quota"],
    ),
    "BURST_LIMIT_EXCEEDED": ErrorClassification(
        category=ErrorCategory.RATE_LIMIT,
        severity=ErrorSeverity.LOW,
        recoverability=ErrorRecoverability.RETRYABLE,
        scope=ErrorScope.USER,
        http_status=429,
        retry_after_seconds=1,
        tags=["rate_limit", "burst"],
    ),
    # Internal
    "INTERNAL_ERROR": ErrorClassification(
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.CRITICAL,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.GLOBAL,
        http_status=500,
        alert_threshold=5,
        tags=["internal"],
    ),
    "NOT_IMPLEMENTED": ErrorClassification(
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.LOW,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.REQUEST,
        http_status=501,
        tags=["internal", "not_implemented"],
    ),
    "SERVICE_UNAVAILABLE": ErrorClassification(
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.HIGH,
        recoverability=ErrorRecoverability.CIRCUIT_BREAK,
        scope=ErrorScope.GLOBAL,
        http_status=503,
        retry_after_seconds=30,
        alert_threshold=5,
        tags=["internal", "availability"],
    ),
    # External Service
    "EXTERNAL_SERVICE_ERROR": ErrorClassification(
        category=ErrorCategory.EXTERNAL_SERVICE,
        severity=ErrorSeverity.HIGH,
        recoverability=ErrorRecoverability.CIRCUIT_BREAK,
        scope=ErrorScope.GLOBAL,
        http_status=502,
        retry_after_seconds=10,
        alert_threshold=10,
        tags=["external"],
    ),
    "UPSTREAM_TIMEOUT": ErrorClassification(
        category=ErrorCategory.EXTERNAL_SERVICE,
        severity=ErrorSeverity.HIGH,
        recoverability=ErrorRecoverability.CIRCUIT_BREAK,
        scope=ErrorScope.GLOBAL,
        http_status=504,
        retry_after_seconds=5,
        alert_threshold=10,
        tags=["external", "timeout"],
    ),
    "UPSTREAM_UNAVAILABLE": ErrorClassification(
        category=ErrorCategory.EXTERNAL_SERVICE,
        severity=ErrorSeverity.HIGH,
        recoverability=ErrorRecoverability.CIRCUIT_BREAK,
        scope=ErrorScope.GLOBAL,
        http_status=503,
        retry_after_seconds=30,
        alert_threshold=5,
        tags=["external", "availability"],
    ),
    "CONNECTOR_ERROR": ErrorClassification(
        category=ErrorCategory.EXTERNAL_SERVICE,
        severity=ErrorSeverity.MEDIUM,
        recoverability=ErrorRecoverability.RETRYABLE,
        scope=ErrorScope.RESOURCE,
        http_status=502,
        retry_after_seconds=5,
        tags=["external", "connector"],
    ),
    "WEBHOOK_DELIVERY_FAILED": ErrorClassification(
        category=ErrorCategory.EXTERNAL_SERVICE,
        severity=ErrorSeverity.MEDIUM,
        recoverability=ErrorRecoverability.RETRYABLE,
        scope=ErrorScope.RESOURCE,
        http_status=502,
        retry_after_seconds=60,
        tags=["external", "webhook"],
    ),
    # Network
    "NETWORK_ERROR": ErrorClassification(
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.HIGH,
        recoverability=ErrorRecoverability.RETRYABLE,
        scope=ErrorScope.GLOBAL,
        http_status=502,
        retry_after_seconds=2,
        tags=["network"],
    ),
    "DNS_RESOLUTION_FAILED": ErrorClassification(
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.HIGH,
        recoverability=ErrorRecoverability.RETRYABLE,
        scope=ErrorScope.GLOBAL,
        http_status=502,
        retry_after_seconds=5,
        tags=["network", "dns"],
    ),
    "TLS_HANDSHAKE_FAILED": ErrorClassification(
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.HIGH,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.GLOBAL,
        http_status=502,
        tags=["network", "tls", "security"],
    ),
    # Timeout
    "TIMEOUT": ErrorClassification(
        category=ErrorCategory.TIMEOUT,
        severity=ErrorSeverity.MEDIUM,
        recoverability=ErrorRecoverability.RETRYABLE,
        scope=ErrorScope.REQUEST,
        http_status=408,
        retry_after_seconds=1,
        tags=["timeout"],
    ),
    "REQUEST_TIMEOUT": ErrorClassification(
        category=ErrorCategory.TIMEOUT,
        severity=ErrorSeverity.MEDIUM,
        recoverability=ErrorRecoverability.RETRYABLE,
        scope=ErrorScope.REQUEST,
        http_status=408,
        retry_after_seconds=1,
        tags=["timeout", "request"],
    ),
    "WORKFLOW_STEP_TIMEOUT": ErrorClassification(
        category=ErrorCategory.TIMEOUT,
        severity=ErrorSeverity.MEDIUM,
        recoverability=ErrorRecoverability.RETRYABLE,
        scope=ErrorScope.WORKFLOW,
        http_status=408,
        retry_after_seconds=5,
        tags=["timeout", "workflow"],
    ),
    "AGENT_EXECUTION_TIMEOUT": ErrorClassification(
        category=ErrorCategory.TIMEOUT,
        severity=ErrorSeverity.HIGH,
        recoverability=ErrorRecoverability.RETRYABLE,
        scope=ErrorScope.AGENT,
        http_status=408,
        retry_after_seconds=10,
        tags=["timeout", "agent"],
    ),
    # Resource
    "RESOURCE_EXHAUSTED": ErrorClassification(
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.HIGH,
        recoverability=ErrorRecoverability.FALLBACK,
        scope=ErrorScope.GLOBAL,
        http_status=503,
        retry_after_seconds=60,
        alert_threshold=5,
        tags=["resource", "exhausted"],
    ),
    "MEMORY_LIMIT_EXCEEDED": ErrorClassification(
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.CRITICAL,
        recoverability=ErrorRecoverability.FALLBACK,
        scope=ErrorScope.GLOBAL,
        http_status=503,
        retry_after_seconds=30,
        alert_threshold=3,
        tags=["resource", "memory"],
    ),
    "DISK_FULL": ErrorClassification(
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.CRITICAL,
        recoverability=ErrorRecoverability.MANUAL,
        scope=ErrorScope.GLOBAL,
        http_status=503,
        alert_threshold=1,
        tags=["resource", "disk"],
    ),
    "CONCURRENCY_LIMIT_EXCEEDED": ErrorClassification(
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.MEDIUM,
        recoverability=ErrorRecoverability.RETRYABLE,
        scope=ErrorScope.TENANT,
        http_status=503,
        retry_after_seconds=5,
        tags=["resource", "concurrency"],
    ),
    # Configuration
    "CONFIGURATION_ERROR": ErrorClassification(
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.HIGH,
        recoverability=ErrorRecoverability.MANUAL,
        scope=ErrorScope.GLOBAL,
        http_status=500,
        alert_threshold=1,
        tags=["config"],
    ),
    "INVALID_CONFIGURATION": ErrorClassification(
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.HIGH,
        recoverability=ErrorRecoverability.MANUAL,
        scope=ErrorScope.GLOBAL,
        http_status=500,
        alert_threshold=1,
        tags=["config", "invalid"],
    ),
    "MISSING_CONFIGURATION": ErrorClassification(
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.HIGH,
        recoverability=ErrorRecoverability.MANUAL,
        scope=ErrorScope.GLOBAL,
        http_status=500,
        alert_threshold=1,
        tags=["config", "missing"],
    ),
    # Policy
    "POLICY_COMPILATION_FAILED": ErrorClassification(
        category=ErrorCategory.POLICY,
        severity=ErrorSeverity.MEDIUM,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.RESOURCE,
        http_status=422,
        tags=["policy", "compilation"],
    ),
    "POLICY_EVALUATION_FAILED": ErrorClassification(
        category=ErrorCategory.POLICY,
        severity=ErrorSeverity.HIGH,
        recoverability=ErrorRecoverability.FALLBACK,
        scope=ErrorScope.REQUEST,
        http_status=500,
        tags=["policy", "evaluation"],
    ),
    "POLICY_CONFLICT": ErrorClassification(
        category=ErrorCategory.POLICY,
        severity=ErrorSeverity.MEDIUM,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.RESOURCE,
        http_status=409,
        tags=["policy", "conflict"],
    ),
    "POLICY_VERSION_MISMATCH": ErrorClassification(
        category=ErrorCategory.POLICY,
        severity=ErrorSeverity.MEDIUM,
        recoverability=ErrorRecoverability.RETRYABLE,
        scope=ErrorScope.RESOURCE,
        http_status=409,
        retry_after_seconds=1,
        tags=["policy", "version"],
    ),
    # Workflow
    "WORKFLOW_EXECUTION_FAILED": ErrorClassification(
        category=ErrorCategory.WORKFLOW,
        severity=ErrorSeverity.HIGH,
        recoverability=ErrorRecoverability.MANUAL,
        scope=ErrorScope.WORKFLOW,
        http_status=500,
        alert_threshold=5,
        tags=["workflow", "execution"],
    ),
    "WORKFLOW_STEP_FAILED": ErrorClassification(
        category=ErrorCategory.WORKFLOW,
        severity=ErrorSeverity.MEDIUM,
        recoverability=ErrorRecoverability.RETRYABLE,
        scope=ErrorScope.WORKFLOW,
        http_status=500,
        retry_after_seconds=5,
        tags=["workflow", "step"],
    ),
    "WORKFLOW_CANCELLED": ErrorClassification(
        category=ErrorCategory.WORKFLOW,
        severity=ErrorSeverity.LOW,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.WORKFLOW,
        http_status=499,
        tags=["workflow", "cancelled"],
    ),
    "WORKFLOW_DEADLINE_EXCEEDED": ErrorClassification(
        category=ErrorCategory.WORKFLOW,
        severity=ErrorSeverity.HIGH,
        recoverability=ErrorRecoverability.MANUAL,
        scope=ErrorScope.WORKFLOW,
        http_status=408,
        tags=["workflow", "deadline"],
    ),
    # Data
    "DATA_INTEGRITY_ERROR": ErrorClassification(
        category=ErrorCategory.DATA,
        severity=ErrorSeverity.CRITICAL,
        recoverability=ErrorRecoverability.MANUAL,
        scope=ErrorScope.GLOBAL,
        http_status=500,
        alert_threshold=1,
        tags=["data", "integrity"],
    ),
    "DATA_VALIDATION_FAILED": ErrorClassification(
        category=ErrorCategory.DATA,
        severity=ErrorSeverity.MEDIUM,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.RESOURCE,
        http_status=422,
        tags=["data", "validation"],
    ),
    "DATA_TRANSFORMATION_FAILED": ErrorClassification(
        category=ErrorCategory.DATA,
        severity=ErrorSeverity.MEDIUM,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.RESOURCE,
        http_status=422,
        tags=["data", "transformation"],
    ),
    "DATA_MIGRATION_FAILED": ErrorClassification(
        category=ErrorCategory.DATA,
        severity=ErrorSeverity.CRITICAL,
        recoverability=ErrorRecoverability.MANUAL,
        scope=ErrorScope.GLOBAL,
        http_status=500,
        alert_threshold=1,
        tags=["data", "migration"],
    ),
    # Security
    "SECURITY_VIOLATION": ErrorClassification(
        category=ErrorCategory.SECURITY,
        severity=ErrorSeverity.CRITICAL,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.GLOBAL,
        http_status=403,
        alert_threshold=1,
        tags=["security", "violation"],
    ),
    "SUSPICIOUS_ACTIVITY": ErrorClassification(
        category=ErrorCategory.SECURITY,
        severity=ErrorSeverity.HIGH,
        recoverability=ErrorRecoverability.MANUAL,
        scope=ErrorScope.USER,
        http_status=403,
        alert_threshold=3,
        tags=["security", "suspicious"],
    ),
    "CSRF_TOKEN_INVALID": ErrorClassification(
        category=ErrorCategory.SECURITY,
        severity=ErrorSeverity.MEDIUM,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.REQUEST,
        http_status=403,
        tags=["security", "csrf"],
    ),
    "ENCRYPTION_FAILED": ErrorClassification(
        category=ErrorCategory.SECURITY,
        severity=ErrorSeverity.CRITICAL,
        recoverability=ErrorRecoverability.NON_RECOVERABLE,
        scope=ErrorScope.GLOBAL,
        http_status=500,
        alert_threshold=1,
        tags=["security", "encryption"],
    ),
    # Dependency
    "DEPENDENCY_UNAVAILABLE": ErrorClassification(
        category=ErrorCategory.DEPENDENCY,
        severity=ErrorSeverity.HIGH,
        recoverability=ErrorRecoverability.CIRCUIT_BREAK,
        scope=ErrorScope.GLOBAL,
        http_status=503,
        retry_after_seconds=30,
        alert_threshold=5,
        tags=["dependency"],
    ),
    "DEPENDENCY_TIMEOUT": ErrorClassification(
        category=ErrorCategory.DEPENDENCY,
        severity=ErrorSeverity.HIGH,
        recoverability=ErrorRecoverability.CIRCUIT_BREAK,
        scope=ErrorScope.GLOBAL,
        http_status=504,
        retry_after_seconds=5,
        alert_threshold=10,
        tags=["dependency", "timeout"],
    ),
    "DEPENDENCY_VERSION_MISMATCH": ErrorClassification(
        category=ErrorCategory.DEPENDENCY,
        severity=ErrorSeverity.MEDIUM,
        recoverability=ErrorRecoverability.MANUAL,
        scope=ErrorScope.GLOBAL,
        http_status=500,
        tags=["dependency", "version"],
    ),
}

_DEFAULT_CLASSIFICATION = ErrorClassification(
    category=ErrorCategory.UNKNOWN,
    severity=ErrorSeverity.MEDIUM,
    recoverability=ErrorRecoverability.NON_RECOVERABLE,
    scope=ErrorScope.REQUEST,
    http_status=500,
    tags=["unknown"],
)


def classify_error(code: str) -> ErrorClassification:
    """Get the classification for an error code.

    Args:
        code: The error code string (e.g., "UNAUTHENTICATED").

    Returns:
        The ErrorClassification for the code, or a default if unknown.
    """
    return _CLASSIFICATION_RULES.get(code, _DEFAULT_CLASSIFICATION)


def get_codes_by_category(category: ErrorCategory) -> list[str]:
    """Get all error codes for a given category."""
    return [
        code
        for code, cls in _CLASSIFICATION_RULES.items()
        if cls.category == category
    ]


def get_codes_by_severity(severity: ErrorSeverity) -> list[str]:
    """Get all error codes for a given severity."""
    return [
        code
        for code, cls in _CLASSIFICATION_RULES.items()
        if cls.severity == severity
    ]


def get_retryable_codes() -> list[str]:
    """Get all error codes that are retryable."""
    return [
        code
        for code, cls in _CLASSIFICATION_RULES.items()
        if cls.recoverability
        in (ErrorRecoverability.RETRYABLE, ErrorRecoverability.IDEMPOTENT_RETRY)
    ]


def get_circuit_breakable_codes() -> list[str]:
    """Get all error codes that should trigger circuit breaking."""
    return [
        code
        for code, cls in _CLASSIFICATION_RULES.items()
        if cls.recoverability == ErrorRecoverability.CIRCUIT_BREAK
    ]
