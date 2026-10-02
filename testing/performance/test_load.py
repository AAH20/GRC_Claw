"""Load testing framework for marketing systems.

This module provides load testing capabilities including:
- Concurrent user simulation
- Request rate testing
- Response time measurement
- Throughput analysis
- Resource utilization tracking
- Load pattern definitions (spike, ramp, steady)
"""

from __future__ import annotations

import asyncio
import statistics
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine


class LoadPattern(Enum):
    """Load pattern types."""

    STEADY = "steady"
    RAMP_UP = "ramp_up"
    SPIKE = "spike"
    WAVE = "wave"
    STRESS = "stress"


@dataclass
class LoadConfig:
    """Configuration for a load test.

    Attributes:
        pattern: Load pattern type.
        initial_users: Starting number of concurrent users.
        max_users: Maximum number of concurrent users.
        ramp_up_seconds: Time to ramp up to max users.
        steady_duration_seconds: Duration of steady-state testing.
        spike_users: Number of users during spike (for spike pattern).
        spike_duration_seconds: Duration of spike.
        requests_per_user: Number of requests each user makes.
        timeout_seconds: Request timeout in seconds.
    """

    pattern: LoadPattern = LoadPattern.STEADY
    initial_users: int = 10
    max_users: int = 100
    ramp_up_seconds: float = 60.0
    steady_duration_seconds: float = 300.0
    spike_users: int = 500
    spike_duration_seconds: float = 30.0
    requests_per_user: int = 10
    timeout_seconds: float = 30.0


@dataclass
class RequestResult:
    """Result of a single request.

    Attributes:
        request_id: Unique request identifier.
        user_id: User that made the request.
        status_code: HTTP status code or result code.
        response_time_seconds: Time taken for the request.
        success: Whether the request succeeded.
        error_message: Error message if the request failed.
        timestamp: When the request was made.
        metadata: Additional request metadata.
    """

    request_id: str
    user_id: str
    status_code: int = 0
    response_time_seconds: float = 0.0
    success: bool = False
    error_message: str | None = None
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadTestResult:
    """Aggregated results of a load test.

    Attributes:
        config: The load configuration used.
        total_requests: Total number of requests made.
        successful_requests: Number of successful requests.
        failed_requests: Number of failed requests.
        requests_per_second: Achieved requests per second.
        mean_response_time: Mean response time.
        median_response_time: Median response time.
        p95_response_time: 95th percentile response time.
        p99_response_time: 99th percentile response time.
        min_response_time: Minimum response time.
        max_response_time: Maximum response time.
        error_rate: Fraction of requests that failed.
        duration_seconds: Total test duration.
        raw_results: List of individual request results.
    """

    config: LoadConfig
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    requests_per_second: float = 0.0
    mean_response_time: float = 0.0
    median_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    min_response_time: float = 0.0
    max_response_time: float = 0.0
    error_rate: float = 0.0
    duration_seconds: float = 0.0
    raw_results: list[RequestResult] = field(default_factory=list)


class LoadTarget(ABC):
    """Abstract base class for load test targets."""

    @abstractmethod
    async def send_request(self, user_id: str) -> RequestResult:
        """Send a single request.

        Args:
            user_id: The user identifier.

        Returns:
            The request result.
        """
        ...

    @abstractmethod
    async def setup(self) -> None:
        """Set up the target before testing."""
        ...

    @abstractmethod
    async def teardown(self) -> None:
        """Tear down the target after testing."""
        ...


