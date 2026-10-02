"""Shared fixtures for chaos engineering tests.

This module provides pytest fixtures that simulate various failure modes
including service outages, network partitions, resource exhaustion, and
cascading failures. All fixtures are designed to be composable and
configurable via environment variables or pytest markers.
"""

from __future__ import annotations

import asyncio
import contextlib
import dataclasses
import enum
import logging
import os
import random
import socket
import threading
import time
import uuid
from collections.abc import AsyncGenerator, Callable, Generator
from typing import Any, Protocol, TypeVar, cast
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logger = logging.getLogger("grc_chaos")


def _configure_logging() -> None:
    """Configure logging for chaos test output."""
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if os.getenv("CHAOS_DEBUG") else logging.INFO)


_configure_logging()


# ---------------------------------------------------------------------------
# Enums and data classes
# ---------------------------------------------------------------------------
class FailureMode(enum.Enum):
    """Supported failure injection modes."""

    TIMEOUT = "timeout"
    CONNECTION_REFUSED = "connection_refused"
    CONNECTION_RESET = "connection_reset"
    PARTIAL_RESPONSE = "partial_response"
    CORRUPTED_DATA = "corrupted_data"
    SLOW_RESPONSE = "slow_response"
    RATE_LIMIT = "rate_limit"
    DNS_FAILURE = "dns_failure"
    TLS_FAILURE = "tls_failure"
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"


class ServiceType(enum.Enum):
    """Types of services that can be targeted by chaos experiments."""

    LLM = "llm"
    DATABASE = "database"
    KAFKA = "kafka"
    REDIS = "redis"
    API = "api"
    NETWORK = "network"


@dataclasses.dataclass(frozen=True)
class ChaosConfig:
    """Configuration for a chaos experiment.

    Attributes:
        failure_mode: The type of failure to inject.
        target_service: Which service to target.
        duration_seconds: How long the failure should last.
        probability: Probability of failure per request (0.0–1.0).
        delay_ms: Artificial delay in milliseconds before responding.
        error_message: Custom error message to return.
        retry_count: Number of retries before giving up.
        timeout_seconds: Timeout threshold in seconds.
    """

    failure_mode: FailureMode = FailureMode.TIMEOUT
    target_service: ServiceType = ServiceType.API
    duration_seconds: float = 5.0
    probability: float = 1.0
    delay_ms: int = 0
    error_message: str = "Chaos-induced failure"
    retry_count: int = 3
    timeout_seconds: float = 30.0


@dataclasses.dataclass
class ChaosEvent:
    """Record of a chaos event that occurred during testing."""

    event_id: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = dataclasses.field(default_factory=time.time)
    service: ServiceType = ServiceType.API
    failure_mode: FailureMode = FailureMode.TIMEOUT
    message: str = ""
    recovered: bool = False
    recovery_time_ms: float | None = None


@dataclasses.dataclass
class ServiceHealth:
    """Health status of a service during chaos testing."""

    service: ServiceType
    is_healthy: bool = True
    consecutive_failures: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    last_failure_time: float | None = None
    circuit_open: bool = False


# ---------------------------------------------------------------------------
# Protocols (structural subtyping)
# ---------------------------------------------------------------------------
class ChaosTarget(Protocol):
    """Protocol for services that can be targeted by chaos experiments."""

    async def execute(self, request: dict[str, Any]) -> dict[str, Any]:
        """Execute a request against the target service."""
        ...

    def health_check(self) -> ServiceHealth:
        """Return current health status."""
        ...


class Recoverable(Protocol):
    """Protocol for services that support recovery operations."""

    async def recover(self) -> bool:
        """Attempt to recover from failure. Returns True on success."""
        ...


