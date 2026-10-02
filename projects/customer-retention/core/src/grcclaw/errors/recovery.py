"""
Error Recovery Strategies for GRC_Claw

Provides automatic error recovery mechanisms:
- Retry with exponential backoff and jitter
- Circuit breaker pattern
- Fallback strategies
- Recovery manager for orchestrating multiple strategies
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, TypeVar

from .taxonomy import ErrorRecoverability, classify_error

logger = logging.getLogger("grcclaw.errors.recovery")

T = TypeVar("T")


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RetryConfig:
    """Configuration for retry strategy."""

    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    backoff_multiplier: float = 2.0
    jitter: bool = True
    jitter_max_seconds: float = 1.0
    retryable_exceptions: tuple[type[Exception], ...] = (
        ConnectionError,
        TimeoutError,
        OSError,
    )
    retryable_error_codes: set[str] = field(default_factory=set)


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_seconds: float = 60.0
    half_open_max_calls: int = 3


@dataclass
class FallbackConfig:
    """Configuration for fallback strategy."""

    fallback_value: Any = None
    fallback_function: Callable[[], Awaitable[Any]] | None = None
    cache_ttl_seconds: float = 300.0


class RecoveryStrategy:
    """Base class for recovery strategies."""

    async def execute(
        self,
        operation: Callable[[], Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute an operation with recovery."""
        raise NotImplementedError


class RetryStrategy(RecoveryStrategy):
    """Retry strategy with exponential backoff and jitter."""

    def __init__(self, config: RetryConfig | None = None):
        self.config = config or RetryConfig()

    async def execute(
        self,
        operation: Callable[[], Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute with retry logic."""
        last_exception: Exception | None = None

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                return await operation(*args, **kwargs)
            except Exception as exc:
                last_exception = exc

                # Check if exception is retryable
                if not self._is_retryable(exc):
                    raise

                # Don't retry on last attempt
                if attempt == self.config.max_attempts:
                    break

                # Calculate delay
                delay = self._calculate_delay(attempt)

                logger.warning(
                    "Retry attempt %d/%d after %s: %s (waiting %.2fs)",
                    attempt,
                    self.config.max_attempts,
                    type(exc).__name__,
                    exc,
                    delay,
                )

                await asyncio.sleep(delay)

        # All retries exhausted
        if last_exception:
            raise last_exception
        raise RuntimeError("Retry exhausted with no exception")

    def _is_retryable(self, exc: Exception) -> bool:
        """Check if an exception is retryable."""
        # Check exception type
        if isinstance(exc, self.config.retryable_exceptions):
            return True

        # Check error code if available
        error_code = getattr(exc, "code", None)
        if error_code and error_code in self.config.retryable_error_codes:
            return True

        # Check classification
        if error_code:
            classification = classify_error(error_code)
            if classification.recoverability in (
                ErrorRecoverability.RETRYABLE,
                ErrorRecoverability.IDEMPOTENT_RETRY,
            ):
                return True

        return False

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        delay = self.config.base_delay_seconds * (
            self.config.backoff_multiplier ** (attempt - 1)
        )
        delay = min(delay, self.config.max_delay_seconds)

        if self.config.jitter:
            delay += random.uniform(0, self.config.jitter_max_seconds)

        return delay


class CircuitBreaker(RecoveryStrategy):
    """Circuit breaker pattern implementation."""

    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitBreakerState:
        return self._state

    async def execute(
        self,
        operation: Callable[[], Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute with circuit breaker protection."""
        async with self._lock:
            await self._update_state()

            if self._state == CircuitBreakerState.OPEN:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is open"
                )

            if self._state == CircuitBreakerState.HALF_OPEN:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' half-open call limit reached"
                    )
                self._half_open_calls += 1

        try:
            result = await operation(*args, **kwargs)
            await self._on_success()
            return result
        except Exception:
            await self._on_failure()
            raise

    async def _update_state(self) -> None:
        """Update circuit breaker state based on time."""
        if self._state == CircuitBreakerState.OPEN:
            if self._last_failure_time is None:
                return

            elapsed = time.time() - self._last_failure_time
            if elapsed >= self.config.timeout_seconds:
                logger.info(
                    "Circuit breaker '%s' transitioning to half-open", self.name
                )
                self._state = CircuitBreakerState.HALF_OPEN
                self._half_open_calls = 0
                self._success_count = 0

    async def _on_success(self) -> None:
        """Handle successful call."""
        async with self._lock:
            if self._state == CircuitBreakerState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    logger.info(
                        "Circuit breaker '%s' closing after recovery", self.name
                    )
                    self._state = CircuitBreakerState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
            else:
                self._failure_count = 0

    async def _on_failure(self) -> None:
        """Handle failed call."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitBreakerState.HALF_OPEN:
                logger.warning(
                    "Circuit breaker '%s' reopening after failure in half-open",
                    self.name,
                )
                self._state = CircuitBreakerState.OPEN
                self._success_count = 0
            elif self._failure_count >= self.config.failure_threshold:
                logger.warning(
                    "Circuit breaker '%s' opening after %d failures",
                    self.name,
                    self._failure_count,
                )
                self._state = CircuitBreakerState.OPEN

    def get_metrics(self) -> dict[str, Any]:
        """Get circuit breaker metrics."""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": self._last_failure_time,
            "half_open_calls": self._half_open_calls,
        }


class CircuitBreakerOpenError(Exception):
    """Raised when a circuit breaker is open."""

    def __init__(self, message: str = "Circuit breaker is open"):
        super().__init__(message)
        self.code = "CIRCUIT_BREAKER_OPEN"


class FallbackStrategy(RecoveryStrategy):
    """Fallback strategy for degraded operation."""

    def __init__(self, config: FallbackConfig | None = None):
        self.config = config or FallbackConfig()
        self._cache: dict[str, tuple[float, Any]] = {}

    async def execute(
        self,
        operation: Callable[[], Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute with fallback on failure."""
        try:
            result = await operation(*args, **kwargs)
            # Cache successful result
            cache_key = self._make_cache_key(args, kwargs)
            self._cache[cache_key] = (time.time(), result)
            return result
        except Exception as exc:
            logger.warning(
                "Operation failed, attempting fallback: %s", exc
            )

            # Try fallback function
            if self.config.fallback_function:
                try:
                    return await self.config.fallback_function()
                except Exception as fallback_exc:
                    logger.error("Fallback function failed: %s", fallback_exc)

            # Try cached value
            cache_key = self._make_cache_key(args, kwargs)
            cached = self._cache.get(cache_key)
            if cached:
                cached_time, cached_value = cached
                if time.time() - cached_time < self.config.cache_ttl_seconds:
                    logger.info("Using cached fallback value")
                    return cached_value

            # Use static fallback value
            if self.config.fallback_value is not None:
                return self.config.fallback_value

            raise

    def _make_cache_key(self, args: tuple, kwargs: dict) -> str:
        """Create a cache key from arguments."""
        return f"{args}:{sorted(kwargs.items())}"


