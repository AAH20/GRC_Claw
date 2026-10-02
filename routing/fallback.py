"""Fallback strategies for model routing.

Provides configurable fallback chains for handling model failures,
rate limits, and degradation scenarios.
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple

logger = logging.getLogger(__name__)


class FallbackReason(Enum):
    """Reason for fallback activation."""

    MODEL_ERROR = "model_error"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    BUDGET_EXCEEDED = "budget_exceeded"
    QUALITY_THRESHOLD = "quality_threshold"
    CIRCUIT_BREAKER = "circuit_breaker"
    MANUAL = "manual"


@dataclass
class FallbackEvent:
    """Record of a fallback event.

    Attributes:
        timestamp: When the fallback occurred.
        from_model: Original model that failed.
        to_model: Fallback model that was used.
        reason: Why the fallback was triggered.
        error: The error that caused the fallback.
        latency_ms: Time taken to resolve the fallback.
    """

    timestamp: float
    from_model: str
    to_model: str
    reason: FallbackReason
    error: Optional[str] = None
    latency_ms: float = 0.0


class ModelExecutor(Protocol):
    """Protocol for model execution backends."""

    def execute(self, prompt: str, **kwargs: Any) -> str:
        """Execute a prompt against a model.

        Args:
            prompt: The prompt to execute.
            **kwargs: Additional execution parameters.

        Returns:
            The model response.
        """
        ...


@dataclass
class FallbackStrategy:
    """Configuration for a fallback strategy.

    Attributes:
        name: Strategy name.
        description: Human-readable description.
        max_retries: Maximum retry attempts before falling back.
        retry_delay_seconds: Base delay between retries.
        exponential_backoff: Whether to use exponential backoff.
        fallback_models: Ordered list of fallback model names.
        circuit_breaker_threshold: Errors before circuit breaker opens.
        circuit_breaker_timeout_seconds: Time before circuit breaker resets.
    """

    name: str
    description: str = ""
    max_retries: int = 2
    retry_delay_seconds: float = 1.0
    exponential_backoff: bool = True
    fallback_models: List[str] = field(default_factory=list)
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout_seconds: float = 60.0


class CircuitBreaker:
    """Circuit breaker pattern implementation.

    Prevents cascading failures by temporarily disabling a model
    after repeated failures.

    Example:
        >>> cb = CircuitBreaker(threshold=3, timeout=30.0)
        >>> if cb.can_execute():
        ...     try:
        ...         result = execute()
        ...         cb.record_success()
        ...     except Exception:
        ...         cb.record_failure()
    """

    def __init__(self, threshold: int = 5, timeout_seconds: float = 60.0) -> None:
        """Initialize the circuit breaker.

        Args:
            threshold: Number of failures before opening the circuit.
            timeout_seconds: Seconds before attempting to close the circuit.
        """
        self._threshold = threshold
        self._timeout = timeout_seconds
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state = "closed"  # closed, open, half-open

    @property
    def state(self) -> str:
        """Get current circuit state.

        Returns:
            "closed", "open", or "half-open".
        """
        if self._state == "open" and self._last_failure_time:
            if time.time() - self._last_failure_time >= self._timeout:
                self._state = "half-open"
        return self._state

    def can_execute(self) -> bool:
        """Check if execution is allowed.

        Returns:
            True if the circuit is closed or half-open.
        """
        return self.state in ("closed", "half-open")

    def record_success(self) -> None:
        """Record a successful execution."""
        self._failure_count = 0
        self._state = "closed"

    def record_failure(self) -> None:
        """Record a failed execution."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._failure_count >= self._threshold:
            self._state = "open"
            logger.warning(
                "Circuit breaker opened after %d failures", self._failure_count
            )

    def reset(self) -> None:
        """Reset the circuit breaker."""
        self._failure_count = 0
        self._last_failure_time = None
        self._state = "closed"