# ---------------------------------------------------------------------------
# Chaos monkey — the core failure injector
# ---------------------------------------------------------------------------
class ChaosMonkey:
    """Injects failures into service calls based on configuration.

    This is the primary tool for chaos experiments. It wraps service calls
    and injects failures according to the configured probability and mode.
    """

    def __init__(self, config: ChaosConfig) -> None:
        self.config = config
        self.events: list[ChaosEvent] = []
        self._active = False
        self._start_time: float | None = None

    def start(self) -> None:
        """Activate the chaos monkey."""
        self._active = True
        self._start_time = time.time()
        logger.info(
            "ChaosMonkey activated: mode=%s target=%s duration=%.1fs",
            self.config.failure_mode.value,
            self.config.target_service.value,
            self.config.duration_seconds,
        )

    def stop(self) -> None:
        """Deactivate the chaos monkey."""
        self._active = False
        elapsed = (time.time() - self._start_time) if self._start_time else 0
        logger.info("ChaosMonkey deactivated after %.2fs", elapsed)

    @property
    def is_active(self) -> bool:
        """Check if chaos is currently active."""
        return self._active

    def should_inject(self) -> bool:
        """Determine if a failure should be injected for this request."""
        if not self._active:
            return False
        if self._start_time and (time.time() - self._start_time) > self.config.duration_seconds:
            self._active = False
            return False
        return random.random() < self.config.probability

    def inject_failure(self, context: str = "") -> ChaosEvent:
        """Create and record a chaos event."""
        event = ChaosEvent(
            service=self.config.target_service,
            failure_mode=self.config.failure_mode,
            message=f"[{context}] {self.config.error_message}",
        )
        self.events.append(event)
        logger.warning("Chaos injected: %s — %s", event.failure_mode.value, event.message)
        return event

    def get_events(
        self,
        service: ServiceType | None = None,
        mode: FailureMode | None = None,
    ) -> list[ChaosEvent]:
        """Get recorded chaos events, optionally filtered."""
        events = self.events
        if service is not None:
            events = [e for e in events if e.service == service]
        if mode is not None:
            events = [e for e in events if e.failure_mode == mode]
        return events


