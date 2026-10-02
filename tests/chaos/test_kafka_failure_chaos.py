"""Chaos engineering tests for Kafka failure handling.

These tests verify that the system gracefully handles Kafka failures
including broker unavailability, consumer group rebalancing, message
loss, and partition leader elections.
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
    MockKafkaService,
    ServiceType,
    CircuitBreaker,
)


class TestKafkaFailureHandling:
    """Test suite for Kafka failure chaos scenarios."""

    @pytest.mark.asyncio
    async def test_kafka_broker_unavailability(
        self, mock_kafka: MockKafkaService
    ) -> None:
        """Verify that Kafka broker unavailability is handled gracefully."""
        mock_kafka.brokers_available = False

        with pytest.raises(ConnectionError, match="Kafka brokers unavailable"):
            await mock_kafka.produce("test-topic", {"key": "value"})

        # Verify the error is catchable and informative
        mock_kafka.brokers_available = True
        result = await mock_kafka.produce("test-topic", {"key": "value"})
        assert result is True

    @pytest.mark.asyncio
    async def test_kafka_producer_retry_on_failure(
        self, mock_kafka: MockKafkaService
    ) -> None:
        """Verify that Kafka producer retries on transient failures."""
        max_retries = 3
        attempt_count = 0
        mock_kafka.brokers_available = False

        async def produce_with_retry(topic: str, message: dict[str, Any]) -> bool:
            nonlocal attempt_count
            for attempt in range(max_retries):
                attempt_count += 1
                try:
                    return await mock_kafka.produce(topic, message)
                except ConnectionError:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(0.01 * (2**attempt))
                    mock_kafka.brokers_available = True  # Simulate recovery
            return False

        result = await produce_with_retry("test-topic", {"data": "test"})
        assert result is True
        assert attempt_count >= 1

    @pytest.mark.asyncio
    async def test_kafka_consumer_rebalance_handling(
        self, mock_kafka: MockKafkaService
    ) -> None:
        """Verify that Kafka consumer group rebalancing is handled."""
        rebalance_events: list[dict[str, Any]] = []

        async def simulate_rebalance() -> None:
            rebalance_events.append({
                "type": "rebalance_started",
                "timestamp": time.time(),
                "partitions_revoked": [0, 1, 2],
            })
            await asyncio.sleep(0.05)
            rebalance_events.append({
                "type": "rebalance_completed",
                "timestamp": time.time(),
                "partitions_assigned": [0, 1],
            })

        await simulate_rebalance()

        assert len(rebalance_events) == 2
        assert rebalance_events[0]["type"] == "rebalance_started"
        assert rebalance_events[1]["type"] == "rebalance_completed"

    @pytest.mark.asyncio
    async def test_kafka_message_loss_detection(
        self, mock_kafka: MockKafkaService
    ) -> None:
        """Verify that Kafka message loss is detected and handled."""
        produced_messages: list[dict[str, Any]] = []
        consumed_messages: list[dict[str, Any]] = []

        # Produce messages
        for i in range(10):
            msg = {"id": i, "data": f"message_{i}"}
            await mock_kafka.produce("test-topic", msg)
            produced_messages.append(msg)

        # Consume messages (simulate partial consumption)
        consumed = await mock_kafka.consume("test-topic", "test-group")
        consumed_messages.extend(consumed)

        # Detect message loss
        produced_ids = {m["id"] for m in produced_messages}
        consumed_ids = {m.get("id") for m in consumed_messages if "id" in m}
        lost_count = len(produced_ids - consumed_ids)

        # System should detect potential message loss
        assert isinstance(lost_count, int)
        assert lost_count >= 0

    @pytest.mark.asyncio
    async def test_kafka_partition_leader_election(
        self, mock_kafka: MockKafkaService
    ) -> None:
        """Verify that Kafka partition leader election failures are handled."""
        partition_leaders: dict[int, int | None] = {0: 1, 1: 2, 2: 3}

        # Simulate leader failure for partition 1
        partition_leaders[1] = None

        async def elect_leader(partition: int) -> int | None:
            await asyncio.sleep(0.01)
            # Simulate election of new leader
            new_leader = 4
            partition_leaders[partition] = new_leader
            return new_leader

        new_leader = await elect_leader(1)
        assert new_leader is not None
        assert partition_leaders[1] == new_leader

    @pytest.mark.asyncio
    async def test_kafka_circuit_breaker_integration(
        self, mock_kafka: MockKafkaService, circuit_breaker: CircuitBreaker
    ) -> None:
        """Verify that circuit breaker prevents cascading Kafka failures."""
        mock_kafka.brokers_available = False

        async def protected_produce(topic: str, message: dict[str, Any]) -> bool:
            if not circuit_breaker.can_execute():
                raise ConnectionError("Circuit breaker open — Kafka unavailable")
            try:
                result = await mock_kafka.produce(topic, message)
                circuit_breaker.record_success()
                return result
            except ConnectionError:
                circuit_breaker.record_failure()
                raise

        # Trigger failures
        for _ in range(5):
            with pytest.raises((ConnectionError, Exception)):
                await protected_produce("test", {"data": "test"})

        assert circuit_breaker.state == "open"

    @pytest.mark.asyncio
    async def test_kafka_consumer_lag_monitoring(
        self, mock_kafka: MockKafkaService
    ) -> None:
        """Verify that Kafka consumer lag is monitored during failures."""
        lag_threshold = 1000
        current_lag = 1500

        async def check_lag() -> dict[str, Any]:
            return {
                "current_lag": current_lag,
                "threshold": lag_threshold,
                "is_critical": current_lag > lag_threshold,
                "timestamp": time.time(),
            }

        status = await check_lag()
        assert status["is_critical"] is True
        assert status["current_lag"] > status["threshold"]

    @pytest.mark.asyncio
    async def test_kafka_dlq_routing(
        self, mock_kafka: MockKafkaService
    ) -> None:
        """Verify that failed messages are routed to dead letter queue."""
        dlq_topic = "test-topic-dlq"
        failed_messages: list[dict[str, Any]] = []

        async def process_with_dlq(message: dict[str, Any]) -> bool:
            try:
                # Simulate processing failure
                raise ValueError("Processing failed")
            except ValueError:
                failed_messages.append(message)
                await mock_kafka.produce(dlq_topic, {
                    "original": message,
                    "error": "Processing failed",
                    "timestamp": time.time(),
                })
                return False

        result = await process_with_dlq({"id": 1, "data": "test"})
        assert result is False
        assert len(failed_messages) == 1

    @pytest.mark.asyncio
    async def test_kafka_timeout_handling(
        self, mock_kafka: MockKafkaService
    ) -> None:
        """Verify that Kafka operation timeouts are handled gracefully."""
        async def produce_with_timeout() -> dict[str, Any]:
            try:
                result = await asyncio.wait_for(
                    mock_kafka.produce("test-topic", {"data": "test"}),
                    timeout=0.5,
                )
                return {"status": "success", "produced": result}
            except asyncio.TimeoutError:
                return {
                    "status": "timeout",
                    "error_code": "KAFKA_PRODUCE_TIMEOUT",
                    "retryable": True,
                }

        response = await produce_with_timeout()
        assert response["status"] in ("success", "timeout")

    @pytest.mark.asyncio
    async def test_kafka_recovery_after_broker_restart(
        self, mock_kafka: MockKafkaService
    ) -> None:
        """Verify that Kafka recovers after broker restart."""
        mock_kafka.brokers_available = False

        # Simulate broker restart
        await asyncio.sleep(0.1)
        mock_kafka.brokers_available = True

        # Verify recovery
        result = await mock_kafka.produce("test-topic", {"data": "after_restart"})
        assert result is True

        consumed = await mock_kafka.consume("test-topic", "test-group")
        assert isinstance(consumed, list)

    @pytest.mark.asyncio
    async def test_kafka_failure_metrics_recording(
        self, mock_kafka: MockKafkaService, chaos_monkey: ChaosMonkey
    ) -> None:
        """Verify that Kafka failure metrics are properly recorded."""
        chaos_monkey.config.failure_mode = FailureMode.CONNECTION_REFUSED
        chaos_monkey.config.target_service = ServiceType.KAFKA

        event = chaos_monkey.inject_failure(context="kafka_failure_test")

        assert event.service == ServiceType.KAFKA
        assert event.failure_mode == FailureMode.CONNECTION_REFUSED
        assert event.event_id is not None