class FallbackChain:
    """Chain of fallback models with retry and circuit breaker logic.

    Manages a prioritized list of models to try when the primary
    model fails, with configurable retry policies and circuit breakers.

    Example:
        >>> chain = FallbackChain()
        >>> chain.add_model("gpt-4o", executor)
        >>> chain.add_model("gpt-4o-mini", executor)
        >>> result = chain.execute("Hello!")
    """

    def __init__(self, strategy: Optional[FallbackStrategy] = None) -> None:
        """Initialize the fallback chain.

        Args:
            strategy: Fallback strategy configuration.
        """
        self._strategy = strategy or FallbackStrategy(name="default")
        self._models: List[Tuple[str, ModelExecutor]] = []
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._event_history: List[FallbackEvent] = []

    @property
    def strategy(self) -> FallbackStrategy:
        """Get the fallback strategy.

        Returns:
            The current fallback strategy.
        """
        return self._strategy

    @property
    def event_history(self) -> List[FallbackEvent]:
        """Get fallback event history.

        Returns:
            List of fallback events.
        """
        return list(self._event_history)

    def add_model(self, name: str, executor: ModelExecutor) -> None:
        """Add a model to the fallback chain.

        Args:
            name: Model name.
            executor: Model executor instance.
        """
        self._models.append((name, executor))
        self._circuit_breakers[name] = CircuitBreaker(
            threshold=self._strategy.circuit_breaker_threshold,
            timeout_seconds=self._strategy.circuit_breaker_timeout_seconds,
        )
        logger.info("Added model to fallback chain: %s", name)

    def remove_model(self, name: str) -> bool:
        """Remove a model from the fallback chain.

        Args:
            name: Model name to remove.

        Returns:
            True if the model was removed, False if not found.
        """
        original_len = len(self._models)
        self._models = [(n, e) for n, e in self._models if n != name]
        self._circuit_breakers.pop(name, None)
        return len(self._models) < original_len

    def execute(
        self,
        prompt: str,
        **kwargs: Any,
    ) -> Tuple[str, str]:
        """Execute a prompt through the fallback chain.

        Tries each model in order, with retries and circuit breaker
        protection, until one succeeds.

        Args:
            prompt: The prompt to execute.
            **kwargs: Additional execution parameters.

        Returns:
            Tuple of (model_name, response).

        Raises:
            FallbackExhaustedError: If all models in the chain fail.
        """
        if not self._models:
            raise FallbackExhaustedError("No models in fallback chain")

        last_error: Optional[Exception] = None

        for model_name, executor in self._models:
            cb = self._circuit_breakers[model_name]

            if not cb.can_execute():
                logger.debug("Circuit breaker open for %s, skipping", model_name)
                continue

            # Try with retries
            for attempt in range(self._strategy.max_retries + 1):
                try:
                    start_time = time.time()
                    response = executor.execute(prompt, **kwargs)
                    latency_ms = (time.time() - start_time) * 1000

                    cb.record_success()

                    if attempt > 0 or model_name != self._models[0][0]:
                        self._record_event(
                            from_model=self._models[0][0],
                            to_model=model_name,
                            reason=FallbackReason.MODEL_ERROR,
                            latency_ms=latency_ms,
                        )

                    logger.info(
                        "Fallback chain succeeded with %s (attempt %d)",
                        model_name,
                        attempt + 1,
                    )
                    return model_name, response

                except Exception as exc:
                    last_error = exc
                    cb.record_failure()

                    if attempt < self._strategy.max_retries:
                        delay = self._calculate_delay(attempt)
                        logger.warning(
                            "Model %s failed (attempt %d/%d): %s. Retrying in %.1fs",
                            model_name,
                            attempt + 1,
                            self._strategy.max_retries + 1,
                            exc,
                            delay,
                        )
                        time.sleep(delay)

        raise FallbackExhaustedError(
            f"All models in fallback chain failed. Last error: {last_error}"
        )

    def get_circuit_breaker_states(self) -> Dict[str, str]:
        """Get circuit breaker states for all models.

        Returns:
            Dictionary mapping model names to circuit states.
        """
        return {name: cb.state for name, cb in self._circuit_breakers.items()}

    def reset_circuit_breakers(self) -> None:
        """Reset all circuit breakers."""
        for cb in self._circuit_breakers.values():
            cb.reset()
        logger.info("All circuit breakers reset")

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate retry delay.

        Args:
            attempt: Current attempt number (0-indexed).

        Returns:
            Delay in seconds.
        """
        if self._strategy.exponential_backoff:
            return self._strategy.retry_delay_seconds * (2 ** attempt)
        return self._strategy.retry_delay_seconds

    def _record_event(
        self,
        from_model: str,
        to_model: str,
        reason: FallbackReason,
        latency_ms: float = 0.0,
        error: Optional[str] = None,
    ) -> None:
        """Record a fallback event.

        Args:
            from_model: Original model.
            to_model: Fallback model.
            reason: Fallback reason.
            latency_ms: Resolution latency.
            error: Optional error message.
        """
        event = FallbackEvent(
            timestamp=time.time(),
            from_model=from_model,
            to_model=to_model,
            reason=reason,
            error=error,
            latency_ms=latency_ms,
        )
        self._event_history.append(event)


class FallbackExhaustedError(Exception):
    """Raised when all fallback models have been exhausted."""

    pass


class RandomFallbackStrategy(FallbackStrategy):
    """Random fallback strategy that shuffles model order."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize random fallback strategy.

        Args:
            **kwargs: Additional strategy parameters.
        """
        super().__init__(name="random", description="Random model selection", **kwargs)


class WeightedFallbackStrategy(FallbackStrategy):
    """Weighted fallback strategy with probability-based selection."""

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize weighted fallback strategy.

        Args:
            weights: Model name to weight mapping.
            **kwargs: Additional strategy parameters.
        """
        super().__init__(name="weighted", description="Weighted model selection", **kwargs)
        self._weights = weights or {}

    def select_model(self, available_models: List[str]) -> str:
        """Select a model based on weights.

        Args:
            available_models: List of available model names.

        Returns:
            Selected model name.

        Raises:
            ValueError: If no models are available.
        """
        if not available_models:
            raise ValueError("No available models for weighted selection")

        weights = [self._weights.get(m, 1.0) for m in available_models]
        total = sum(weights)
        probabilities = [w / total for w in weights]

        return random.choices(available_models, weights=probabilities, k=1)[0]
