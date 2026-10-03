"""Token bucket rate limiter for the Recruitment Platform SDK.

Provides both synchronous and asynchronous token bucket rate limiters
that can be used to throttle API requests.
"""

from __future__ import annotations

import asyncio
import time
from threading import Lock


class TokenBucketRateLimiter:
    """Synchronous token bucket rate limiter.

    The token bucket algorithm refills tokens at a fixed rate. Each request
    consumes one token. If no tokens are available, the request must wait.

    Args:
        rate: Token refill rate in tokens per second.
        capacity: Maximum number of tokens the bucket can hold.

    Example:
        >>> limiter = TokenBucketRateLimiter(rate=10, capacity=100)
        >>> limiter.acquire()  # Returns True if token available
        True
    """

    def __init__(self, rate: float, capacity: int) -> None:
        """Initialize the token bucket rate limiter.

        Args:
            rate: Token refill rate in tokens per second.
            capacity: Maximum number of tokens the bucket can hold.

        Raises:
            ValueError: If rate or capacity is not positive.
        """
        if rate <= 0:
            raise ValueError("Rate must be positive")
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        self._rate: float = rate
        self._capacity: int = capacity
        self._tokens: float = float(capacity)
        self._last_refill: float = time.monotonic()
        self._lock: Lock = Lock()

    @property
    def rate(self) -> float:
        """Token refill rate in tokens per second."""
        return self._rate

    @property
    def capacity(self) -> int:
        """Maximum bucket capacity."""
        return self._capacity

    @property
    def tokens(self) -> float:
        """Current number of available tokens."""
        with self._lock:
            self._refill()
            return self._tokens

    def _refill(self) -> None:
        """Refill tokens based on elapsed time. Must be called with lock held."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
        self._last_refill = now

    def acquire(
        self, tokens: int = 1, blocking: bool = False, timeout: float | None = None
    ) -> bool:
        """Acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire.
            blocking: If True, block until tokens are available.
            timeout: Maximum time to wait in seconds (None = forever).

        Returns:
            True if tokens were acquired, False otherwise.
        """
        if blocking:
            return self._acquire_blocking(tokens, timeout)
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def _acquire_blocking(self, tokens: int, timeout: float | None) -> bool:
        """Blocking token acquisition with optional timeout.

        Args:
            tokens: Number of tokens to acquire.
            timeout: Maximum time to wait in seconds (None = forever).

        Returns:
            True if tokens were acquired, False if timeout exceeded.
        """
        start = time.monotonic()
        while True:
            with self._lock:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True
                wait = (tokens - self._tokens) / self._rate
            if timeout is not None:
                elapsed = time.monotonic() - start
                if elapsed + wait > timeout:
                    return False
            time.sleep(min(wait, 0.1))

    def wait_time(self, tokens: int = 1) -> float:
        """Calculate wait time for the requested tokens.

        Args:
            tokens: Number of tokens needed.

        Returns:
            Estimated wait time in seconds.
        """
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                return 0.0
            return (tokens - self._tokens) / self._rate

    def reset(self) -> None:
        """Reset the bucket to full capacity."""
        with self._lock:
            self._tokens = float(self._capacity)
            self._last_refill = time.monotonic()


class AsyncTokenBucketRateLimiter:
    """Asynchronous token bucket rate limiter.

    Same algorithm as TokenBucketRateLimiter but uses asyncio locks
    for use in async/await contexts.

    Args:
        rate: Token refill rate in tokens per second.
        capacity: Maximum number of tokens the bucket can hold.

    Example:
        >>> limiter = AsyncTokenBucketRateLimiter(rate=10, capacity=100)
        >>> await limiter.acquire()  # Returns True if token available
        True
    """

    def __init__(self, rate: float, capacity: int) -> None:
        """Initialize the async token bucket rate limiter.

        Args:
            rate: Token refill rate in tokens per second.
            capacity: Maximum number of tokens the bucket can hold.

        Raises:
            ValueError: If rate or capacity is not positive.
        """
        if rate <= 0:
            raise ValueError("Rate must be positive")
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        self._rate: float = rate
        self._capacity: int = capacity
        self._tokens: float = float(capacity)
        self._last_refill: float = time.monotonic()
        self._lock: asyncio.Lock = asyncio.Lock()

    @property
    def rate(self) -> float:
        """Token refill rate in tokens per second."""
        return self._rate

    @property
    def capacity(self) -> int:
        """Maximum bucket capacity."""
        return self._capacity

    @property
    def tokens(self) -> float:
        """Current number of available tokens."""
        self._refill_sync()
        return self._tokens

    def _refill_sync(self) -> None:
        """Synchronous refill for property access."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
        self._last_refill = now

    async def _refill(self) -> None:
        """Async refill for use within lock."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
        self._last_refill = now

    async def acquire(
        self, tokens: int = 1, blocking: bool = False, timeout: float | None = None
    ) -> bool:
        """Acquire tokens from the bucket asynchronously.

        Args:
            tokens: Number of tokens to acquire.
            blocking: If True, block until tokens are available.
            timeout: Maximum time to wait in seconds (None = forever).

        Returns:
            True if tokens were acquired, False otherwise.
        """
        if blocking:
            return await self._acquire_blocking(tokens, timeout)
        async with self._lock:
            await self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    async def _acquire_blocking(self, tokens: int, timeout: float | None) -> bool:
        """Blocking token acquisition with optional timeout.

        Args:
            tokens: Number of tokens to acquire.
            timeout: Maximum time to wait in seconds (None = forever).

        Returns:
            True if tokens were acquired, False if timeout exceeded.
        """
        start = time.monotonic()
        while True:
            async with self._lock:
                await self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True
                wait = (tokens - self._tokens) / self._rate
            if timeout is not None:
                elapsed = time.monotonic() - start
                if elapsed + wait > timeout:
                    return False
            await asyncio.sleep(min(wait, 0.1))

    async def wait_time(self, tokens: int = 1) -> float:
        """Calculate wait time for the requested tokens.

        Args:
            tokens: Number of tokens needed.

        Returns:
            Estimated wait time in seconds.
        """
        async with self._lock:
            await self._refill()
            if self._tokens >= tokens:
                return 0.0
            return (tokens - self._tokens) / self._rate

    async def reset(self) -> None:
        """Reset the bucket to full capacity."""
        async with self._lock:
            self._tokens = float(self._capacity)
            self._last_refill = time.monotonic()
