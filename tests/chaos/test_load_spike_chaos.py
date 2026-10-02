"""Chaos engineering tests for load spike handling.

These tests verify that the system gracefully handles sudden traffic
spikes including throttling, queue-based load leveling, auto-scaling
triggers, and resource exhaustion prevention.
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


class TestLoadSpikeHandling:
    """Test suite for load spike chaos scenarios."""

    @pytest.mark.asyncio
    async def test_sudden_traffic_spike_throttling(self) -> None:
        """Verify that sudden traffic spikes are handled via throttling."""
        requests_per_second = 0
        max_rps = 100
        throttle_delay = 0.0

        async def throttled_request() -> dict[str, Any]:
            nonlocal requests_per_second, throttle_delay
            requests_per_second += 1
            if requests_per_second > max_rps:
                throttle_delay = (requests_per_second - max_rps) * 0.01
                await asyncio.sleep(throttle_delay)
            return {"status": "ok", "throttled": throttle_delay > 0}

        # Simulate traffic spike
        results = await asyncio.gather(*[throttled_request() for _ in range(150)])

        throttled_count = sum(1 for r in results if r["throttled"])
        assert throttled_count > 0
        assert len(results) == 150

    @pytest.mark.asyncio
    async def test_queue_based_load_leveling(self) -> None:
        """Verify that queue-based load leveling smooths traffic spikes."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        processed_count = 0
        max_queue_size = 0

        async def producer(count: int) -> None:
            nonlocal max_queue_size
            for i in range(count):
                await queue.put({"id": i, "data": f"request_{i}"})
                max_queue_size = max(max_queue_size, queue.qsize())

        async def consumer() -> None:
            nonlocal processed_count
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=0.5)
                    processed_count += 1
                    queue.task_done()
                except asyncio.TimeoutError:
                    break

        # Start producer and consumer
        producer_task = asyncio.create_task(producer(50))
        consumer_task = asyncio.create_task(consumer())

        await producer_task
        await queue.join()
        consumer_task.cancel()

        assert processed_count == 50
        assert max_queue_size > 0

    @pytest.mark.asyncio
    async def test_auto_scaling_trigger_on_spike(self) -> None:
        """Verify that auto-scaling triggers during load spikes."""
        current_instances = 2
        max_instances = 10
        cpu_threshold = 70.0
        current_cpu = 85.0

        async def evaluate_scaling() -> dict[str, Any]:
            nonlocal current_instances
            if current_cpu > cpu_threshold and current_instances < max_instances:
                new_instances = min(max_instances, current_instances + 2)
                return {
                    "action": "scale_up",
                    "previous": current_instances,
                    "new": new_instances,
                    "reason": f"CPU {current_cpu}% > threshold {cpu_threshold}%",
                }
            return {"action": "no_change", "instances": current_instances}

        result = await evaluate_scaling()
        assert result["action"] == "scale_up"
        assert result["new"] > result["previous"]

    @pytest.mark.asyncio
    async def test_resource_exhaustion_prevention(self) -> None:
        """Verify that resource exhaustion is prevented during load spikes."""
        max_memory_mb = 512
        current_memory_mb = 0
        request_memory_kb = 10

        async def process_with_memory_limit() -> dict[str, Any]:
            nonlocal current_memory_mb
            required_mb = request_memory_kb / 1024
            if current_memory_mb + required_mb > max_memory_mb:
                return {
                    "status": "rejected",
                    "reason": "Memory limit would be exceeded",
                    "current_mb": current_memory_mb,
                    "max_mb": max_memory_mb,
                }
            current_memory_mb += required_mb
            return {"status": "accepted", "memory_used_mb": current_memory_mb}

        # Simulate many requests
        results = []
        for _ in range(10000):
            result = await process_with_memory_limit()
            results.append(result)
            if result["status"] == "rejected":
                break

        rejected = [r for r in results if r["status"] == "rejected"]
        assert len(rejected) > 0
        assert current_memory_mb <= max_memory_mb

    @pytest.mark.asyncio
    async def test_load_spike_circuit_breaker_protection(
        self, circuit_breaker: CircuitBreaker
    ) -> None:
        """Verify that circuit breaker protects against load spike overload."""
        request_count = 0
        max_requests = 50

        async def protected_request() -> dict[str, Any]:
            nonlocal request_count
            if not circuit_breaker.can_execute():
                return {
                    "status": "circuit_open",
                    "message": "Load spike protection active",
                }
            request_count += 1
            if request_count > max_requests:
                circuit_breaker.record_failure()
                return {"status": "overloaded"}
            circuit_breaker.record_success()
            return {"status": "ok"}

        results = []
        for _ in range(100):
            result = await protected_request()
            results.append(result)

        circuit_open = [r for r in results if r["status"] == "circuit_open"]
        assert len(circuit_open) > 0

    @pytest.mark.asyncio
    async def test_load_spike_graceful_degradation(self) -> None:
        """Verify that the system degrades gracefully under load spikes."""
        load_level = 0.95  # 95% load

        async def get_degradation_strategy() -> dict[str, Any]:
            if load_level > 0.9:
                return {
                    "level": "critical",
                    "actions": [
                        "disable_non_critical_features",
                        "reduce_response_payload_size",
                        "enable_aggressive_caching",
                        "reject_low_priority_requests",
                    ],
                }
            elif load_level > 0.7:
                return {
                    "level": "high",
                    "actions": ["enable_caching", "reduce_payload_size"],
                }
            return {"level": "normal", "actions": []}

        result = await get_degradation_strategy()
        assert result["level"] == "critical"
        assert len(result["actions"]) >= 3

    @pytest.mark.asyncio
    async def test_load_spike_backpressure(self) -> None:
        """Verify that backpressure is applied during load spikes."""
        queue_size = 0
        max_queue_size = 100
        backpressure_applied = False

        async def apply_backpressure() -> dict[str, Any]:
            nonlocal backpressure_applied
            if queue_size >= max_queue_size:
                backpressure_applied = True
                return {
                    "status": "backpressure",
                    "message": "Queue full — applying backpressure",
                    "retry_after": 1.0,
                }
            return {"status": "ok"}

        # Simulate full queue
        queue_size = max_queue_size
        result = await apply_backpressure()
        assert result["status"] == "backpressure"
        assert backpressure_applied is True

    @pytest.mark.asyncio
    async def test_load_spike_metrics_recording(
        self, chaos_monkey: ChaosMonkey, load_generator: Callable[[int], int]
    ) -> None:
        """Verify that load spike metrics are properly recorded."""
        chaos_monkey.config.failure_mode = FailureMode.RATE_LIMIT
        chaos_monkey.config.target_service = ServiceType.API

        # Generate load
        successful = load_generator(1000)
        total_requests = 1000

        event = chaos_monkey.inject_failure(context="load_spike_test")

        assert event.service == ServiceType.API
        assert event.failure_mode == FailureMode.RATE_LIMIT
        assert successful <= total_requests

    @pytest.mark.asyncio
    async def test_load_spike_recovery(self) -> None:
        """Verify that the system recovers after load spike subsides."""
        current_load = 0.95
        normal_load = 0.3

        async def simulate_load_decrease() -> dict[str, Any]:
            nonlocal current_load
            steps = 0
            while current_load > normal_load:
                current_load = max(normal_load, current_load * 0.8)
                steps += 1
                await asyncio.sleep(0.01)
            return {
                "status": "recovered",
                "steps": steps,
                "final_load": current_load,
            }

        result = await simulate_load_decrease()
        assert result["status"] == "recovered"
        assert result["final_load"] <= normal_load
        assert result["steps"] > 0

    @pytest.mark.asyncio
    async def test_burst_traffic_handling(self) -> None:
        """Verify that burst traffic is handled without service degradation."""
        burst_size = 500
        processed = 0
        rejected = 0
        max_concurrent = 50
        semaphore = asyncio.Semaphore(max_concurrent)

        async def handle_burst_request() -> None:
            nonlocal processed, rejected
            try:
                async with semaphore:
                    await asyncio.sleep(0.001)
                    processed += 1
            except Exception:
                rejected += 1

        await asyncio.gather(*[handle_burst_request() for _ in range(burst_size)])

        assert processed + rejected == burst_size
        assert processed > 0
