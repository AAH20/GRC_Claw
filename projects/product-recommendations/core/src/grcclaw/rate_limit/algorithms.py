"""
Rate limiting algorithms: Token Bucket, Sliding Window, Leaky Bucket, Fixed Window.

Each algorithm provides an `acquire` method that returns a RateLimitResult
indicating whether the request is allowed and the current rate limit status.
"""

from __future__ import annotations

import time
import threading
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Optional

from .models import RateLimitAlgorithm


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    allowed: bool
    limit: int
    remaining: int
    reset_at: int
    retry_after: Optional[int] = None
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET
    current_usage: float = 0.0
    window_start: float = 0.0


class RateLimiter(ABC):
    """Abstract base class for rate limiters."""

    def __init__(
        self,
        requests_per_second: float = 100.0,
        burst_size: int = 200,
        window_size: int = 60,
    ):
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        self.window_size = window_size

    @abstractmethod
    def acquire(self, key: str, tokens: int = 1) -> RateLimitResult:
        """Attempt to acquire tokens for the given key."""
        pass

    @abstractmethod
    def get_status(self, key: str) -> RateLimitResult:
        """Get current rate limit status for a key without consuming tokens."""
        pass

    @abstractmethod
    def reset(self, key: str) -> None:
        """Reset rate limit state for a key."""
        pass


class TokenBucketLimiter(RateLimiter):
    """
    Token Bucket rate limiter.

    Tokens are added to the bucket at a constant rate. Each request consumes
    one or more tokens. If insufficient tokens are available, the request is
    rejected. The bucket has a maximum capacity (burst size).
    """

    def __init__(
        self,
        requests_per_second: float = 100.0,
        burst_size: int = 200,
        window_size: int = 60,
    ):
        super().__init__(requests_per_second, burst_size, window_size)
        self._buckets: dict[str, dict] = {}
        self._lock = threading.Lock()

    def _get_bucket(self, key: str) -> dict:
        if key not in self._buckets:
            self._buckets[key] = {
                "tokens": float(self.burst_size),
                "last_refill": time.time(),
            }
        return self._buckets[key]

    def _refill(self, bucket: dict) -> None:
        now = time.time()
        elapsed = now - bucket["last_refill"]
        new_tokens = elapsed * self.requests_per_second
        bucket["tokens"] = min(self.burst_size, bucket["tokens"] + new_tokens)
        bucket["last_refill"] = now

    def acquire(self, key: str, tokens: int = 1) -> RateLimitResult:
        with self._lock:
            bucket = self._get_bucket(key)
            self._refill(bucket)

            if bucket["tokens"] >= tokens:
                bucket["tokens"] -= tokens
                remaining = int(bucket["tokens"])
                reset_at = int(time.time() + (self.burst_size - bucket["tokens"]) / self.requests_per_second)
                return RateLimitResult(
                    allowed=True,
                    limit=self.burst_size,
                    remaining=remaining,
                    reset_at=reset_at,
                    algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                    current_usage=self.burst_size - bucket["tokens"],
                    window_start=bucket["last_refill"],
                )
            else:
                retry_after = int((tokens - bucket["tokens"]) / self.requests_per_second) + 1
                return RateLimitResult(
                    allowed=False,
                    limit=self.burst_size,
                    remaining=0,
                    reset_at=int(time.time() + retry_after),
                    retry_after=retry_after,
                    algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                    current_usage=self.burst_size - bucket["tokens"],
                    window_start=bucket["last_refill"],
                )

    def get_status(self, key: str) -> RateLimitResult:
        with self._lock:
            bucket = self._get_bucket(key)
            self._refill(bucket)
            remaining = int(bucket["tokens"])
            reset_at = int(time.time() + (self.burst_size - bucket["tokens"]) / self.requests_per_second)
            return RateLimitResult(
                allowed=bucket["tokens"] >= 1,
                limit=self.burst_size,
                remaining=remaining,
                reset_at=reset_at,
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                current_usage=self.burst_size - bucket["tokens"],
                window_start=bucket["last_refill"],
            )

    def reset(self, key: str) -> None:
        with self._lock:
            if key in self._buckets:
                del self._buckets[key]


