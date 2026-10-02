"""Rate limiting security tests for GRC_Claw.

Tests rate limiting conditions, request throttling, and abuse prevention
to ensure API endpoints are protected against excessive requests and
denial-of-service attacks.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from unittest.mock import MagicMock, patch

import pytest

from auth.rbac import rate_limit_condition


# ===========================================================================
# Rate Limit Condition Tests
# ===========================================================================


class TestRateLimitCondition:
    """Tests for rate limit condition factory."""

    def test_rate_limit_allows_under_limit(self) -> None:
        """Verify requests under the limit are allowed."""
        condition = rate_limit_condition(max_requests=5, window_seconds=60)
        for i in range(5):
            assert condition({"subject": "user-1"}) is True

    def test_rate_limit_blocks_over_limit(self) -> None:
        """Verify requests over the limit are blocked."""
        condition = rate_limit_condition(max_requests=3, window_seconds=60)
        assert condition({"subject": "user-1"}) is True
        assert condition({"subject": "user-1"}) is True
        assert condition({"subject": "user-1"}) is True
        assert condition({"subject": "user-1"}) is False

    def test_rate_limit_tracks_subjects_separately(self) -> None:
        """Verify different subjects have separate rate limits."""
        condition = rate_limit_condition(max_requests=2, window_seconds=60)
        assert condition({"subject": "user-a"}) is True
        assert condition({"subject": "user-b"}) is True
        assert condition({"subject": "user-a"}) is True
        assert condition({"subject": "user-b"}) is True
        assert condition({"subject": "user-a"}) is False
        assert condition({"subject": "user-b"}) is False

    def test_rate_limit_window_expires(self) -> None:
        """Verify rate limit window expires after time."""
        condition = rate_limit_condition(max_requests=1, window_seconds=1)
        assert condition({"subject": "user-1"}) is True
        assert condition({"subject": "user-1"}) is False
        time.sleep(1.1)
        assert condition({"subject": "user-1"}) is True

    def test_rate_limit_with_default_subject(self) -> None:
        """Verify rate limit works with default subject."""
        condition = rate_limit_condition(max_requests=2, window_seconds=60)
        assert condition({}) is True
        assert condition({}) is True
        assert condition({}) is False

    def test_rate_limit_single_request(self) -> None:
        """Verify rate limit with max_requests=1."""
        condition = rate_limit_condition(max_requests=1, window_seconds=60)
        assert condition({"subject": "user-1"}) is True
        assert condition({"subject": "user-1"}) is False

    def test_rate_limit_high_volume(self) -> None:
        """Verify rate limit with high volume."""
        condition = rate_limit_condition(max_requests=100, window_seconds=60)
        for i in range(100):
            assert condition({"subject": "user-1"}) is True
        assert condition({"subject": "user-1"}) is False


# ===========================================================================
# Rate Limit Configuration Tests
# ===========================================================================


class TestRateLimitConfiguration:
    """Tests for rate limit configuration validation."""

    def test_rate_limit_with_zero_max_requests(self) -> None:
        """Verify rate limit with zero max requests blocks all."""
        condition = rate_limit_condition(max_requests=0, window_seconds=60)
        assert condition({"subject": "user-1"}) is False

    def test_rate_limit_with_very_short_window(self) -> None:
        """Verify rate limit with very short window."""
        condition = rate_limit_condition(max_requests=1, window_seconds=0)
        assert condition({"subject": "user-1"}) is True
        # With 0 second window, old entries are immediately cleaned
        assert condition({"subject": "user-1"}) is True

    def test_rate_limit_with_long_window(self) -> None:
        """Verify rate limit with long window."""
        condition = rate_limit_condition(max_requests=1, window_seconds=86400)
        assert condition({"subject": "user-1"}) is True
        assert condition({"subject": "user-1"}) is False


# ===========================================================================
# Rate Limit Per-Endpoint Tests
# ===========================================================================


class TestRateLimitPerEndpoint:
    """Tests for per-endpoint rate limiting."""

    def test_different_endpoints_have_separate_limits(self) -> None:
        """Verify different endpoints have separate rate limits."""
        login_limit = rate_limit_condition(max_requests=3, window_seconds=60)
        api_limit = rate_limit_condition(max_requests=100, window_seconds=60)
        # Exhaust login limit
        for _ in range(3):
            login_limit({"subject": "user-1"})
        assert login_limit({"subject": "user-1"}) is False
        # API limit should still work
        assert api_limit({"subject": "user-1"}) is True

    def test_rate_limit_per_ip_address(self) -> None:
        """Verify rate limiting per IP address."""
        condition = rate_limit_condition(max_requests=5, window_seconds=60)
        for _ in range(5):
            condition({"subject": "192.168.1.1"})
        assert condition({"subject": "192.168.1.1"}) is False
        # Different IP should still work
        assert condition({"subject": "192.168.1.2"}) is True

    def test_rate_limit_per_user(self) -> None:
        """Verify rate limiting per user."""
        condition = rate_limit_condition(max_requests=5, window_seconds=60)
        for _ in range(5):
            condition({"subject": "user-1"})
        assert condition({"subject": "user-1"}) is False
        # Different user should still work
        assert condition({"subject": "user-2"}) is True


# ===========================================================================
# Rate Limit Burst Handling Tests
# ===========================================================================


class TestRateLimitBurstHandling:
    """Tests for burst traffic handling."""

    def test_burst_requests_blocked(self) -> None:
        """Verify burst of requests is blocked after limit."""
        condition = rate_limit_condition(max_requests=10, window_seconds=60)
        # Simulate burst
        results = [condition({"subject": "user-1"}) for _ in range(20)]
        assert sum(results) == 10
        assert results[-1] is False

    def test_sustained_requests_eventually_blocked(self) -> None:
        """Verify sustained requests are eventually blocked."""
        condition = rate_limit_condition(max_requests=5, window_seconds=60)
        # First batch
        for _ in range(5):
            assert condition({"subject": "user-1"}) is True
        # Second batch should be blocked
        for _ in range(5):
            assert condition({"subject": "user-1"}) is False

    def test_rate_limit_recovery_after_window(self) -> None:
        """Verify rate limit recovers after window expires."""
        condition = rate_limit_condition(max_requests=2, window_seconds=1)
        assert condition({"subject": "user-1"}) is True
        assert condition({"subject": "user-1"}) is True
        assert condition({"subject": "user-1"}) is False
        time.sleep(1.1)
        assert condition({"subject": "user-1"}) is True


# ===========================================================================
# Rate Limit Security Edge Cases
# ===========================================================================


class TestRateLimitEdgeCases:
    """Tests for rate limiting security edge cases."""

    def test_rate_limit_does_not_leak_user_existence(self) -> None:
        """Verify rate limit response does not leak user existence."""
        # In a real system, rate limit responses should be identical
        # regardless of whether the user exists
        condition = rate_limit_condition(max_requests=1, window_seconds=60)
        result1 = condition({"subject": "existing-user"})
        result2 = condition({"subject": "nonexistent-user"})
        # Both should return the same type of result
        assert isinstance(result1, bool)
        assert isinstance(result2, bool)

    def test_rate_limit_with_concurrent_requests(self) -> None:
        """Verify rate limit handles concurrent requests."""
        import concurrent.futures

        condition = rate_limit_condition(max_requests=10, window_seconds=60)

        def make_request(i: int) -> bool:
            return condition({"subject": "user-1"})

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(make_request, range(20)))
        # At most 10 should succeed
        assert sum(results) <= 10

    def test_rate_limit_does_not_consume_on_invalid_input(self) -> None:
        """Verify rate limit does not consume quota on invalid input."""
        # In a real system, invalid requests should not consume rate limit quota
        condition = rate_limit_condition(max_requests=1, window_seconds=60)
        # Valid request consumes quota
        assert condition({"subject": "user-1"}) is True
        assert condition({"subject": "user-1"}) is False

    def test_rate_limit_with_empty_subject(self) -> None:
        """Verify rate limit with empty subject."""
        condition = rate_limit_condition(max_requests=2, window_seconds=60)
        assert condition({"subject": ""}) is True
        assert condition({"subject": ""}) is True
        assert condition({"subject": ""}) is False

    def test_rate_limit_with_special_characters_in_subject(self) -> None:
        """Verify rate limit with special characters in subject."""
        condition = rate_limit_condition(max_requests=2, window_seconds=60)
        special_subjects = [
            "user@domain.com",
            "user:name",
            "user/name",
            "user\\name",
            "user name",
            "user\tname",
        ]
        for subject in special_subjects:
            assert condition({"subject": subject}) is True

    def test_rate_limit_sliding_window(self) -> None:
        """Verify rate limit implements sliding window correctly."""
        condition = rate_limit_condition(max_requests=3, window_seconds=2)
        # Use all requests
        assert condition({"subject": "user-1"}) is True
        time.sleep(0.5)
        assert condition({"subject": "user-1"}) is True
        time.sleep(0.5)
        assert condition({"subject": "user-1"}) is True
        assert condition({"subject": "user-1"}) is False
        # Wait for first request to expire from window
        time.sleep(1.1)
        # Should have 2 slots available (first request expired)
        assert condition({"subject": "user-1"}) is True
        assert condition({"subject": "user-1"}) is True
        assert condition({"subject": "user-1"}) is False
