"""Token bucket rate limiter for UGC Marketplace SDK."""

from __future__ import annotations

import asyncio
import threading
import time
from typing import Any


class TokenBucketRateLimiter:
    """Thread-safe token bucket rate limiter.

    Args:
        rate: Tokens added per second.
        capacity: Maximum number of tokens in the bucket.
    """

    def __init__(self, rate: float = 10.0, capacity: int = 10) -> None:
        self.rate = rate
        self.capacity = capacity
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(float(self.capacity), self._tokens + elapsed * self.rate)
        self._last_refill = now

    def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire.

        Returns:
            True if tokens were acquired, False otherwise.
        """
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def wait_time(self, tokens: int = 1) -> float:
        """Calculate wait time until enough tokens are available.

        Args:
            tokens: Number of tokens needed.

        Returns:
            Seconds to wait before enough tokens will be available.
        """
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                return 0.0
            return (tokens - self._tokens) / self.rate

    def __enter__(self) -> TokenBucketRateLimiter:
        return self

    def __exit__(self, *_: Any) -> None:
        pass


class AsyncTokenBucketRateLimiter:
    """Asyncio-safe token bucket rate limiter.

    Args:
        rate: Tokens added per second.
        capacity: Maximum number of tokens in the bucket.
    """

    def __init__(self, rate: float = 10.0, capacity: int = 10) -> None:
        self.rate = rate
        self.capacity = capacity
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(float(self.capacity), self._tokens + elapsed * self.rate)
        self._last_refill = now

    async def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire.

        Returns:
            True if tokens were acquired, False otherwise.
        """
        async with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    async def wait_time(self, tokens: int = 1) -> float:
        """Calculate wait time until enough tokens are available.

        Args:
            tokens: Number of tokens needed.

        Returns:
            Seconds to wait before enough tokens will be available.
        """
        async with self._lock:
            self._refill()
            if self._tokens >= tokens:
                return 0.0
            return (tokens - self._tokens) / self.rate
