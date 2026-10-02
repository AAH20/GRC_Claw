"""Custom exceptions for recruitment analytics."""

from __future__ import annotations


class RecruitmentAnalyticsError(Exception):
    """Base exception for recruitment analytics."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(self.message)


class AgentExecutionError(RecruitmentAnalyticsError):
    """Raised when an agent fails to execute."""

    def __init__(self, message: str, agent_name: str = "") -> None:
        self.agent_name = agent_name
        super().__init__(message, code="AGENT_EXECUTION_ERROR")


class ExternalAPIError(RecruitmentAnalyticsError):
    """Raised when an external API call fails."""

    def __init__(self, message: str, api_name: str = "", status_code: int = 0) -> None:
        self.api_name = api_name
        self.status_code = status_code
        super().__init__(message, code="EXTERNAL_API_ERROR")


class ValidationError(RecruitmentAnalyticsError):
    """Raised when input validation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="VALIDATION_ERROR")


class NotFoundError(RecruitmentAnalyticsError):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="NOT_FOUND")


class RateLimitError(RecruitmentAnalyticsError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded") -> None:
        super().__init__(message, code="RATE_LIMIT_EXCEEDED")
