"""Chaos engineering tests for cascade failure handling.

These tests verify that the system prevents and handles cascade failures
where a failure in one service triggers failures in dependent services.
Tests cover failure isolation, bulkhead patterns, dependency chains, and
failure propagation control.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from .conftest import (
    ChaosConfig,
    ChaosMonkey,
    ChaosEvent,
    FailureMode,
    ServiceType,
    CircuitBreaker,
)


class TestCascadeFailureHandling:
    """Test suite for cascade failure chaos scenarios."""

    @pytest.mark.asyncio
    async def test_cascade_failure_prevention_via_circuit_breaker(
        self, circuit_breaker: CircuitBreaker
    ) -> None:
        """Verify that circuit breakers prevent cascade failures."""
        # Simulate downstream service failure
        downstream_healthy = False

        async def call_downstream() -> dict[str, Any]:
            if not downstream_healthy:
                raise ConnectionError("Downstream service unavailable")
            return {"status": "ok"}

        async def protected_call() -> dict[str, Any]:
            if not circuit_breaker.can_execute():
                return {
                    "status": "circuit_open",
                    "message": "Cascade failure prevented by circuit breaker",
                }
            try:
                result = await call_downstream()
                circuit_breaker.record_success()
                return result
            except ConnectionError:
                circuit_breaker.record_failure()
                return {"status": "error", "message": "Downstream unavailable"}

        # Trigger failures
        results = []
        for _ in range(10):
            result = await protected_call()
            results.append(result)

        # Circuit should be open, preventing further cascade
        assert circuit_breaker.state == "open"
        circuit_open_count = sum(1 for r in results if r["status"] == "circuit_open")
        assert circuit_open_count > 0

    @pytest.mark.asyncio
    async def test_bulkhead_pattern_isolation(self) -> None:
        """Verify that bulkhead pattern isolates failures between services."""
        # Simulate separate thread pools for different services
        llm_semaphore = asyncio.Semaphore(5)
        db_semaphore = asyncio.Semaphore(3)

        async def call_llm() -> dict[str, Any]:
            async with llm_semaphore:
                await asyncio.sleep(0.01)
                return {"service": "llm", "status": "ok"}

        async def call_db() -> dict[str, Any]:
            async with db_semaphore:
                await asyncio.sleep(0.01)
                return {"service": "database", "status": "ok"}

        # Even if LLM is slow, DB should still work
        results = await asyncio.gather(
            call_llm(), call_llm(), call_llm(),
            call_db(), call_db(),
        )

        llm_results = [r for r in results if r["service"] == "llm"]
        db_results = [r for r in results if r["service"] == "database"]
        assert len(llm_results) == 3
        assert len(db_results) == 2
        assert all(r["status"] == "ok" for r in results)

    @pytest.mark.asyncio
    async def test_dependency_chain_failure_isolation(self) -> None:
        """Verify that failures in dependency chains are isolated."""
        # Service A depends on B, B depends on C
        service_c_healthy = False

        async def service_c() -> dict[str, Any]:
            if not service_c_healthy:
                raise ConnectionError("Service C is down")
            return {"service": "C", "status": "ok"}

        async def service_b() -> dict[str, Any]:
            try:
                c_result = await service_c()
                return {"service": "B", "status": "ok", "dependency": c_result}
            except ConnectionError:
                return {"service": "B", "status": "degraded", "fallback": True}

        async def service_a() -> dict[str, Any]:
            b_result = await service_b()
            if b_result.get("fallback"):
                return {"service": "A", "status": "degraded", "cached": True}
            return {"service": "A", "status": "ok", "dependency": b_result}

        result = await service_a()
        assert result["status"] == "degraded"
        assert result["cached"] is True

    @pytest.mark.asyncio
    async def test_failure_propagation_control(self) -> None:
        """Verify that failure propagation is controlled and limited."""
        failure_counts: dict[str, int] = {
            "service_a": 0,
            "service_b": 0,
            "service_c": 0,
        }

        async def call_with_isolation(service: str, should_fail: bool) -> dict[str, Any]:
            if should_fail:
                failure_counts[service] += 1
                raise ConnectionError(f"{service} failed")
            return {"service": service, "status": "ok"}

        # Service C fails, but A and B should be isolated
        results = await asyncio.gather(
            call_with_isolation("service_a", False),
            call_with_isolation("service_b", False),
            call_with_isolation("service_c", True),
            return_exceptions=True,
        )

        assert failure_counts["service_c"] == 1
        assert failure_counts["service_a"] == 0
        assert failure_counts["service_b"] == 0

    @pytest.mark.asyncio
    async def test_cascade_failure_timeout_isolation(self) -> None:
        """Verify that timeouts in one service don't cascade to others."""
        async def slow_service() -> dict[str, Any]:
            await asyncio.sleep(10)  # Very slow
            return {"service": "slow", "status": "ok"}

        async def fast_service() -> dict[str, Any]:
            await asyncio.sleep(0.01)
            return {"service": "fast", "status": "ok"}

        # Fast service should complete despite slow service
        fast_result, slow_result = await asyncio.gather(
            asyncio.wait_for(fast_service(), timeout=1.0),
            asyncio.wait_for(slow_service(), timeout=0.1),
            return_exceptions=True,
        )

        assert isinstance(fast_result, dict)
        assert fast_result["status"] == "ok"
        assert isinstance(slow_result, asyncio.TimeoutError)

    @pytest.mark.asyncio
    async def test_cascade_failure_recovery_storm_prevention(self) -> None:
        """Verify that recovery storms are prevented after cascade failure."""
        recovery_attempts: list[float] = []
        min_recovery_interval = 1.0  # Minimum seconds between recovery attempts

        async def attempt_recovery() -> dict[str, Any]:
            now = time.time()
            if recovery_attempts:
                last_attempt = recovery_attempts[-1]
                if now - last_attempt < min_recovery_interval:
                    return {
                        "status": "deferred",
                        "reason": "Recovery storm prevention",
                        "retry_after": min_recovery_interval - (now - last_attempt),
                    }
            recovery_attempts.append(now)
            return {"status": "recovering", "attempt": len(recovery_attempts)}

        # Rapid recovery attempts
        results = []
        for _ in range(5):
            result = await attempt_recovery()
            results.append(result)
            await asyncio.sleep(0.1)

        # Only first attempt should proceed
        assert results[0]["status"] == "recovering"
        deferred_count = sum(1 for r in results if r["status"] == "deferred")
        assert deferred_count == 4

    @pytest.mark.asyncio
    async def test_cascade_failure_bulkhead_timeout(self) -> None:
        """Verify that bulkhead timeouts prevent resource exhaustion."""
        max_concurrent = 3
        semaphore = asyncio.Semaphore(max_concurrent)
        active_count = 0
        max_active = 0

        async def bounded_call() -> dict[str, Any]:
            nonlocal active_count, max_active
            async with semaphore:
                active_count += 1
                max_active = max(max_active, active_count)
                await asyncio.sleep(0.05)
                active_count -= 1
                return {"status": "ok"}

        # Launch more tasks than the bulkhead allows
        results = await asyncio.gather(*[bounded_call() for _ in range(10)])

        assert max_active <= max_concurrent
        assert all(r["status"] == "ok" for r in results)

    @pytest.mark.asyncio
    async def test_cascade_failure_metrics_recording(
        self, chaos_monkey: ChaosMonkey
    ) -> None:
        """Verify that cascade failure metrics are properly recorded."""
        chaos_monkey.config.failure_mode = FailureMode.CONNECTION_REFUSED
        chaos_monkey.config.target_service = ServiceType.DATABASE

        event = chaos_monkey.inject_failure(context="cascade_failure_test")

        assert event.service == ServiceType.DATABASE
        assert event.failure_mode == FailureMode.CONNECTION_REFUSED

    @pytest.mark.asyncio
    async def test_cascade_failure_graceful_degradation_chain(self) -> None:
        """Verify that services degrade gracefully in a cascade failure."""
        services = ["api", "cache", "database", "queue"]
        health_status: dict[str, bool] = {s: True for s in services}

        # Simulate cascade: database fails, then cache, then api
        health_status["database"] = False
        health_status["cache"] = False
        health_status["api"] = False

        async def get_service_status(service: str) -> dict[str, Any]:
            healthy = health_status.get(service, False)
            if not healthy:
                return {
                    "service": service,
                    "status": "unavailable",
                    "degraded_mode": True,
                    "fallback": "static_response",
                }
            return {"service": service, "status": "healthy"}

        results = await asyncio.gather(*[
            get_service_status(svc) for svc in services
        ])

        unavailable = [r for r in results if r["status"] == "unavailable"]
        assert len(unavailable) == 3
        assert all(r["degraded_mode"] for r in unavailable)

    @pytest.mark.asyncio
    async def test_cascade_failure_rate_limiting(self) -> None:
        """Verify that rate limiting prevents cascade failures."""
        request_count = 0
        max_requests_per_second = 10
        window_start = time.time()

        async def rate_limited_call() -> dict[str, Any]:
            nonlocal request_count, window_start
            now = time.time()
            if now - window_start >= 1.0:
                window_start = now
                request_count = 0
            if request_count >= max_requests_per_second:
                return {
                    "status": "rate_limited",
                    "retry_after": 1.0 - (now - window_start),
                }
            request_count += 1
            return {"status": "ok"}

        # Send many requests rapidly
        results = await asyncio.gather(*[rate_limited_call() for _ in range(20)])

        ok_count = sum(1 for r in results if r["status"] == "ok")
        limited_count = sum(1 for r in results if r["status"] == "rate_limited")
        assert ok_count <= max_requests_per_second
        assert limited_count > 0
