"""Error Handler Agent.

Handles and recovers from errors during workflow execution, providing
retry logic, fallback strategies, and error reporting.
"""

from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Enumeration of error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Enumeration of error categories."""

    VALIDATION = "validation"
    TIMEOUT = "timeout"
    DEPENDENCY = "dependency"
    DOMAIN_UNAVAILABLE = "domain_unavailable"
    INTERNAL = "internal"
    UNKNOWN = "unknown"


class ErrorRecord(BaseModel):
    """Record of an error that occurred during execution.

    Attributes:
        id: Unique error identifier.
        category: Error category.
        severity: Error severity level.
        message: Error message.
        step_id: ID of the step where the error occurred.
        workflow_id: ID of the workflow where the error occurred.
        timestamp: When the error occurred.
        resolved: Whether the error has been resolved.
        resolution: Description of how the error was resolved.
    """

    id: str = Field(default_factory=lambda: str(uuid4()), description="Error identifier")
    category: ErrorCategory = Field(..., description="Error category")
    severity: ErrorSeverity = Field(..., description="Error severity")
    message: str = Field(..., description="Error message")
    step_id: str | None = Field(default=None, description="Step identifier")
    workflow_id: str | None = Field(default=None, description="Workflow identifier")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp",
    )
    resolved: bool = Field(default=False, description="Whether error is resolved")
    resolution: str | None = Field(default=None, description="Resolution description")


class ErrorHandlerAgent:
    """Agent responsible for handling and recovering from errors.

    Provides error classification, retry logic, fallback strategies,
    and comprehensive error reporting.

    Attributes:
        error_log: Log of all encountered errors.
        retry_policies: Configured retry policies per error category.
        fallback_strategies: Configured fallback strategies.
    """

    def __init__(self) -> None:
        """Initialize the Error Handler Agent."""
        self.error_log: list[ErrorRecord] = []
        self.retry_policies: dict[ErrorCategory, dict[str, Any]] = {
            ErrorCategory.VALIDATION: {"max_retries": 0, "backoff_factor": 0},
            ErrorCategory.TIMEOUT: {"max_retries": 3, "backoff_factor": 1.5},
            ErrorCategory.DEPENDENCY: {"max_retries": 2, "backoff_factor": 2.0},
            ErrorCategory.DOMAIN_UNAVAILABLE: {"max_retries": 3, "backoff_factor": 1.0},
            ErrorCategory.INTERNAL: {"max_retries": 1, "backoff_factor": 1.0},
            ErrorCategory.UNKNOWN: {"max_retries": 1, "backoff_factor": 1.0},
        }
        self.fallback_strategies: dict[ErrorCategory, str] = {
            ErrorCategory.VALIDATION: "reject",
            ErrorCategory.TIMEOUT: "retry",
            ErrorCategory.DEPENDENCY: "skip",
            ErrorCategory.DOMAIN_UNAVAILABLE: "failover",
            ErrorCategory.INTERNAL: "abort",
            ErrorCategory.UNKNOWN: "abort",
        }

    def classify_error(self, error: Exception) -> tuple[ErrorCategory, ErrorSeverity]:
        """Classify an exception into category and severity.

        Args:
            error: The exception to classify.

        Returns:
            Tuple of (category, severity).
        """
        error_name = type(error).__name__.lower()
        error_msg = str(error).lower()

        if "timeout" in error_name or "timeout" in error_msg:
            return ErrorCategory.TIMEOUT, ErrorSeverity.MEDIUM
        if "validation" in error_name or "invalid" in error_msg:
            return ErrorCategory.VALIDATION, ErrorSeverity.LOW
        if "connection" in error_name or "unavailable" in error_msg:
            return ErrorCategory.DOMAIN_UNAVAILABLE, ErrorSeverity.HIGH
        if "dependency" in error_name or "dependency" in error_msg:
            return ErrorCategory.DEPENDENCY, ErrorSeverity.MEDIUM

        return ErrorCategory.INTERNAL, ErrorSeverity.HIGH

    def handle_error(
        self,
        error: Exception,
        step_id: str | None = None,
        workflow_id: str | None = None,
    ) -> ErrorRecord:
        """Handle an error by classifying and logging it.

        Args:
            error: The exception to handle.
            step_id: Optional step identifier.
            workflow_id: Optional workflow identifier.

        Returns:
            The created error record.
        """
        category, severity = self.classify_error(error)

        record = ErrorRecord(
            category=category,
            severity=severity,
            message=str(error),
            step_id=step_id,
            workflow_id=workflow_id,
        )

        self.error_log.append(record)
        logger.error(
            "Error occurred: [%s] %s (severity=%s, step=%s, workflow=%s)",
            record.id,
            record.message,
            severity.value,
            step_id,
            workflow_id,
        )

        return record

    def should_retry(self, category: ErrorCategory) -> bool:
        """Determine if an error category should be retried.

        Args:
            category: The error category.

        Returns:
            True if the error should be retried.
        """
        return self.retry_policies[category]["max_retries"] > 0

    def get_retry_delay(self, category: ErrorCategory, attempt: int) -> float:
        """Calculate the delay before a retry attempt.

        Args:
            category: The error category.
            attempt: The current attempt number (0-indexed).

        Returns:
            Delay in seconds.
        """
        policy = self.retry_policies[category]
        return policy["backoff_factor"] ** attempt

    def get_fallback_strategy(self, category: ErrorCategory) -> str:
        """Get the fallback strategy for an error category.

        Args:
            category: The error category.

        Returns:
            Fallback strategy name.
        """
        return self.fallback_strategies.get(category, "abort")

    def resolve_error(self, error_id: str, resolution: str) -> bool:
        """Mark an error as resolved.

        Args:
            error_id: The error identifier.
            resolution: Description of the resolution.

        Returns:
            True if the error was found and resolved.
        """
        for record in self.error_log:
            if record.id == error_id:
                record.resolved = True
                record.resolution = resolution
                logger.info("Error %s resolved: %s", error_id, resolution)
                return True
        return False

    def get_error_summary(self) -> dict[str, Any]:
        """Get a summary of all errors.

        Returns:
            Error summary dictionary.
        """
        total = len(self.error_log)
        resolved = sum(1 for e in self.error_log if e.resolved)
        by_category: dict[str, int] = {}
        by_severity: dict[str, int] = {}

        for record in self.error_log:
            cat = record.category.value
            sev = record.severity.value
            by_category[cat] = by_category.get(cat, 0) + 1
            by_severity[sev] = by_severity.get(sev, 0) + 1

        return {
            "total_errors": total,
            "resolved_errors": resolved,
            "unresolved_errors": total - resolved,
            "by_category": by_category,
            "by_severity": by_severity,
        }
