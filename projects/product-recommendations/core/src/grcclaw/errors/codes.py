"""
Error Codes Registry for GRC_Claw

Central registry of all error codes used across the platform.
Each code has a unique identifier, default message, and classification.
Codes are organized by category for discoverability.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .taxonomy import (
    ErrorCategory,
    ErrorRecoverability,
    ErrorScope,
    ErrorSeverity,
    classify_error,
)


@dataclass(frozen=True)
class ErrorCode:
    """A registered error code with metadata."""

    code: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    recoverability: ErrorRecoverability
    scope: ErrorScope
    http_status: int
    retry_after_seconds: float | None = None
    alert_threshold: int = 10
    tags: tuple[str, ...] = ()
    documentation_url: str = ""

    @classmethod
    def from_code_string(cls, code: str) -> ErrorCode:
        """Create an ErrorCode from a code string using the taxonomy."""
        classification = classify_error(code)
        return cls(
            code=code,
            message=code.replace("_", " ").title(),
            category=classification.category,
            severity=classification.severity,
            recoverability=classification.recoverability,
            scope=classification.scope,
            http_status=classification.http_status,
            retry_after_seconds=classification.retry_after_seconds,
            alert_threshold=classification.alert_threshold,
            tags=tuple(classification.tags),
            documentation_url=f"https://docs.grc-claw.io/errors/{code.lower()}",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "recoverability": self.recoverability.value,
            "scope": self.scope.value,
            "http_status": self.http_status,
            "retry_after_seconds": self.retry_after_seconds,
            "alert_threshold": self.alert_threshold,
            "tags": list(self.tags),
            "documentation_url": self.documentation_url,
        }


class ErrorRegistry:
    """Central registry of all error codes."""

    def __init__(self) -> None:
        self._codes: dict[str, ErrorCode] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register all default error codes from the taxonomy."""
        # Authentication
        self.register(ErrorCode(
            code="UNAUTHENTICATED",
            message="Missing or invalid credentials",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.MEDIUM,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.REQUEST,
            http_status=401,
            tags=("auth", "security"),
        ))
        self.register(ErrorCode(
            code="TOKEN_EXPIRED",
            message="Authentication token has expired",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.MEDIUM,
            recoverability=ErrorRecoverability.RETRYABLE,
            scope=ErrorScope.USER,
            http_status=401,
            retry_after_seconds=0,
            tags=("auth", "token"),
        ))
        self.register(ErrorCode(
            code="TOKEN_INVALID",
            message="Authentication token is invalid",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.MEDIUM,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.REQUEST,
            http_status=401,
            tags=("auth", "token"),
        ))
        self.register(ErrorCode(
            code="API_KEY_INVALID",
            message="API key is invalid",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.MEDIUM,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.REQUEST,
            http_status=401,
            tags=("auth", "api_key"),
        ))
        self.register(ErrorCode(
            code="API_KEY_EXPIRED",
            message="API key has expired",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.MEDIUM,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.USER,
            http_status=401,
            tags=("auth", "api_key"),
        ))
        self.register(ErrorCode(
            code="OAUTH_TOKEN_FETCH_FAILED",
            message="Failed to fetch OAuth2 token",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            recoverability=ErrorRecoverability.RETRYABLE,
            scope=ErrorScope.GLOBAL,
            http_status=502,
            retry_after_seconds=5,
            tags=("auth", "oauth"),
        ))
        self.register(ErrorCode(
            code="MTLS_VERIFICATION_FAILED",
            message="mTLS certificate verification failed",
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.REQUEST,
            http_status=401,
            tags=("auth", "mtls", "security"),
        ))

        # Authorization
        self.register(ErrorCode(
            code="FORBIDDEN",
            message="Insufficient permissions",
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.MEDIUM,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.REQUEST,
            http_status=403,
            tags=("authz",),
        ))
        self.register(ErrorCode(
            code="INSUFFICIENT_SCOPE",
            message="Insufficient scope for this operation",
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.MEDIUM,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.REQUEST,
            http_status=403,
            tags=("authz", "scope"),
        ))
        self.register(ErrorCode(
            code="INSUFFICIENT_ROLE",
            message="Insufficient role for this operation",
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.MEDIUM,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.REQUEST,
            http_status=403,
            tags=("authz", "role"),
        ))
        self.register(ErrorCode(
            code="TENANT_ACCESS_DENIED",
            message="Access to tenant resource denied",
            category=ErrorCategory.AUTHORIZATION,
            severity=ErrorSeverity.HIGH,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.TENANT,
            http_status=403,
            tags=("authz", "tenant"),
        ))

        # Validation
        self.register(ErrorCode(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.REQUEST,
            http_status=400,
            tags=("validation",),
        ))
        self.register(ErrorCode(
            code="SCHEMA_VALIDATION_FAILED",
            message="Schema validation failed",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.REQUEST,
            http_status=400,
            tags=("validation", "schema"),
        ))
        self.register(ErrorCode(
            code="INVALID_PARAMETER",
            message="Invalid parameter value",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.REQUEST,
            http_status=400,
            tags=("validation", "parameter"),
        ))
        self.register(ErrorCode(
            code="MISSING_REQUIRED_FIELD",
            message="Missing required field",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.REQUEST,
            http_status=400,
            tags=("validation", "required"),
        ))
        self.register(ErrorCode(
            code="INVALID_FORMAT",
            message="Invalid data format",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.REQUEST,
            http_status=400,
            tags=("validation", "format"),
        ))

        # Not Found
        self.register(ErrorCode(
            code="NOT_FOUND",
            message="Resource not found",
            category=ErrorCategory.NOT_FOUND,
            severity=ErrorSeverity.LOW,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.RESOURCE,
            http_status=404,
            tags=("not_found",),
        ))
        self.register(ErrorCode(
            code="POLICY_NOT_FOUND",
            message="Policy not found",
            category=ErrorCategory.NOT_FOUND,
            severity=ErrorSeverity.LOW,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.RESOURCE,
            http_status=404,
            tags=("not_found", "policy"),
        ))
        self.register(ErrorCode(
            code="EVIDENCE_NOT_FOUND",
            message="Evidence not found",
            category=ErrorCategory.NOT_FOUND,
            severity=ErrorSeverity.LOW,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.RESOURCE,
            http_status=404,
            tags=("not_found", "evidence"),
        ))
        self.register(ErrorCode(
            code="AGENT_NOT_FOUND",
            message="Agent not found",
            category=ErrorCategory.NOT_FOUND,
            severity=ErrorSeverity.LOW,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.AGENT,
            http_status=404,
            tags=("not_found", "agent"),
        ))
        self.register(ErrorCode(
            code="WORKFLOW_NOT_FOUND",
            message="Workflow not found",
            category=ErrorCategory.NOT_FOUND,
            severity=ErrorSeverity.LOW,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.WORKFLOW,
            http_status=404,
            tags=("not_found", "workflow"),
        ))

        # Conflict
        self.register(ErrorCode(
            code="CONFLICT",
            message="Resource conflict",
            category=ErrorCategory.CONFLICT,
            severity=ErrorSeverity.MEDIUM,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.RESOURCE,
            http_status=409,
            tags=("conflict",),
        ))
        self.register(ErrorCode(
            code="DUPLICATE_RESOURCE",
            message="Duplicate resource",
            category=ErrorCategory.CONFLICT,
            severity=ErrorSeverity.LOW,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.RESOURCE,
            http_status=409,
            tags=("conflict", "duplicate"),
        ))
        self.register(ErrorCode(
            code="RESOURCE_LOCKED",
            message="Resource is locked by another operation",
            category=ErrorCategory.CONFLICT,
            severity=ErrorSeverity.MEDIUM,
            recoverability=ErrorRecoverability.RETRYABLE,
            scope=ErrorScope.RESOURCE,
            http_status=423,
            retry_after_seconds=30,
            tags=("conflict", "lock"),
        ))
        self.register(ErrorCode(
            code="OPTIMISTIC_LOCK_FAILURE",
            message="Optimistic lock failure, resource was modified",
            category=ErrorCategory.CONFLICT,
            severity=ErrorSeverity.LOW,
            recoverability=ErrorRecoverability.IDEMPOTENT_RETRY,
            scope=ErrorScope.RESOURCE,
            http_status=409,
            retry_after_seconds=1,
            tags=("conflict", "lock", "optimistic"),
        ))

        # Rate Limit
        self.register(ErrorCode(
            code="RATE_LIMIT_EXCEEDED",
            message="Rate limit exceeded",
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.LOW,
            recoverability=ErrorRecoverability.RETRYABLE,
            scope=ErrorScope.USER,
            http_status=429,
            retry_after_seconds=30,
            tags=("rate_limit",),
        ))
        self.register(ErrorCode(
            code="QUOTA_EXCEEDED",
            message="Quota exceeded",
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.TENANT,
            http_status=429,
            tags=("quota",),
        ))
        self.register(ErrorCode(
            code="BURST_LIMIT_EXCEEDED",
            message="Burst rate limit exceeded",
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.LOW,
            recoverability=ErrorRecoverability.RETRYABLE,
            scope=ErrorScope.USER,
            http_status=429,
            retry_after_seconds=1,
            tags=("rate_limit", "burst"),
        ))

        # Internal
        self.register(ErrorCode(
            code="INTERNAL_ERROR",
            message="An unexpected internal error occurred",
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.CRITICAL,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.GLOBAL,
            http_status=500,
            alert_threshold=5,
            tags=("internal",),
        ))
        self.register(ErrorCode(
            code="NOT_IMPLEMENTED",
            message="Feature not implemented",
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.LOW,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.REQUEST,
            http_status=501,
            tags=("internal", "not_implemented"),
        ))
        self.register(ErrorCode(
            code="SERVICE_UNAVAILABLE",
            message="Service is temporarily unavailable",
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.HIGH,
            recoverability=ErrorRecoverability.CIRCUIT_BREAK,
            scope=ErrorScope.GLOBAL,
            http_status=503,
            retry_after_seconds=30,
            alert_threshold=5,
            tags=("internal", "availability"),
        ))

        # External Service
        self.register(ErrorCode(
            code="EXTERNAL_SERVICE_ERROR",
            message="External service returned an error",
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.HIGH,
            recoverability=ErrorRecoverability.CIRCUIT_BREAK,
            scope=ErrorScope.GLOBAL,
            http_status=502,
            retry_after_seconds=10,
            alert_threshold=10,
            tags=("external",),
        ))
        self.register(ErrorCode(
            code="UPSTREAM_TIMEOUT",
            message="Upstream service timed out",
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.HIGH,
            recoverability=ErrorRecoverability.CIRCUIT_BREAK,
            scope=ErrorScope.GLOBAL,
            http_status=504,
            retry_after_seconds=5,
            alert_threshold=10,
            tags=("external", "timeout"),
        ))
        self.register(ErrorCode(
            code="UPSTREAM_UNAVAILABLE",
            message="Upstream service is unavailable",
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.HIGH,
            recoverability=ErrorRecoverability.CIRCUIT_BREAK,
            scope=ErrorScope.GLOBAL,
            http_status=503,
            retry_after_seconds=30,
            alert_threshold=5,
            tags=("external", "availability"),
        ))
        self.register(ErrorCode(
            code="CONNECTOR_ERROR",
            message="Connector operation failed",
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.MEDIUM,
            recoverability=ErrorRecoverability.RETRYABLE,
            scope=ErrorScope.RESOURCE,
            http_status=502,
            retry_after_seconds=5,
            tags=("external", "connector"),
        ))
        self.register(ErrorCode(
            code="WEBHOOK_DELIVERY_FAILED",
            message="Webhook delivery failed",
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.MEDIUM,
            recoverability=ErrorRecoverability.RETRYABLE,
            scope=ErrorScope.RESOURCE,
            http_status=502,
            retry_after_seconds=60,
            tags=("external", "webhook"),
        ))

        # Network
        self.register(ErrorCode(
            code="NETWORK_ERROR",
            message="Network communication error",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            recoverability=ErrorRecoverability.RETRYABLE,
            scope=ErrorScope.GLOBAL,
            http_status=502,
            retry_after_seconds=2,
            tags=("network",),
        ))
        self.register(ErrorCode(
            code="DNS_RESOLUTION_FAILED",
            message="DNS resolution failed",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            recoverability=ErrorRecoverability.RETRYABLE,
            scope=ErrorScope.GLOBAL,
            http_status=502,
            retry_after_seconds=5,
            tags=("network", "dns"),
        ))
        self.register(ErrorCode(
            code="TLS_HANDSHAKE_FAILED",
            message="TLS handshake failed",
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.GLOBAL,
            http_status=502,
            tags=("network", "tls", "security"),
        ))

        # Timeout
        self.register(ErrorCode(
            code="TIMEOUT",
            message="Operation timed out",
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            recoverability=ErrorRecoverability.RETRYABLE,
            scope=ErrorScope.REQUEST,
            http_status=408,
            retry_after_seconds=1,
            tags=("timeout",),
        ))
        self.register(ErrorCode(
            code="REQUEST_TIMEOUT",
            message="Request timed out",
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            recoverability=ErrorRecoverability.RETRYABLE,
            scope=ErrorScope.REQUEST,
            http_status=408,
            retry_after_seconds=1,
            tags=("timeout", "request"),
        ))
        self.register(ErrorCode(
            code="WORKFLOW_STEP_TIMEOUT",
            message="Workflow step timed out",
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            recoverability=ErrorRecoverability.RETRYABLE,
            scope=ErrorScope.WORKFLOW,
            http_status=408,
            retry_after_seconds=5,
            tags=("timeout", "workflow"),
        ))
        self.register(ErrorCode(
            code="AGENT_EXECUTION_TIMEOUT",
            message="Agent execution timed out",
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.HIGH,
            recoverability=ErrorRecoverability.RETRYABLE,
            scope=ErrorScope.AGENT,
            http_status=408,
            retry_after_seconds=10,
            tags=("timeout", "agent"),
        ))

        # Resource
        self.register(ErrorCode(
            code="RESOURCE_EXHAUSTED",
            message="Resource exhausted",
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.HIGH,
            recoverability=ErrorRecoverability.FALLBACK,
            scope=ErrorScope.GLOBAL,
            http_status=503,
            retry_after_seconds=60,
            alert_threshold=5,
            tags=("resource", "exhausted"),
        ))
        self.register(ErrorCode(
            code="MEMORY_LIMIT_EXCEEDED",
            message="Memory limit exceeded",
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.CRITICAL,
            recoverability=ErrorRecoverability.FALLBACK,
            scope=ErrorScope.GLOBAL,
            http_status=503,
            retry_after_seconds=30,
            alert_threshold=3,
            tags=("resource", "memory"),
        ))
        self.register(ErrorCode(
            code="DISK_FULL",
            message="Disk space exhausted",
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.CRITICAL,
            recoverability=ErrorRecoverability.MANUAL,
            scope=ErrorScope.GLOBAL,
            http_status=503,
            alert_threshold=1,
            tags=("resource", "disk"),
        ))
        self.register(ErrorCode(
            code="CONCURRENCY_LIMIT_EXCEEDED",
            message="Concurrency limit exceeded",
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.MEDIUM,
            recoverability=ErrorRecoverability.RETRYABLE,
            scope=ErrorScope.TENANT,
            http_status=503,
            retry_after_seconds=5,
            tags=("resource", "concurrency"),
        ))

        # Configuration
        self.register(ErrorCode(
            code="CONFIGURATION_ERROR",
            message="Configuration error",
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            recoverability=ErrorRecoverability.MANUAL,
            scope=ErrorScope.GLOBAL,
            http_status=500,
            alert_threshold=1,
            tags=("config",),
        ))
        self.register(ErrorCode(
            code="INVALID_CONFIGURATION",
            message="Invalid configuration",
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            recoverability=ErrorRecoverability.MANUAL,
            scope=ErrorScope.GLOBAL,
            http_status=500,
            alert_threshold=1,
            tags=("config", "invalid"),
        ))
        self.register(ErrorCode(
            code="MISSING_CONFIGURATION",
            message="Missing required configuration",
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            recoverability=ErrorRecoverability.MANUAL,
            scope=ErrorScope.GLOBAL,
            http_status=500,
            alert_threshold=1,
            tags=("config", "missing"),
        ))

        # Policy
        self.register(ErrorCode(
            code="POLICY_COMPILATION_FAILED",
            message="Policy compilation failed",
            category=ErrorCategory.POLICY,
            severity=ErrorSeverity.MEDIUM,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.RESOURCE,
            http_status=422,
            tags=("policy", "compilation"),
        ))
        self.register(ErrorCode(
            code="POLICY_EVALUATION_FAILED",
            message="Policy evaluation failed",
            category=ErrorCategory.POLICY,
            severity=ErrorSeverity.HIGH,
            recoverability=ErrorRecoverability.FALLBACK,
            scope=ErrorScope.REQUEST,
            http_status=500,
            tags=("policy", "evaluation"),
        ))
        self.register(ErrorCode(
            code="POLICY_CONFLICT",
            message="Policy conflict detected",
            category=ErrorCategory.POLICY,
            severity=ErrorSeverity.MEDIUM,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.RESOURCE,
            http_status=409,
            tags=("policy", "conflict"),
        ))
        self.register(ErrorCode(
            code="POLICY_VERSION_MISMATCH",
            message="Policy version mismatch",
            category=ErrorCategory.POLICY,
            severity=ErrorSeverity.MEDIUM,
            recoverability=ErrorRecoverability.RETRYABLE,
            scope=ErrorScope.RESOURCE,
            http_status=409,
            retry_after_seconds=1,
            tags=("policy", "version"),
        ))

        # Workflow
        self.register(ErrorCode(
            code="WORKFLOW_EXECUTION_FAILED",
            message="Workflow execution failed",
            category=ErrorCategory.WORKFLOW,
            severity=ErrorSeverity.HIGH,
            recoverability=ErrorRecoverability.MANUAL,
            scope=ErrorScope.WORKFLOW,
            http_status=500,
            alert_threshold=5,
            tags=("workflow", "execution"),
        ))
        self.register(ErrorCode(
            code="WORKFLOW_STEP_FAILED",
            message="Workflow step failed",
            category=ErrorCategory.WORKFLOW,
            severity=ErrorSeverity.MEDIUM,
            recoverability=ErrorRecoverability.RETRYABLE,
            scope=ErrorScope.WORKFLOW,
            http_status=500,
            retry_after_seconds=5,
            tags=("workflow", "step"),
        ))
        self.register(ErrorCode(
            code="WORKFLOW_CANCELLED",
            message="Workflow was cancelled",
            category=ErrorCategory.WORKFLOW,
            severity=ErrorSeverity.LOW,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.WORKFLOW,
            http_status=499,
            tags=("workflow", "cancelled"),
        ))
        self.register(ErrorCode(
            code="WORKFLOW_DEADLINE_EXCEEDED",
            message="Workflow deadline exceeded",
            category=ErrorCategory.WORKFLOW,
            severity=ErrorSeverity.HIGH,
            recoverability=ErrorRecoverability.MANUAL,
            scope=ErrorScope.WORKFLOW,
            http_status=408,
            tags=("workflow", "deadline"),
        ))

        # Data
        self.register(ErrorCode(
            code="DATA_INTEGRITY_ERROR",
            message="Data integrity error",
            category=ErrorCategory.DATA,
            severity=ErrorSeverity.CRITICAL,
            recoverability=ErrorRecoverability.MANUAL,
            scope=ErrorScope.GLOBAL,
            http_status=500,
            alert_threshold=1,
            tags=("data", "integrity"),
        ))
        self.register(ErrorCode(
            code="DATA_VALIDATION_FAILED",
            message="Data validation failed",
            category=ErrorCategory.DATA,
            severity=ErrorSeverity.MEDIUM,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.RESOURCE,
            http_status=422,
            tags=("data", "validation"),
        ))
        self.register(ErrorCode(
            code="DATA_TRANSFORMATION_FAILED",
            message="Data transformation failed",
            category=ErrorCategory.DATA,
            severity=ErrorSeverity.MEDIUM,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.RESOURCE,
            http_status=422,
            tags=("data", "transformation"),
        ))
        self.register(ErrorCode(
            code="DATA_MIGRATION_FAILED",
            message="Data migration failed",
            category=ErrorCategory.DATA,
            severity=ErrorSeverity.CRITICAL,
            recoverability=ErrorRecoverability.MANUAL,
            scope=ErrorScope.GLOBAL,
            http_status=500,
            alert_threshold=1,
            tags=("data", "migration"),
        ))

        # Security
        self.register(ErrorCode(
            code="SECURITY_VIOLATION",
            message="Security violation detected",
            category=ErrorCategory.SECURITY,
            severity=ErrorSeverity.CRITICAL,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.GLOBAL,
            http_status=403,
            alert_threshold=1,
            tags=("security", "violation"),
        ))
        self.register(ErrorCode(
            code="SUSPICIOUS_ACTIVITY",
            message="Suspicious activity detected",
            category=ErrorCategory.SECURITY,
            severity=ErrorSeverity.HIGH,
            recoverability=ErrorRecoverability.MANUAL,
            scope=ErrorScope.USER,
            http_status=403,
            alert_threshold=3,
            tags=("security", "suspicious"),
        ))
        self.register(ErrorCode(
            code="CSRF_TOKEN_INVALID",
            message="CSRF token invalid",
            category=ErrorCategory.SECURITY,
            severity=ErrorSeverity.MEDIUM,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.REQUEST,
            http_status=403,
            tags=("security", "csrf"),
        ))
        self.register(ErrorCode(
            code="ENCRYPTION_FAILED",
            message="Encryption operation failed",
            category=ErrorCategory.SECURITY,
            severity=ErrorSeverity.CRITICAL,
            recoverability=ErrorRecoverability.NON_RECOVERABLE,
            scope=ErrorScope.GLOBAL,
            http_status=500,
            alert_threshold=1,
            tags=("security", "encryption"),
        ))

        # Dependency
        self.register(ErrorCode(
            code="DEPENDENCY_UNAVAILABLE",
            message="Required dependency is unavailable",
            category=ErrorCategory.DEPENDENCY,
            severity=ErrorSeverity.HIGH,
            recoverability=ErrorRecoverability.CIRCUIT_BREAK,
            scope=ErrorScope.GLOBAL,
            http_status=503,
            retry_after_seconds=30,
            alert_threshold=5,
            tags=("dependency",),
        ))
        self.register(ErrorCode(
            code="DEPENDENCY_TIMEOUT",
            message="Dependency call timed out",
            category=ErrorCategory.DEPENDENCY,
            severity=ErrorSeverity.HIGH,
            recoverability=ErrorRecoverability.CIRCUIT_BREAK,
            scope=ErrorScope.GLOBAL,
            http_status=504,
            retry_after_seconds=5,
            alert_threshold=10,
            tags=("dependency", "timeout"),
        ))
        self.register(ErrorCode(
            code="DEPENDENCY_VERSION_MISMATCH",
            message="Dependency version mismatch",
            category=ErrorCategory.DEPENDENCY,
            severity=ErrorSeverity.MEDIUM,
            recoverability=ErrorRecoverability.MANUAL,
            scope=ErrorScope.GLOBAL,
            http_status=500,
            tags=("dependency", "version"),
        ))

    def register(self, error_code: ErrorCode) -> None:
        """Register a new error code.

        Args:
            error_code: The ErrorCode to register.

        Raises:
            ValueError: If the code is already registered.
        """
        if error_code.code in self._codes:
            raise ValueError(f"Error code '{error_code.code}' is already registered")
        self._codes[error_code.code] = error_code

    def get(self, code: str) -> ErrorCode | None:
        """Get an error code by its string identifier.

        Args:
            code: The error code string.

        Returns:
            The ErrorCode if found, None otherwise.
        """
        return self._codes.get(code)

    def get_or_create(self, code: str) -> ErrorCode:
        """Get an error code, creating a default one if not registered.

        Args:
            code: The error code string.

        Returns:
            The ErrorCode (existing or newly created).
        """
        if code in self._codes:
            return self._codes[code]
        return ErrorCode.from_code_string(code)

    def list_codes(
        self,
        category: ErrorCategory | None = None,
        severity: ErrorSeverity | None = None,
    ) -> list[ErrorCode]:
        """List all registered error codes, optionally filtered.

        Args:
            category: Filter by category.
            severity: Filter by severity.

        Returns:
            List of matching ErrorCodes.
        """
        codes = list(self._codes.values())
        if category is not None:
            codes = [c for c in codes if c.category == category]
        if severity is not None:
            codes = [c for c in codes if c.severity == severity]
        return codes

    def is_registered(self, code: str) -> bool:
        """Check if an error code is registered."""
        return code in self._codes

    def to_dict(self) -> dict[str, Any]:
        """Export the entire registry as a dictionary."""
        return {
            "total_codes": len(self._codes),
            "codes": {code: ec.to_dict() for code, ec in self._codes.items()},
        }


# Singleton instance
_registry = ErrorRegistry()


def get_error_code(code: str) -> ErrorCode:
    """Get an error code from the global registry.

    Args:
        code: The error code string.

    Returns:
        The ErrorCode (existing or auto-created from taxonomy).
    """
    return _registry.get_or_create(code)


def register_error_code(error_code: ErrorCode) -> None:
    """Register a new error code in the global registry.

    Args:
        error_code: The ErrorCode to register.
    """
    _registry.register(error_code)


def get_registry() -> ErrorRegistry:
    """Get the global error registry instance."""
    return _registry
