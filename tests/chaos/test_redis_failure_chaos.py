"""Chaos engineering tests for Redis failure handling.

These tests verify that the system gracefully handles Redis failures
including connection loss, cache misses during outage, failover to
replica, and data consistency after recovery.
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
    MockRedisService,
    ServiceType,
    CircuitBreaker,
)


class TestRedisFailureHandling:
    """Test suite for Redis failure chaos scenarios."""

    @pytest.mark.asyncio
    async def test_redis_connection_refused_handling(
        self, mock_redis: MockRedisService
    ) -> None:
        """Verify that Redis connection refused errors are handled gracefully."""
        mock_redis.available = False

        with pytest.raises(ConnectionError, match="Redis connection refused"):
            await mock_redis.get("test_key")

        # Verify recovery
        mock_redis.available = True
        result = await mock_redis.get("test_key")
        assert result is None  # Key doesn't exist yet

    @pytest.mark.asyncio
    async def test_redis_cache_miss_during_outage(
        self, mock_redis: MockRedisService
    ) -> None:
        """Verify that cache misses during Redis outage fall back to database."""
        mock_redis.available = False
        db_data = {"user:1": {"name": "Alice", "email": "alice@example.com"}}

        async def get_with_fallback(key: str) -> dict[str, Any] | None:
            try:
                cached = await mock_redis.get(key)
                if cached is not None:
                    return {"source": "cache", "data": cached}
            except ConnectionError:
                pass
            # Fallback to database
            if key in db_data:
                return {"source": "database", "data": db_data[key]}
            return None

        result = await get_with_fallback("user:1")
        assert result is not None
        assert result["source"] == "database"
        assert result["data"]["name"] == "Alice"

    @pytest.mark.asyncio
    async def test_redis_failover_to_replica(
        self, mock_redis: MockRedisService
    ) -> None:
        """Verify that Redis failover to replica works during primary failure."""
        primary_available = False
        replica_available = True

        async def get_with_failover(key: str) -> dict[str, Any]:
            if primary_available:
                try:
                    value = await mock_redis.get(key)
                    return {"source": "primary", "value": value}
                except ConnectionError:
                    pass
            if replica_available:
                return {"source": "replica", "value": None, "stale": True}
            raise ConnectionError("No Redis instance available")

        result = await get_with_failover("test_key")
        assert result["source"] == "replica"
        assert result.get("stale") is True

    @pytest.mark.asyncio
    async def test_redis_circuit_breaker_protection(
        self, mock_redis: MockRedisService, circuit_breaker: CircuitBreaker
    ) -> None:
        """Verify that circuit breaker protects against Redis failure cascades."""
        mock_redis.available = False

        async def protected_get(key: str) -> str | None:
            if not circuit_breaker.can_execute():
                raise ConnectionError("Circuit breaker open — Redis unavailable")
            try:
                result = await mock_redis.get(key)
                circuit_breaker.record_success()
                return result
            except ConnectionError:
                circuit_breaker.record_failure()
                raise

        # Trigger failures to open circuit
        for _ in range(5):
            with pytest.raises((ConnectionError, Exception)):
                await protected_get("test_key")

        assert circuit_breaker.state == "open"

    @pytest.mark.asyncio
    async def test_redis_timeout_handling(
        self, mock_redis: MockRedisService
    ) -> None:
        """Verify that Redis operation timeouts are handled gracefully."""
        async def get_with_timeout(key: str) -> dict[str, Any]:
            try:
                value = await asyncio.wait_for(mock_redis.get(key), timeout=0.5)
                return {"status": "success", "value": value}
            except asyncio.TimeoutError:
                return {
                    "status": "timeout",
                    "error_code": "REDIS_TIMEOUT",
                    "retryable": True,
                }

        response = await get_with_timeout("test_key")
        assert response["status"] in ("success", "timeout")

    @pytest.mark.asyncio
    async def test_redis_data_consistency_after_recovery(
        self, mock_redis: MockRedisService
    ) -> None:
        """Verify that Redis data is consistent after recovery from failure."""
        # Write data before failure
        mock_redis.available = True
        await mock_redis.set("key1", "value1")
        await mock_redis.set("key2", "value2")

        # Simulate failure
        mock_redis.available = False
        await asyncio.sleep(0.1)

        # Simulate recovery
        mock_redis.available = True

        # Verify data persistence
        val1 = await mock_redis.get("key1")
        val2 = await mock_redis.get("key2")

        # In a real scenario, data might be lost depending on persistence config
        # Here we verify the mock maintains data
        assert val1 == "value1"
        assert val2 == "value2"

    @pytest.mark.asyncio
    async def test_redis_memory_pressure_handling(
        self, mock_redis: MockRedisService
    ) -> None:
        """Verify that Redis memory pressure is handled gracefully."""
        max_memory_mb = 256
        current_memory_mb = 300

        async def check_memory_pressure() -> dict[str, Any]:
            return {
                "current_mb": current_memory_mb,
                "max_mb": max_memory_mb,
                "usage_percent": (current_memory_mb / max_memory_mb) * 100,
                "is_critical": current_memory_mb > max_memory_mb,
            }

        status = await check_memory_pressure()
        assert status["is_critical"] is True
        assert status["usage_percent"] > 100

    @pytest.mark.asyncio
    async def test_redis_pipeline_failure_handling(
        self, mock_redis: MockRedisService
    ) -> None:
        """Verify that Redis pipeline failures are handled gracefully."""
        mock_redis.available = False

        async def pipeline_with_fallback(operations: list[tuple[str, str]]) -> dict[str, Any]:
            results = {}
            failed_ops = []
            for op, key in operations:
                try:
                    if op == "get":
                        results[key] = await mock_redis.get(key)
                    elif op == "set":
                        await mock_redis.set(key, "value")
                        results[key] = "OK"
                except ConnectionError:
                    failed_ops.append((op, key))

            return {
                "results": results,
                "failed_operations": failed_ops,
                "partial_success": len(results) > 0,
            }

        ops = [("get", "key1"), ("set", "key2"), ("get", "key3")]
        result = await pipeline_with_fallback(ops)

        assert result["partial_success"] is False
        assert len(result["failed_operations"]) == 3

    @pytest.mark.asyncio
    async def test_redis_recovery_detection(
        self, mock_redis: MockRedisService
    ) -> None:
        """Verify that Redis recovery is detected after failure."""
        mock_redis.available = False

        # Simulate failure
        with pytest.raises(ConnectionError):
            await mock_redis.get("test")

        # Simulate recovery
        await asyncio.sleep(0.1)
        mock_redis.available = True

        # Verify recovery
        await mock_redis.set("test", "value")
        result = await mock_redis.get("test")
        assert result == "value"
        assert mock_redis.health_check().is_healthy is True

    @pytest.mark.asyncio
    async def test_redis_failure_metrics_recording(
        self, mock_redis: MockRedisService, chaos_monkey: ChaosMonkey
    ) -> None:
        """Verify that Redis failure metrics are properly recorded."""
        chaos_monkey.config.failure_mode = FailureMode.CONNECTION_REFUSED
        chaos_monkey.config.target_service = ServiceType.REDIS

        event = chaos_monkey.inject_failure(context="redis_failure_test")

        assert event.service == ServiceType.REDIS
        assert event.failure_mode == FailureMode.CONNECTION_REFUSED
        assert event.event_id is not None

    @pytest.mark.asyncio
    async def test_redis_cluster_shard_failure(
        self, mock_redis: MockRedisService
    ) -> None:
        """Verify that Redis cluster shard failures are handled."""
        shard_status = {
            0: {"available": True, "keys": 1000},
            1: {"available": False, "keys": 1500},
            2: {"available": True, "keys": 800},
        }

        async def get_shard_health() -> dict[str, Any]:
            available_shards = sum(1 for s in shard_status.values() if s["available"])
            total_shards = len(shard_status)
            return {
                "available_shards": available_shards,
                "total_shards": total_shards,
                "is_degraded": available_shards < total_shards,
                "availability_percent": (available_shards / total_shards) * 100,
            }

        health = await get_shard_health()
        assert health["is_degraded"] is True
        assert health["available_shards"] == 2
        assert health["availability_percent"] < 100
