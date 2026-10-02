"""
Custom exceptions for rate limiting and quota management.
"""

from __future__ import annotations

from typing import Optional


class RateLimitError(Exception):
    """Base exception for rate limiting errors."""
    pass


class RateLimitExceeded(RateLimitError):
    """Raised when a rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int = 30,
        limit: int = 1000,
        remaining: int = 0,
        policy_name: str = "default",
    ):
        self.message = message
        self.retry_after = retry_after
        self.limit = limit
        self.remaining = remaining
        self.policy_name = policy_name
        super().__init__(message)

    def to_dict(self) -> dict:
        return {
            "error": "RATE_LIMIT_EXCEEDED",
            "message": self.message,
            "retry_after": self.retry_after,
            "limit": self.limit,
            "remaining": self.remaining,
            "policy": self.policy_name,
        }


class QuotaError(Exception):
    """Base exception for quota errors."""
    pass


class QuotaExceeded(QuotaError):
    """Raised when a quota is exceeded."""

    def __init__(
        self,
        message: str = "Quota exceeded",
        quota_name: str = "",
        limit: float = 0,
        used: float = 0,
        remaining: float = 0,
        reset_at: str = "",
    ):
        self.message = message
        self.quota_name = quota_name
        self.limit = limit
        self.used = used
        self.remaining = remaining
        self.reset_at = reset_at
        super().__init__(message)

    def to_dict(self) -> dict:
        return {
            "error": "QUOTA_EXCEEDED",
            "message": self.message,
            "quota_name": self.quota_name,
            "limit": self.limit,
            "used": self.used,
            "remaining": self.remaining,
            "reset_at": self.reset_at,
        }


class QuotaNotFoundError(QuotaError):
    """Raised when a quota is not found."""

    def __init__(self, quota_name: str, tenant_id: str = ""):
        self.quota_name = quota_name
        self.tenant_id = tenant_id
        message = f"Quota '{quota_name}' not found"
        if tenant_id:
            message += f" for tenant '{tenant_id}'"
        super().__init__(message)


class RateLimitConfigError(RateLimitError):
    """Raised when rate limit configuration is invalid."""

    def __init__(self, message: str = "Invalid rate limit configuration"):
        super().__init__(message)
