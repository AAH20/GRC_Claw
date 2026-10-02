"""
GRC_Claw Unified Error Handling Framework

Provides a comprehensive error handling system including:
- Error taxonomy and classification
- Standardized error codes registry
- FastAPI error handling middleware
- Error recovery strategies (retry, circuit breaker, fallback)
- Error reporting and analytics
"""

from .taxonomy import (
    ErrorCategory,
    ErrorSeverity,
    ErrorRecoverability,
    ErrorScope,
    ErrorClassification,
    classify_error,
)
from .codes import ErrorCode, ErrorRegistry, get_error_code, register_error_code
from .middleware import ErrorHandlingMiddleware, setup_error_handling
from .recovery import (
    RecoveryStrategy,
    RetryStrategy,
    CircuitBreaker,
    FallbackStrategy,
    RecoveryManager,
    CircuitBreakerState,
)
from .reporting import (
    ErrorReporter,
    ErrorMetrics,
    ErrorAnalytics,
    AlertRule,
    ErrorTrend,
)

__all__ = [
    # Taxonomy
    "ErrorCategory",
    "ErrorSeverity",
    "ErrorRecoverability",
    "ErrorScope",
    "ErrorClassification",
    "classify_error",
    # Codes
    "ErrorCode",
    "ErrorRegistry",
    "get_error_code",
    "register_error_code",
    # Middleware
    "ErrorHandlingMiddleware",
    "setup_error_handling",
    # Recovery
    "RecoveryStrategy",
    "RetryStrategy",
    "CircuitBreaker",
    "FallbackStrategy",
    "RecoveryManager",
    "CircuitBreakerState",
    # Reporting
    "ErrorReporter",
    "ErrorMetrics",
    "ErrorAnalytics",
    "AlertRule",
    "ErrorTrend",
]
