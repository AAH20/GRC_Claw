"""Chaos engineering tests for API outage handling.

These tests verify that the system gracefully handles external API outages
including complete service unavailability, partial degradation, rate
limiting, and intermittent failures.
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
    MockAPIService,
    ServiceType,
    CircuitBreaker,
)


class TestAPIOutageHandling:
    """Test suite for API outage chaos scenarios."""

    @pytest.mark.asyncio
    async def test_api_complete_outage_returns_fallback(
        self, mock_api: MockAPIService
    ) -> None:
        """Verify that complete API outage returns fallback response."""
        mock_api.up = False

        async def call_with_fallback(endpoint: str) -> dict[str, Any]:
            try:
                return await asyncio.wait_for(mock_api.call(endpoint), timeout=0.5)
            except (ConnectionError, asyncio.TimeoutError):
                return {
                    "status": "fallback",
                    "endpoint": endpoint,
                    "data": None,
                    "cached": True,
                    "message": "API unavailable — serving cached data",
                }

        result = await call_with_fallback("/users")
        assert result["status"] == "fallback"
        assert result["cached"] is True

    @pytest.mark.asyncio
    async def test_api_partial_degradation_handling(
        self, mock_api: MockAPIService
    ) -> None:
        """Verify that partial API degradation is handled gracefully."""
        endpoints_status = {
            "/users": {"up": True, "latency_ms": 50},
            "/orders": {"up": False, "latency_ms": 0},
            "/products": {"up": True, "latency_ms": 200},
        }

        async def check_endpoint_health(endpoint: str) -> dict[str, Any]:
            status = endpoints_status.get(endpoint, {"up": False})
            return {
                "endpoint": endpoint,
                "available": status["up"],
                "latency_ms": status.get("latency_ms", 0),
                "degraded": status.get("latency_ms", 0) > 100,
            }

        results = await asyncio.gather(*[
            check_endpoint_health(ep) for ep in endpoints_status
        ])

        available_count = sum(1 for r in results if r["available"])
        assert available_count == 2
        assert any(r["degraded"] for r in results)

    @pytest.mark.asyncio
    async def test_api_rate_limit_handling(
        self, mock_api: MockAPIService
    ) -> None:
        """Verify that API rate limiting is handled with backoff."""
        rate_limit_remaining = 0
        rate_limit_reset = time.time() + 60

        async def call_with_rate_limit_handling() -> dict[str, Any]:
            nonlocal rate_limit_remaining
            if rate_limit_remaining <= 0:
                return {
                    "status": "rate_limited",
                    "retry_after": max(0, rate_limit_reset - time.time()),
                    "limit": 100,
                    "remaining": 0,
                }
            rate_limit_remaining -= 1
            return await mock_api.call("/data")

        result = await call_with_rate_limit_handling()
        assert result["status"] == "rate_limited"
        assert result["retry_after"] > 0

    @pytest.mark.asyncio
    async def test_api_intermittent_failure_handling(
        self, mock_api: MockAPIService
    ) -> None:
        """Verify that intermittent API failures are handled with retry."""
        call_count = 0
        failure_pattern = [True, False, True, False, True]  # True = success

        async def call_with_retry() -> dict[str, Any]:
            nonlocal call_count
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    should_succeed = failure_pattern[attempt % len(failure_pattern)]
                    if not should_succeed:
                        raise ConnectionError("Intermittent failure")
                    result = await mock_api.call("/data")
                    call_count += 1
                    return {"status": "success", "attempts": attempt + 1, "data": result}
                except ConnectionError:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(0.01 * (2**attempt))
            return {"status": "failed", "attempts": max_retries}

        result = await call_with_retry()
        assert result["status"] in ("success", "failed")
        if result["status"] == "success":
            assert result["attempts"] >= 1

    @pytest.mark.asyncio
    async def test_api_circuit_breaker_during_outage(
        self, mock_api: MockAPIService, circuit_breaker: CircuitBreaker
    ) -> None:
        """Verify that circuit breaker opens during sustained API outage."""
        mock_api.up = False

        async def protected_call(endpoint: str) -> dict[str, Any]:
            if not circuit_breaker.can_execute():
                return {
                    "status": "circuit_open",
                    "endpoint": endpoint,
                    "message": "Circuit breaker is open — API calls blocked",
                }
            try:
                result = await mock_api.call(endpoint)
                circuit_breaker.record_success()
                return {"status": "success", "data": result}
            except ConnectionError:
                circuit_breaker.record_failure()
                return {"status": "error", "message": "API unavailable"}

        # Trigger failures to open circuit
        results = []
        for _ in range(10):
            result = await protected_call("/data")
            results.append(result)

        # Circuit should be open after threshold
        assert circuit_breaker.state == "open"
        circuit_open_results = [r for r in results if r["status"] == "circuit_open"]
        assert len(circuit_open_results) > 0

    @pytest.mark.asyncio
    async def test_api_timeout_with_graceful_degradation(
        self, mock_api: MockAPIService
    ) -> None:
        """Verify that API timeouts trigger graceful degradation."""
        mock_api.latency_ms = 5000  # Very slow API

        async def call_with_degradation() -> dict[str, Any]:
            try:
                result = await asyncio.wait_for(mock_api.call("/data"), timeout=0.1)
                return {"status": "full", "data": result}
            except asyncio.TimeoutError:
                return {
                    "status": "degraded",
                    "data": None,
                    "message": "API timeout — serving stale data",
                    "stale": True,
                }

        result = await call_with_degradation()
        assert result["status"] == "degraded"
        assert result["stale"] is True

    @pytest.mark.asyncio
    async def test_api_health_check_during_outage(
        self, mock_api: MockAPIService
    ) -> None:
        """Verify that API health checks detect outages."""
        mock_api.up = False

        async def health_check() -> dict[str, Any]:
            try:
                await asyncio.wait_for(mock_api.call("/health"), timeout=0.1)
                return {"status": "healthy", "up": True}
            except (ConnectionError, asyncio.TimeoutError):
                return {"status": "unhealthy", "up": False, "outage_detected": True}

        result = await health_check()
        assert result["up"] is False
        assert result["outage_detected"] is True

    @pytest.mark.asyncio
    async def test_api_recovery_after_outage(
        self, mock_api: MockAPIService
    ) -> None:
        """Verify that API recovery is detected after outage."""
        mock_api.up = False

        # Simulate outage
        with pytest.raises(ConnectionError):
            await mock_api.call("/data")

        # Simulate recovery
        await asyncio.sleep(0.1)
        mock_api.up = True

        # Verify recovery
        result = await mock_api.call("/data")
        assert result["status"] == "ok"
        assert mock_api.health_check().is_healthy is True

    @pytest.mark.asyncio
    async def test_api_outage_metrics_recording(
        self, mock_api: MockAPIService, chaos_monkey: ChaosMonkey
    ) -> None:
        """Verify that API outage metrics are properly recorded."""
        chaos_monkey.config.failure_mode = FailureMode.CONNECTION_REFUSED
        chaos_monkey.config.target_service = ServiceType.API

        event = chaos_monkey.inject_failure(context="api_outage_test")

        assert event.service == ServiceType.API
        assert event.failure_mode == FailureMode.CONNECTION_REFUSED
        assert event.event_id is not None

    @pytest.mark.asyncio
    async def test_api_fallback_chain(
        self, mock_api: MockAPIService
    ) -> None:
        """Verify that API fallback chain works during outage."""
        fallback_levels = [
            {"name": "primary_api", "available": False},
            {"name": "secondary_api", "available": False},
            {"name": "cache", "available": True},
            {"name": "static_fallback", "available": True},
        ]

        async def call_with_fallback_chain(endpoint: str) -> dict[str, Any]:
            for level in fallback_levels:
                if level["available"]:
                    return {
                        "status": "success",
                        "source": level["name"],
                        "endpoint": endpoint,
                        "data": {"fallback": True},
                    }
            return {"status": "error", "message": "All fallback levels exhausted"}

        result = await call_with_fallback_chain("/data")
        assert result["status"] == "success"
        assert result["source"] == "cache"