class SlidingWindowLimiter(RateLimiter):
    """
    Sliding Window rate limiter.

    Maintains a sliding window of request timestamps. The window slides
    continuously, providing smoother rate limiting than fixed windows.
    """

    def __init__(
        self,
        requests_per_second: float = 100.0,
        burst_size: int = 200,
        window_size: int = 60,
    ):
        super().__init__(requests_per_second, burst_size, window_size)
        self._windows: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def _clean_window(self, key: str, now: float) -> None:
        window = self._windows[key]
        cutoff = now - self.window_size
        while window and window[0] <= cutoff:
            window.popleft()

    def acquire(self, key: str, tokens: int = 1) -> RateLimitResult:
        with self._lock:
            now = time.time()
            self._clean_window(key, now)

            current_count = len(self._windows[key])
            limit = int(self.requests_per_second * self.window_size)

            if current_count + tokens <= limit:
                for _ in range(tokens):
                    self._windows[key].append(now)
                remaining = limit - current_count - tokens
                reset_at = int(now + self.window_size)
                return RateLimitResult(
                    allowed=True,
                    limit=limit,
                    remaining=remaining,
                    reset_at=reset_at,
                    algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                    current_usage=float(current_count + tokens),
                    window_start=now - self.window_size,
                )
            else:
                retry_after = int(self._windows[key][0] + self.window_size - now) + 1 if self._windows[key] else 1
                return RateLimitResult(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    reset_at=int(now + retry_after),
                    retry_after=max(1, retry_after),
                    algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                    current_usage=float(current_count),
                    window_start=now - self.window_size,
                )

    def get_status(self, key: str) -> RateLimitResult:
        with self._lock:
            now = time.time()
            self._clean_window(key, now)
            current_count = len(self._windows[key])
            limit = int(self.requests_per_second * self.window_size)
            remaining = max(0, limit - current_count)
            reset_at = int(now + self.window_size)
            return RateLimitResult(
                allowed=remaining > 0,
                limit=limit,
                remaining=remaining,
                reset_at=reset_at,
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                current_usage=float(current_count),
                window_start=now - self.window_size,
            )

    def reset(self, key: str) -> None:
        with self._lock:
            if key in self._windows:
                del self._windows[key]


class LeakyBucketLimiter(RateLimiter):
    """
    Leaky Bucket rate limiter.

    Requests are added to a bucket and processed at a constant rate (leaked).
    If the bucket overflows (exceeds capacity), the request is rejected.
    This provides a smooth, constant output rate.
    """

    def __init__(
        self,
        requests_per_second: float = 100.0,
        burst_size: int = 200,
        window_size: int = 60,
    ):
        super().__init__(requests_per_second, burst_size, window_size)
        self._buckets: dict[str, dict] = {}
        self._lock = threading.Lock()

    def _get_bucket(self, key: str) -> dict:
        if key not in self._buckets:
            self._buckets[key] = {
                "volume": 0.0,
                "last_leak": time.time(),
            }
        return self._buckets[key]

    def _leak(self, bucket: dict) -> None:
        now = time.time()
        elapsed = now - bucket["last_leak"]
        leaked = elapsed * self.requests_per_second
        bucket["volume"] = max(0.0, bucket["volume"] - leaked)
        bucket["last_leak"] = now

    def acquire(self, key: str, tokens: int = 1) -> RateLimitResult:
        with self._lock:
            bucket = self._get_bucket(key)
            self._leak(bucket)

            if bucket["volume"] + tokens <= self.burst_size:
                bucket["volume"] += tokens
                remaining = int(self.burst_size - bucket["volume"])
                reset_at = int(time.time() + bucket["volume"] / self.requests_per_second)
                return RateLimitResult(
                    allowed=True,
                    limit=self.burst_size,
                    remaining=remaining,
                    reset_at=reset_at,
                    algorithm=RateLimitAlgorithm.LEAKY_BUCKET,
                    current_usage=bucket["volume"],
                    window_start=bucket["last_leak"],
                )
            else:
                retry_after = int((bucket["volume"] + tokens - self.burst_size) / self.requests_per_second) + 1
                return RateLimitResult(
                    allowed=False,
                    limit=self.burst_size,
                    remaining=0,
                    reset_at=int(time.time() + retry_after),
                    retry_after=retry_after,
                    algorithm=RateLimitAlgorithm.LEAKY_BUCKET,
                    current_usage=bucket["volume"],
                    window_start=bucket["last_leak"],
                )

    def get_status(self, key: str) -> RateLimitResult:
        with self._lock:
            bucket = self._get_bucket(key)
            self._leak(bucket)
            remaining = int(self.burst_size - bucket["volume"])
            reset_at = int(time.time() + bucket["volume"] / self.requests_per_second)
            return RateLimitResult(
                allowed=remaining > 0,
                limit=self.burst_size,
                remaining=remaining,
                reset_at=reset_at,
                algorithm=RateLimitAlgorithm.LEAKY_BUCKET,
                current_usage=bucket["volume"],
                window_start=bucket["last_leak"],
            )

    def reset(self, key: str) -> None:
        with self._lock:
            if key in self._buckets:
                del self._buckets[key]


