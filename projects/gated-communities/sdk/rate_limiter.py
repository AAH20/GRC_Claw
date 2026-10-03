"""Token bucket rate limiter for the Gated Communities SDK.

Provides both synchronous and asynchronous token bucket rate limiting
to prevent exceeding API rate limits.
"""

from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import dataclass, field


@dataclass
class TokenBucket:
    """Thread-safe token bucket rate limiter.

    Args:
        rate: Tokens added per second.
        capacity: Maximum number of tokens the bucket can hold.
    """

    rate: float
    capacity: float
    _tokens: float = field(default=0.0, init=False)
    _last_refill: float = field(default_factory=time.monotonic, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    def __post_init__(self) -> None:
        self._tokens = self.capacity

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last_refill = now

    def acquire(self, tokens: float = 1.0, blocking: bool = True) -> bool:
        """Acquire tokens from the bucket.

        Args:
            tokens: Number of tokens to acquire.
            blocking: If True, block until tokens are available.

        Returns:
            True if tokens were acquired, False otherwise.
        """
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            if not blocking:
                return False
            # Calculate wait time
            needed = tokens - self._tokens
            wait_time = needed / self.rate
        time.sleep(wait_time)
        with self._lock:
            self._refill()
            self._tokens -= tokens
        return True

    @property
    def available_tokens(self) -> float:
        """Current number of available tokens."""
        with self._lock:
            self._refill()
            return self._tokens


@dataclass
class AsyncTokenBucket:
    """Asyncio-compatible token bucket rate limiter.

    Args:
        rate: Tokens added per second.
        capacity: Maximum number of tokens the bucket can hold.
    """

    rate: float
    capacity: float
    _tokens: float = field(default=0.0, init=False)
    _last_refill: float = field(default_factory=time.monotonic, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    def __post_init__(self) -> None:
        self._tokens = self.capacity

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
        self._last_refill = now

    async def acquire(self, tokens: float = 1.0) -> None:
        """Acquire tokens from the bucket, waiting if necessary.

        Args:
            tokens: Number of tokens to acquire.
        """
        while True:
            async with self._lock:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return
                needed = tokens - self._tokens
                wait_time = needed / self.rate
            await asyncio.sleep(wait_time)

    @property
    def available_tokens(self) -> float:
        """Current number of available tokens."""
        self._refill()
        return self._tokens


class RateLimiter:
    """High-level rate limiter with configurable presets.

    Args:
        requests_per_second: Maximum requests per second.
        burst_size: Maximum burst size (bucket capacity).
    """

    def __init__(
        self,
        requests_per_second: float = 10.0,
        burst_size: float = 20.0,
    ) -> None:
        self._bucket = TokenBucket(rate=requests_per_second, capacity=burst_size)

    def acquire(self) -> None:
        """Acquire a token, blocking if necessary."""
        self._bucket.acquire()

    @property
    def available_tokens(self) -> float:
        """Current number of available tokens."""
        return self._bucket.available_tokens


class AsyncRateLimiter:
    """Asyncio-compatible high-level rate limiter.

    Args:
        requests_per_second: Maximum requests per second.
        burst_size: Maximum burst size (bucket capacity).
    """

    def __init__(
        self,
        requests_per_second: float = 10.0,
        burst_size: float = 20.0,
    ) -> None:
        self._bucket = AsyncTokenBucket(rate=requests_per_second, capacity=burst_size)

    async def acquire(self) -> None:
        """Acquire a token, waiting if necessary."""
        await self._bucket.acquire()

    @property
    def available_tokens(self) -> float:
        """Current number of available tokens."""
        return self._bucket.available_tokens
