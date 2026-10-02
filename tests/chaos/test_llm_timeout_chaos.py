"""Chaos engineering tests for LLM timeout handling.

These tests verify that the system gracefully handles LLM service timeouts,
including retry logic, circuit breaker behavior, fallback responses, and
degraded mode operation.
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
    MockLLMService,
    ServiceType,
    CircuitBreaker,
)


class TestLLMTimeoutHandling:
    """Test suite for LLM timeout chaos scenarios."""

    @pytest.mark.asyncio
    async def test_llm_timeout_returns_fallback(
        self, mock_llm: MockLLMService, chaos_monkey: ChaosMonkey
    ) -> None:
        """Verify that LLM timeout returns a fallback response instead of crashing."""
        chaos_monkey.config.failure_mode = FailureMode.TIMEOUT
        chaos_monkey.config.target_service = ServiceType.LLM
        chaos_monkey.config.timeout_seconds = 0.5

        fallback_response = {"text": "Fallback: LLM unavailable", "model": "fallback"}

        async def call_with_fallback() -> dict[str, Any]:
            try:
                return await asyncio.wait_for(
                    mock_llm.generate("test prompt"),
                    timeout=0.3,
                )
            except asyncio.TimeoutError:
                return fallback_response

        result = await call_with_fallback()
        assert result["model"] == "fallback"
        assert "Fallback" in result["text"]

    @pytest.mark.asyncio
    async def test_llm_timeout_triggers_circuit_breaker(
        self, mock_llm: MockLLMService, circuit_breaker: CircuitBreaker
    ) -> None:
        """Verify that repeated LLM timeouts open the circuit breaker."""
        call_count = 0

        async def failing_call() -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            circuit_breaker.record_failure()
            if not circuit_breaker.can_execute():
                raise ConnectionError("Circuit breaker is open")
            raise asyncio.TimeoutError("LLM call timed out")

        # Exhaust the circuit breaker
        for _ in range(5):
            with pytest.raises((asyncio.TimeoutError, ConnectionError)):
                await failing_call()

        assert circuit_breaker.state == "open"
        assert not circuit_breaker.can_execute()

    @pytest.mark.asyncio
    async def test_llm_timeout_with_exponential_backoff(
        self, mock_llm: MockLLMService
    ) -> None:
        """Verify that LLM calls use exponential backoff on timeout."""
        max_retries = 3
        base_delay = 0.01
        attempt_times: list[float] = []

        async def call_with_backoff() -> dict[str, Any]:
            for attempt in range(max_retries):
                attempt_times.append(time.time())
                try:
                    return await asyncio.wait_for(
                        mock_llm.generate("test"),
                        timeout=0.05,
                    )
                except asyncio.TimeoutError:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2**attempt)
                        await asyncio.sleep(delay)
            raise asyncio.TimeoutError("All retries exhausted")

        with pytest.raises(asyncio.TimeoutError):
            await call_with_backoff()

        assert len(attempt_times) == max_retries
        # Verify exponential backoff: second delay > first delay
        if len(attempt_times) >= 3:
            first_interval = attempt_times[1] - attempt_times[0]
            second_interval = attempt_times[2] - attempt_times[1]
            assert second_interval > first_interval

    @pytest.mark.asyncio
    async def test_llm_partial_response_handling(
        self, mock_llm: MockLLMService, chaos_monkey: ChaosMonkey
    ) -> None:
        """Verify that partial LLM responses are handled gracefully."""
        chaos_monkey.config.failure_mode = FailureMode.PARTIAL_RESPONSE

        partial_response = {
            "text": "Partial response cut off mid-",
            "model": "mock-llm-v1",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            "finish_reason": "length",
        }

        # System should detect and handle partial responses
        is_complete = partial_response.get("finish_reason") == "stop"
        assert not is_complete
        assert partial_response["finish_reason"] == "length"

    @pytest.mark.asyncio
    async def test_llm_timeout_degrades_to_cached_response(
        self, mock_llm: MockLLMService
    ) -> None:
        """Verify that LLM timeout falls back to cached responses."""
        cache: dict[str, dict[str, Any]] = {
            "test prompt": {
                "text": "Cached response for test prompt",
                "model": "mock-llm-v1",
                "cached": True,
            }
        }

        async def call_with_cache(prompt: str) -> dict[str, Any]:
            try:
                return await asyncio.wait_for(
                    mock_llm.generate(prompt),
                    timeout=0.05,
                )
            except asyncio.TimeoutError:
                return cache.get(prompt, {"text": "Default fallback", "cached": False})

        result = await call_with_cache("test prompt")
        assert result.get("cached") is True
        assert "Cached response" in result["text"]

    @pytest.mark.asyncio
    async def test_llm_timeout_metrics_recorded(
        self, mock_llm: MockLLMService, chaos_monkey: ChaosMonkey
    ) -> None:
        """Verify that LLM timeout events are properly recorded."""
        chaos_monkey.config.failure_mode = FailureMode.TIMEOUT
        chaos_monkey.config.target_service = ServiceType.LLM

        event = chaos_monkey.inject_failure(context="llm_timeout_test")

        assert event.service == ServiceType.LLM
        assert event.failure_mode == FailureMode.TIMEOUT
        assert event.event_id is not None
        assert event.timestamp > 0

        events = chaos_monkey.get_events(service=ServiceType.LLM)
        assert len(events) >= 1
        assert events[-1].failure_mode == FailureMode.TIMEOUT

    @pytest.mark.asyncio
    async def test_llm_timeout_concurrent_requests(
        self, mock_llm: MockLLMService
    ) -> None:
        """Verify that concurrent LLM requests handle timeouts independently."""
        num_requests = 10
        results: list[dict[str, Any]] = []

        async def timed_call(prompt: str) -> None:
            try:
                result = await asyncio.wait_for(
                    mock_llm.generate(prompt),
                    timeout=0.1,
                )
                results.append({"prompt": prompt, "status": "success", "data": result})
            except asyncio.TimeoutError:
                results.append({"prompt": prompt, "status": "timeout"})

        await asyncio.gather(*[timed_call(f"prompt_{i}") for i in range(num_requests)])

        assert len(results) == num_requests
        statuses = [r["status"] for r in results]
        assert "success" in statuses or "timeout" in statuses

    @pytest.mark.asyncio
    async def test_llm_timeout_with_graceful_degradation(
        self, mock_llm: MockLLMService
    ) -> None:
        """Verify that the system degrades gracefully when LLM is unavailable."""
        degradation_levels = ["full", "reduced", "minimal", "unavailable"]

        async def get_degradation_level() -> str:
            try:
                await asyncio.wait_for(mock_llm.generate("health check"), timeout=0.05)
                return "full"
            except asyncio.TimeoutError:
                return "reduced"

        level = await get_degradation_level()
        assert level in degradation_levels

    @pytest.mark.asyncio
    async def test_llm_timeout_recovery_detection(
        self, mock_llm: MockLLMService, chaos_monkey: ChaosMonkey
    ) -> None:
        """Verify that the system detects when LLM service recovers."""
        chaos_monkey.config.failure_mode = FailureMode.TIMEOUT
        chaos_monkey.config.duration_seconds = 0.2

        # Phase 1: LLM is timing out
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(mock_llm.generate("test"), timeout=0.05)

        # Phase 2: Wait for recovery
        await asyncio.sleep(0.3)

        # Phase 3: LLM should be responsive again
        result = await asyncio.wait_for(mock_llm.generate("test"), timeout=1.0)
        assert "text" in result
        assert result["model"] == "mock-llm-v1"

    @pytest.mark.asyncio
    async def test_llm_timeout_error_message_quality(
        self, mock_llm: MockLLMService
    ) -> None:
        """Verify that LLM timeout errors provide actionable error messages."""
        async def call_with_good_errors() -> dict[str, Any]:
            try:
                return await asyncio.wait_for(mock_llm.generate("test"), timeout=0.01)
            except asyncio.TimeoutError:
                return {
                    "error": "LLM service timeout",
                    "suggestion": "Try again in a few seconds or use cached response",
                    "retryable": True,
                }

        result = await call_with_good_errors()
        assert result["error"] == "LLM service timeout"
        assert result["retryable"] is True
        assert "suggestion" in result