class LoadGenerator:
    """Generates load against a target."""

    def __init__(
        self,
        target: LoadTarget,
        config: LoadConfig,
    ) -> None:
        """Initialize LoadGenerator.

        Args:
            target: The target to load test.
            config: Load configuration.
        """
        self.target = target
        self.config = config
        self._results: list[RequestResult] = []

    async def run(self) -> LoadTestResult:
        """Execute the load test.

        Returns:
            Aggregated load test results.
        """
        await self.target.setup()
        start_time = time.monotonic()

        try:
            if self.config.pattern == LoadPattern.STEADY:
                await self._run_steady()
            elif self.config.pattern == LoadPattern.RAMP_UP:
                await self._run_ramp_up()
            elif self.config.pattern == LoadPattern.SPIKE:
                await self._run_spike()
            elif self.config.pattern == LoadPattern.WAVE:
                await self._run_wave()
            elif self.config.pattern == LoadPattern.STRESS:
                await self._run_stress()
        finally:
            await self.target.teardown()

        duration = time.monotonic() - start_time
        return self._aggregate_results(duration)

    async def _run_steady(self) -> None:
        """Run steady-state load test."""
        semaphore = asyncio.Semaphore(self.config.max_users)

        async def user_session(user_id: str) -> None:
            async with semaphore:
                for i in range(self.config.requests_per_user):
                    result = await asyncio.wait_for(
                        self.target.send_request(user_id),
                        timeout=self.config.timeout_seconds,
                    )
                    self._results.append(result)

        tasks = [
            user_session(f"user_{i}")
            for i in range(self.config.max_users)
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _run_ramp_up(self) -> None:
        """Run ramp-up load test."""
        steps = 10
        users_per_step = self.config.max_users // steps
        delay_per_step = self.config.ramp_up_seconds / steps

        for step in range(steps):
            current_users = (step + 1) * users_per_step
            semaphore = asyncio.Semaphore(current_users)

            async def user_session(user_id: str) -> None:
                async with semaphore:
                    for i in range(self.config.requests_per_user):
                        result = await asyncio.wait_for(
                            self.target.send_request(user_id),
                            timeout=self.config.timeout_seconds,
                        )
                        self._results.append(result)

            tasks = [
                user_session(f"user_{i}")
                for i in range(current_users)
            ]
            await asyncio.gather(*tasks, return_exceptions=True)

            if step < steps - 1:
                await asyncio.sleep(delay_per_step)

    async def _run_spike(self) -> None:
        """Run spike load test."""
        await self._run_steady()

        semaphore = asyncio.Semaphore(self.config.spike_users)

        async def spike_user(user_id: str) -> None:
            async with semaphore:
                result = await asyncio.wait_for(
                    self.target.send_request(user_id),
                    timeout=self.config.timeout_seconds,
                )
                self._results.append(result)

        tasks = [
            spike_user(f"spike_user_{i}")
            for i in range(self.config.spike_users)
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _run_wave(self) -> None:
        """Run wave load test."""
        wave_count = 5
        for wave in range(wave_count):
            users = self.config.initial_users + (
                (self.config.max_users - self.config.initial_users) * wave // wave_count
            )
            semaphore = asyncio.Semaphore(users)

            async def user_session(user_id: str) -> None:
                async with semaphore:
                    result = await asyncio.wait_for(
                        self.target.send_request(user_id),
                        timeout=self.config.timeout_seconds,
                    )
                    self._results.append(result)

            tasks = [
                user_session(f"wave{wave}_user_{i}")
                for i in range(users)
            ]
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(5)

    async def _run_stress(self) -> None:
        """Run stress test until failure."""
        current_users = self.config.initial_users
        while current_users <= self.config.max_users * 2:
            semaphore = asyncio.Semaphore(current_users)

            async def user_session(user_id: str) -> None:
                async with semaphore:
                    result = await asyncio.wait_for(
                        self.target.send_request(user_id),
                        timeout=self.config.timeout_seconds,
                    )
                    self._results.append(result)

            tasks = [
                user_session(f"stress_user_{i}")
                for i in range(current_users)
            ]
            await asyncio.gather(*tasks, return_exceptions=True)

            recent_results = self._results[-current_users:]
            if recent_results:
                error_rate = (
                    sum(1 for r in recent_results if not r.success)
                    / len(recent_results)
                )
                if error_rate > 0.5:
                    break

            current_users = int(current_users * 1.5)

    def _aggregate_results(self, duration: float) -> LoadTestResult:
        """Aggregate raw results into a summary.

        Args:
            duration: Total test duration in seconds.

        Returns:
            Aggregated load test results.
        """
        if not self._results:
            return LoadTestResult(config=self.config, duration_seconds=duration)

        response_times = [r.response_time_seconds for r in self._results]
        successful = sum(1 for r in self._results if r.success)
        failed = len(self._results) - successful

        sorted_times = sorted(response_times)
        n = len(sorted_times)

        return LoadTestResult(
            config=self.config,
            total_requests=len(self._results),
            successful_requests=successful,
            failed_requests=failed,
            requests_per_second=len(self._results) / duration if duration > 0 else 0,
            mean_response_time=statistics.mean(response_times),
            median_response_time=statistics.median(response_times),
            p95_response_time=sorted_times[int(n * 0.95)] if n > 0 else 0,
            p99_response_time=sorted_times[int(n * 0.99)] if n > 0 else 0,
            min_response_time=min(response_times),
            max_response_time=max(response_times),
            error_rate=failed / len(self._results) if self._results else 0,
            duration_seconds=duration,
            raw_results=self._results.copy(),
        )


class LoadTestAssertions:
    """Assertions for validating load test results."""

    @staticmethod
    def assert_response_time(
        result: LoadTestResult,
        max_mean: float = 1.0,
        max_p95: float = 3.0,
        max_p99: float = 5.0,
    ) -> list[str]:
        """Assert response time thresholds.

        Args:
            result: The load test result.
            max_mean: Maximum acceptable mean response time.
            max_p95: Maximum acceptable p95 response time.
            max_p99: Maximum acceptable p99 response time.

        Returns:
            List of assertion failure messages.
        """
        failures: list[str] = []

        if result.mean_response_time > max_mean:
            failures.append(
                f"Mean response time {result.mean_response_time:.3f}s "
                f"exceeds {max_mean:.3f}s"
            )
        if result.p95_response_time > max_p95:
            failures.append(
                f"P95 response time {result.p95_response_time:.3f}s "
                f"exceeds {max_p95:.3f}s"
            )
        if result.p99_response_time > max_p99:
            failures.append(
                f"P99 response time {result.p99_response_time:.3f}s "
                f"exceeds {max_p99:.3f}s"
            )

        return failures

    @staticmethod
    def assert_error_rate(result: LoadTestResult, max_error_rate: float = 0.01) -> list[str]:
        """Assert error rate threshold.

        Args:
            result: The load test result.
            max_error_rate: Maximum acceptable error rate.

        Returns:
            List of assertion failure messages.
        """
        failures: list[str] = []

        if result.error_rate > max_error_rate:
            failures.append(
                f"Error rate {result.error_rate:.2%} exceeds {max_error_rate:.2%}"
            )

        return failures

    @staticmethod
    def assert_throughput(
        result: LoadTestResult, min_rps: float = 100.0
    ) -> list[str]:
        """Assert minimum throughput.

        Args:
            result: The load test result.
            min_rps: Minimum acceptable requests per second.

        Returns:
            List of assertion failure messages.
        """
        failures: list[str] = []

        if result.requests_per_second < min_rps:
            failures.append(
                f"Throughput {result.requests_per_second:.1f} rps "
                f"below minimum {min_rps:.1f} rps"
            )

        return failures