class RecoveryManager:
    """Orchestrates multiple recovery strategies."""

    def __init__(self) -> None:
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._retry_strategies: dict[str, RetryStrategy] = {}
        self._fallback_strategies: dict[str, FallbackStrategy] = {}

    def register_circuit_breaker(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
    ) -> CircuitBreaker:
        """Register a circuit breaker."""
        cb = CircuitBreaker(name, config)
        self._circuit_breakers[name] = cb
        return cb

    def register_retry(
        self,
        name: str,
        config: RetryConfig | None = None,
    ) -> RetryStrategy:
        """Register a retry strategy."""
        strategy = RetryStrategy(config)
        self._retry_strategies[name] = strategy
        return strategy

    def register_fallback(
        self,
        name: str,
        config: FallbackConfig | None = None,
    ) -> FallbackStrategy:
        """Register a fallback strategy."""
        strategy = FallbackStrategy(config)
        self._fallback_strategies[name] = strategy
        return strategy

    async def execute(
        self,
        operation: Callable[[], Awaitable[T]],
        *,
        retry: str | None = None,
        circuit_breaker: str | None = None,
        fallback: str | None = None,
    ) -> T:
        """Execute an operation with the specified recovery strategies.

        Args:
            operation: The async operation to execute (use lambda/partial to bind args).
            retry: Name of retry strategy to use.
            circuit_breaker: Name of circuit breaker to use.
            fallback: Name of fallback strategy to use.

        Returns:
            The operation result.

        Raises:
            Exception: If all recovery strategies fail.
        """
        # Build the execution chain
        exec_fn = operation

        # Wrap with fallback (outermost)
        if fallback and fallback in self._fallback_strategies:
            fb = self._fallback_strategies[fallback]
            exec_fn = lambda: fb.execute(operation)

        # Wrap with circuit breaker
        if circuit_breaker and circuit_breaker in self._circuit_breakers:
            cb = self._circuit_breakers[circuit_breaker]
            inner = exec_fn
            exec_fn = lambda: cb.execute(inner)

        # Wrap with retry (innermost)
        if retry and retry in self._retry_strategies:
            rs = self._retry_strategies[retry]
            inner = exec_fn
            exec_fn = lambda: rs.execute(inner)

        return await exec_fn()

    def get_circuit_breaker(self, name: str) -> CircuitBreaker | None:
        """Get a circuit breaker by name."""
        return self._circuit_breakers.get(name)

    def get_metrics(self) -> dict[str, Any]:
        """Get metrics for all recovery strategies."""
        return {
            "circuit_breakers": {
                name: cb.get_metrics()
                for name, cb in self._circuit_breakers.items()
            },
            "retry_strategies": list(self._retry_strategies.keys()),
            "fallback_strategies": list(self._fallback_strategies.keys()),
        }


# ── Decorator for Easy Application ────────────────────────────────────────


def with_retry(
    max_attempts: int = 3,
    base_delay_seconds: float = 1.0,
    max_delay_seconds: float = 60.0,
    backoff_multiplier: float = 2.0,
    jitter: bool = True,
):
    """Decorator to add retry logic to an async function."""

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        config = RetryConfig(
            max_attempts=max_attempts,
            base_delay_seconds=base_delay_seconds,
            max_delay_seconds=max_delay_seconds,
            backoff_multiplier=backoff_multiplier,
            jitter=jitter,
        )
        strategy = RetryStrategy(config)

        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await strategy.execute(func, *args, **kwargs)

        return wrapper

    return decorator


def with_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    success_threshold: int = 3,
    timeout_seconds: float = 60.0,
):
    """Decorator to add circuit breaker to an async function."""

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            timeout_seconds=timeout_seconds,
        )
        cb = CircuitBreaker(name, config)

        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await cb.execute(func, *args, **kwargs)

        return wrapper

    return decorator


def with_fallback(
    fallback_value: Any = None,
    fallback_function: Callable[[], Awaitable[Any]] | None = None,
    cache_ttl_seconds: float = 300.0,
):
    """Decorator to add fallback to an async function."""

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        config = FallbackConfig(
            fallback_value=fallback_value,
            fallback_function=fallback_function,
            cache_ttl_seconds=cache_ttl_seconds,
        )
        strategy = FallbackStrategy(config)

        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await strategy.execute(func, *args, **kwargs)

        return wrapper

    return decorator
