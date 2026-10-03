"""Enhanced retry logic with exponential backoff, jitter, and sync/async support."""
import asyncio
import functools
import random
import time
from typing import Any, Callable, Coroutine, Optional, Tuple, TypeVar, Union

T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Tuple[type, ...] = (Exception,),
        on_retry: Optional[Callable[[Exception, int, float], None]] = None,
    ) -> None:
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions
        self.on_retry = on_retry


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[type, ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int, float], None]] = None,
) -> Callable:
    """Decorator: retry function with exponential backoff and jitter.

    Supports both synchronous and asynchronous functions.

    Args:
        max_attempts: Maximum number of retry attempts.
        base_delay: Initial delay between retries in seconds.
        max_delay: Maximum delay between retries in seconds.
        exponential_base: Base for exponential backoff calculation.
        jitter: Whether to add random jitter to delay.
        retryable_exceptions: Tuple of exception types to retry on.
        on_retry: Optional callback called on each retry with (exception, attempt, delay).

    Returns:
        Decorated function with retry logic.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                last_exc: Optional[Exception] = None
                for attempt in range(1, max_attempts + 1):
                    try:
                        return await func(*args, **kwargs)
                    except retryable_exceptions as exc:
                        last_exc = exc
                        if attempt == max_attempts:
                            break
                        delay = min(max_delay, base_delay * (exponential_base ** (attempt - 1)))
                        if jitter:
                            delay *= 0.5 + random.random()
                        if on_retry:
                            on_retry(exc, attempt, delay)
                        await asyncio.sleep(delay)
                raise last_exc  # type: ignore[misc]

            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                last_exc: Optional[Exception] = None
                for attempt in range(1, max_attempts + 1):
                    try:
                        return func(*args, **kwargs)
                    except retryable_exceptions as exc:
                        last_exc = exc
                        if attempt == max_attempts:
                            break
                        delay = min(max_delay, base_delay * (exponential_base ** (attempt - 1)))
                        if jitter:
                            delay *= 0.5 + random.random()
                        if on_retry:
                            on_retry(exc, attempt, delay)
                        time.sleep(delay)
                raise last_exc  # type: ignore[misc]

            return sync_wrapper

    return decorator


def retry_with_config(config: RetryConfig) -> Callable:
    """Decorator factory using RetryConfig.

    Args:
        config: RetryConfig instance with retry parameters.

    Returns:
        Decorator function.
    """
    return retry(
        max_attempts=config.max_attempts,
        base_delay=config.base_delay,
        max_delay=config.max_delay,
        exponential_base=config.exponential_base,
        jitter=config.jitter,
        retryable_exceptions=config.retryable_exceptions,
        on_retry=config.on_retry,
    )


async def retry_async(
    func: Callable[..., Coroutine[Any, Any, T]],
    *args: Any,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[type, ...] = (Exception,),
    **kwargs: Any,
) -> T:
    """Retry an async function with exponential backoff.

    Args:
        func: Async function to retry.
        *args: Positional arguments for the function.
        max_attempts: Maximum number of retry attempts.
        base_delay: Initial delay between retries in seconds.
        max_delay: Maximum delay between retries in seconds.
        exponential_base: Base for exponential backoff calculation.
        jitter: Whether to add random jitter to delay.
        retryable_exceptions: Tuple of exception types to retry on.
        **kwargs: Keyword arguments for the function.

    Returns:
        Result of the function call.

    Raises:
        The last exception if all retries fail.
    """
    last_exc: Optional[Exception] = None
    for attempt in range(1, max_attempts + 1):
        try:
            return await func(*args, **kwargs)
        except retryable_exceptions as exc:
            last_exc = exc
            if attempt == max_attempts:
                break
            delay = min(max_delay, base_delay * (exponential_base ** (attempt - 1)))
            if jitter:
                delay *= 0.5 + random.random()
            await asyncio.sleep(delay)
    raise last_exc  # type: ignore[misc]


def retry_sync(
    func: Callable[..., T],
    *args: Any,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[type, ...] = (Exception,),
    **kwargs: Any,
) -> T:
    """Retry a sync function with exponential backoff.

    Args:
        func: Sync function to retry.
        *args: Positional arguments for the function.
        max_attempts: Maximum number of retry attempts.
        base_delay: Initial delay between retries in seconds.
        max_delay: Maximum delay between retries in seconds.
        exponential_base: Base for exponential backoff calculation.
        jitter: Whether to add random jitter to delay.
        retryable_exceptions: Tuple of exception types to retry on.
        **kwargs: Keyword arguments for the function.

    Returns:
        Result of the function call.

    Raises:
        The last exception if all retries fail.
    """
    last_exc: Optional[Exception] = None
    for attempt in range(1, max_attempts + 1):
        try:
            return func(*args, **kwargs)
        except retryable_exceptions as exc:
            last_exc = exc
            if attempt == max_attempts:
                break
            delay = min(max_delay, base_delay * (exponential_base ** (attempt - 1)))
            if jitter:
                delay *= 0.5 + random.random()
            time.sleep(delay)
    raise last_exc  # type: ignore[misc]