class FixedWindowLimiter(RateLimiter):
    """
    Fixed Window rate limiter.

    Divides time into fixed windows (e.g., 1 second). Each window has a
    maximum request count. Simple but can allow burst traffic at window
    boundaries.
    """

    def __init__(
        self,
        requests_per_second: float = 100.0,
        burst_size: int = 200,
        window_size: int = 60,
    ):
        super().__init__(requests_per_second, burst_size, window_size)
        self._windows: dict[str, dict] = {}
        self._lock = threading.Lock()

    def _get_window(self, key: str) -> dict:
        now = time.time()
        window_start = int(now / self.window_size) * self.window_size
        window_key = f"{key}:{window_start}"

        if window_key not in self._windows:
            self._windows[window_key] = {
                "count": 0,
                "window_start": window_start,
            }
        return self._windows[window_key]

    def acquire(self, key: str, tokens: int = 1) -> RateLimitResult:
        with self._lock:
            window = self._get_window(key)
            limit = int(self.requests_per_second * self.window_size)

            if window["count"] + tokens <= limit:
                window["count"] += tokens
                remaining = limit - window["count"]
                reset_at = int(window["window_start"] + self.window_size)
                return RateLimitResult(
                    allowed=True,
                    limit=limit,
                    remaining=remaining,
                    reset_at=reset_at,
                    algorithm=RateLimitAlgorithm.FIXED_WINDOW,
                    current_usage=float(window["count"]),
                    window_start=window["window_start"],
                )
            else:
                retry_after = int(window["window_start"] + self.window_size - time.time()) + 1
                return RateLimitResult(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    reset_at=int(window["window_start"] + self.window_size),
                    retry_after=max(1, retry_after),
                    algorithm=RateLimitAlgorithm.FIXED_WINDOW,
                    current_usage=float(window["count"]),
                    window_start=window["window_start"],
                )

    def get_status(self, key: str) -> RateLimitResult:
        with self._lock:
            window = self._get_window(key)
            limit = int(self.requests_per_second * self.window_size)
            remaining = max(0, limit - window["count"])
            reset_at = int(window["window_start"] + self.window_size)
            return RateLimitResult(
                allowed=remaining > 0,
                limit=limit,
                remaining=remaining,
                reset_at=reset_at,
                algorithm=RateLimitAlgorithm.FIXED_WINDOW,
                current_usage=float(window["count"]),
                window_start=window["window_start"],
            )

    def reset(self, key: str) -> None:
        with self._lock:
            now = time.time()
            window_start = int(now / self.window_size) * self.window_size
            window_key = f"{key}:{window_start}"
            if window_key in self._windows:
                del self._windows[window_key]


# Factory function
def create_limiter(
    algorithm: RateLimitAlgorithm,
    requests_per_second: float = 100.0,
    burst_size: int = 200,
    window_size: int = 60,
) -> RateLimiter:
    """Create a rate limiter for the specified algorithm."""
    limiters = {
        RateLimitAlgorithm.TOKEN_BUCKET: TokenBucketLimiter,
        RateLimitAlgorithm.SLIDING_WINDOW: SlidingWindowLimiter,
        RateLimitAlgorithm.LEAKY_BUCKET: LeakyBucketLimiter,
        RateLimitAlgorithm.FIXED_WINDOW: FixedWindowLimiter,
    }

    limiter_class = limiters.get(algorithm)
    if limiter_class is None:
        raise ValueError(f"Unknown rate limiting algorithm: {algorithm}")

    return limiter_class(
        requests_per_second=requests_per_second,
        burst_size=burst_size,
        window_size=window_size,
    )