# ---------------------------------------------------------------------------
# Mock services
# ---------------------------------------------------------------------------
class MockLLMService:
    """Mock LLM service for chaos testing."""

    def __init__(self, response_delay: float = 0.1) -> None:
        self.response_delay = response_delay
        self.call_count = 0
        self.failure_count = 0

    async def generate(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """Simulate an LLM generation call."""
        self.call_count += 1
        await asyncio.sleep(self.response_delay)
        return {
            "text": f"Response to: {prompt[:50]}",
            "model": "mock-llm-v1",
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        }

    def health_check(self) -> ServiceHealth:
        return ServiceHealth(
            service=ServiceType.LLM,
            is_healthy=self.failure_count == 0,
            consecutive_failures=self.failure_count,
            total_requests=self.call_count,
            failed_requests=self.failure_count,
        )


class MockDatabaseService:
    """Mock database service for chaos testing."""

    def __init__(self) -> None:
        self.connected = True
        self.query_count = 0
        self.failure_count = 0

    async def query(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Simulate a database query."""
        if not self.connected:
            raise ConnectionError("Database connection lost")
        self.query_count += 1
        await asyncio.sleep(0.01)
        return [{"id": 1, "result": "mock_data"}]

    async def execute(self, sql: str, params: dict[str, Any] | None = None) -> int:
        """Simulate a database write operation."""
        if not self.connected:
            raise ConnectionError("Database connection lost")
        self.query_count += 1
        await asyncio.sleep(0.01)
        return 1

    def health_check(self) -> ServiceHealth:
        return ServiceHealth(
            service=ServiceType.DATABASE,
            is_healthy=self.connected,
            consecutive_failures=self.failure_count,
            total_requests=self.query_count,
            failed_requests=self.failure_count,
        )


class MockKafkaService:
    """Mock Kafka service for chaos testing."""

    def __init__(self) -> None:
        self.brokers_available = True
        self.produced_count = 0
        self.consumed_count = 0

    async def produce(self, topic: str, message: dict[str, Any]) -> bool:
        """Simulate producing a message to Kafka."""
        if not self.brokers_available:
            raise ConnectionError("Kafka brokers unavailable")
        self.produced_count += 1
        await asyncio.sleep(0.005)
        return True

    async def consume(self, topic: str, group_id: str) -> list[dict[str, Any]]:
        """Simulate consuming messages from Kafka."""
        if not self.brokers_available:
            raise ConnectionError("Kafka brokers unavailable")
        self.consumed_count += 1
        await asyncio.sleep(0.005)
        return [{"topic": topic, "value": "mock_message"}]

    def health_check(self) -> ServiceHealth:
        return ServiceHealth(
            service=ServiceType.KAFKA,
            is_healthy=self.brokers_available,
            total_requests=self.produced_count + self.consumed_count,
            failed_requests=0 if self.brokers_available else self.produced_count,
        )


class MockRedisService:
    """Mock Redis service for chaos testing."""

    def __init__(self) -> None:
        self.available = True
        self._data: dict[str, str] = {}
        self.command_count = 0

    async def get(self, key: str) -> str | None:
        """Simulate a Redis GET operation."""
        if not self.available:
            raise ConnectionError("Redis connection refused")
        self.command_count += 1
        await asyncio.sleep(0.001)
        return self._data.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> bool:
        """Simulate a Redis SET operation."""
        if not self.available:
            raise ConnectionError("Redis connection refused")
        self.command_count += 1
        await asyncio.sleep(0.001)
        self._data[key] = value
        return True

    async def delete(self, key: str) -> int:
        """Simulate a Redis DELETE operation."""
        if not self.available:
            raise ConnectionError("Redis connection refused")
        self.command_count += 1
        await asyncio.sleep(0.001)
        return 1 if self._data.pop(key, None) is not None else 0

    def health_check(self) -> ServiceHealth:
        return ServiceHealth(
            service=ServiceType.REDIS,
            is_healthy=self.available,
            total_requests=self.command_count,
            failed_requests=0 if self.available else self.command_count,
        )


class MockAPIService:
    """Mock external API service for chaos testing."""

    def __init__(self) -> None:
        self.up = True
        self.latency_ms = 50
        self.request_count = 0

    async def call(self, endpoint: str, method: str = "GET", payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Simulate an external API call."""
        if not self.up:
            raise ConnectionError("API is down")
        self.request_count += 1
        await asyncio.sleep(self.latency_ms / 1000)
        return {"status": "ok", "endpoint": endpoint, "data": payload or {}}

    def health_check(self) -> ServiceHealth:
        return ServiceHealth(
            service=ServiceType.API,
            is_healthy=self.up,
            total_requests=self.request_count,
            failed_requests=0 if self.up else self.request_count,
        )


# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------
class CircuitBreaker:
    """Simple circuit breaker implementation for chaos testing."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self._failure_count = 0
        self._last_failure_time: float | None = None
        self._state = "closed"  # closed, open, half-open
        self._half_open_calls = 0

    @property
    def state(self) -> str:
        """Current state of the circuit breaker."""
        if self._state == "open" and self._last_failure_time:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                self._state = "half-open"
                self._half_open_calls = 0
        return self._state

    def record_success(self) -> None:
        """Record a successful call."""
        self._failure_count = 0
        if self._state == "half-open":
            self._half_open_calls += 1
            if self._half_open_calls >= self.half_open_max_calls:
                self._state = "closed"
                logger.info("Circuit breaker closed after successful recovery")

    def record_failure(self) -> None:
        """Record a failed call."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._state == "half-open":
            self._state = "open"
            logger.warning("Circuit breaker re-opened during half-open state")
        elif self._failure_count >= self.failure_threshold:
            self._state = "open"
            logger.warning("Circuit breaker opened after %d failures", self._failure_count)

    def can_execute(self) -> bool:
        """Check if a call is allowed through the circuit breaker."""
        state = self.state
        if state == "closed":
            return True
        if state == "open":
            return False
        # half-open
        if self._half_open_calls < self.half_open_max_calls:
            self._half_open_calls += 1
            return True
        return False


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def chaos_config() -> ChaosConfig:
    """Default chaos configuration for tests."""
    return ChaosConfig()


@pytest.fixture
def chaos_monkey(chaos_config: ChaosConfig) -> Generator[ChaosMonkey, None, None]:
    """Provide a ChaosMonkey instance for the duration of a test."""
    monkey = ChaosMonkey(chaos_config)
    monkey.start()
    yield monkey
    monkey.stop()


@pytest.fixture
def mock_llm() -> MockLLMService:
    """Provide a mock LLM service."""
    return MockLLMService()


@pytest.fixture
def mock_database() -> MockDatabaseService:
    """Provide a mock database service."""
    return MockDatabaseService()


@pytest.fixture
def mock_kafka() -> MockKafkaService:
    """Provide a mock Kafka service."""
    return MockKafkaService()


@pytest.fixture
def mock_redis() -> MockRedisService:
    """Provide a mock Redis service."""
    return MockRedisService()


@pytest.fixture
def mock_api() -> MockAPIService:
    """Provide a mock API service."""
    return MockAPIService()


@pytest.fixture
def circuit_breaker() -> CircuitBreaker:
    """Provide a circuit breaker instance."""
    return CircuitBreaker(failure_threshold=3, recovery_timeout=5.0)


@pytest.fixture
def failure_injector() -> Callable[..., ChaosEvent]:
    """Provide a simple failure injection function."""

    def _inject(
        mode: FailureMode = FailureMode.TIMEOUT,
        service: ServiceType = ServiceType.API,
        message: str = "Injected failure",
    ) -> ChaosEvent:
        return ChaosEvent(
            service=service,
            failure_mode=mode,
            message=message,
        )

    return _inject


@pytest.fixture
async def async_chaos_monkey(chaos_config: ChaosConfig) -> AsyncGenerator[ChaosMonkey, None]:
    """Async variant of the chaos monkey fixture."""
    monkey = ChaosMonkey(chaos_config)
    monkey.start()
    yield monkey
    monkey.stop()


@pytest.fixture
def network_partition_simulator() -> Generator[dict[str, bool], None, None]:
    """Simulate network partition between services.

    Yields a dict mapping service names to their reachability status.
    """
    partition_state: dict[str, bool] = {
        "llm": True,
        "database": True,
        "kafka": True,
        "redis": True,
        "api": True,
    }
    yield partition_state


@pytest.fixture
def load_generator() -> Generator[Callable[[int], int], None, None]:
    """Provide a load generation helper.

    Returns a function that simulates N concurrent requests and returns
    the number of successful responses.
    """

    def _generate(concurrent_requests: int) -> int:
        successful = 0
        for _ in range(concurrent_requests):
            if random.random() > 0.1:  # 90% success rate
                successful += 1
        return successful

    return _generate


@pytest.fixture
def recovery_tracker() -> Generator[dict[str, Any], None, None]:
    """Track recovery metrics during chaos tests.

    Yields a dict that tests can populate with recovery data.
    """
    tracker: dict[str, Any] = {
        "start_time": time.time(),
        "recovery_attempts": 0,
        "successful_recoveries": 0,
        "failed_recoveries": 0,
        "recovery_times_ms": [],
    }
    yield tracker
    tracker["end_time"] = time.time()
    tracker["total_duration_ms"] = (tracker["end_time"] - tracker["start_time"]) * 1000


@pytest.fixture
def service_health_collector() -> Generator[dict[ServiceType, ServiceHealth], None, None]:
    """Collect health status from multiple services."""
    health_map: dict[ServiceType, ServiceHealth] = {}
    yield health_map


@pytest.fixture(autouse=True)
def reset_random_seed() -> Generator[None, None, None]:
    """Reset random seed before each test for reproducibility."""
    random.seed(42)
    yield
    random.seed()


@pytest.fixture
def temp_socket() -> Generator[socket.socket, None, None]:
    """Provide a temporary socket for network-level chaos testing."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2.0)
    yield sock
    sock.close()


@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Provide an event loop for async chaos tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
