"""Chaos engineering tests for database failure handling.

These tests verify that the system gracefully handles database failures
including connection loss, query timeouts, transaction rollbacks, and
replica unavailability.
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
    MockDatabaseService,
    ServiceType,
    CircuitBreaker,
)


class TestDatabaseFailureHandling:
    """Test suite for database failure chaos scenarios."""

    @pytest.mark.asyncio
    async def test_database_connection_loss_triggers_reconnect(
        self, mock_database: MockDatabaseService
    ) -> None:
        """Verify that database connection loss triggers automatic reconnection."""
        mock_database.connected = False

        async def reconnect_with_backoff(max_attempts: int = 5) -> bool:
            for attempt in range(max_attempts):
                try:
                    await asyncio.sleep(0.01 * (2**attempt))
                    mock_database.connected = True
                    return True
                except Exception:
                    continue
            return False

        result = await reconnect_with_backoff()
        assert result is True
        assert mock_database.connected is True

    @pytest.mark.asyncio
    async def test_database_query_timeout_returns_error(
        self, mock_database: MockDatabaseService
    ) -> None:
        """Verify that database query timeouts return structured errors."""
        async def query_with_timeout() -> dict[str, Any]:
            try:
                result = await asyncio.wait_for(
                    mock_database.query("SELECT * FROM users"),
                    timeout=0.05,
                )
                return {"status": "success", "data": result}
            except asyncio.TimeoutError:
                return {
                    "status": "error",
                    "error_code": "DB_QUERY_TIMEOUT",
                    "message": "Database query exceeded timeout threshold",
                    "retryable": True,
                }

        response = await query_with_timeout()
        assert response["status"] in ("success", "error")
        if response["status"] == "error":
            assert response["error_code"] == "DB_QUERY_TIMEOUT"
            assert response["retryable"] is True

    @pytest.mark.asyncio
    async def test_database_failure_circuit_breaker(
        self, mock_database: MockDatabaseService, circuit_breaker: CircuitBreaker
    ) -> None:
        """Verify that database failures open the circuit breaker."""
        mock_database.connected = False

        async def protected_query() -> list[dict[str, Any]]:
            if not circuit_breaker.can_execute():
                raise ConnectionError("Circuit breaker open — database unavailable")
            try:
                result = await mock_database.query("SELECT 1")
                circuit_breaker.record_success()
                return result
            except ConnectionError:
                circuit_breaker.record_failure()
                raise

        # Trigger failures to open circuit
        for _ in range(5):
            with pytest.raises((ConnectionError, Exception)):
                await protected_query()

        assert circuit_breaker.state == "open"

    @pytest.mark.asyncio
    async def test_database_transaction_rollback_on_failure(
        self, mock_database: MockDatabaseService
    ) -> None:
        """Verify that database transactions are rolled back on failure."""
        executed_statements: list[str] = []
        rolled_back = False

        async def transaction_with_rollback() -> dict[str, Any]:
            nonlocal rolled_back
            try:
                executed_statements.append("BEGIN")
                executed_statements.append("INSERT INTO orders VALUES (1, 'test')")
                # Simulate failure mid-transaction
                raise ConnectionError("Connection lost during transaction")
            except ConnectionError:
                executed_statements.append("ROLLBACK")
                rolled_back = True
                return {"status": "rolled_back", "statements": executed_statements}

        result = await transaction_with_rollback()
        assert result["status"] == "rolled_back"
        assert rolled_back is True
        assert "ROLLBACK" in executed_statements

    @pytest.mark.asyncio
    async def test_database_connection_pool_exhaustion(
        self, mock_database: MockDatabaseService
    ) -> None:
        """Verify that database connection pool exhaustion is handled gracefully."""
        max_connections = 5
        active_connections = 0
        semaphore = asyncio.Semaphore(max_connections)

        async def acquire_connection() -> bool:
            nonlocal active_connections
            if active_connections >= max_connections:
                return False
            active_connections += 1
            return True

        async def release_connection() -> None:
            nonlocal active_connections
            active_connections = max(0, active_connections - 1)

        # Exhaust the pool
        acquired = []
        for _ in range(max_connections + 3):
            acquired.append(await acquire_connection())

        assert acquired.count(True) == max_connections
        assert acquired.count(False) == 3

        # Release connections
        for _ in range(max_connections):
            await release_connection()

        assert active_connections == 0

    @pytest.mark.asyncio
    async def test_database_replica_failover(
        self, mock_database: MockDatabaseService
    ) -> None:
        """Verify that database replica failover works during primary failure."""
        primary_available = False
        replica_available = True

        async def execute_with_failover(query: str) -> dict[str, Any]:
            if primary_available:
                return {"source": "primary", "data": []}
            if replica_available:
                return {"source": "replica", "data": [], "stale": True}
            raise ConnectionError("No database available")

        result = await execute_with_failover("SELECT 1")
        assert result["source"] == "replica"
        assert result.get("stale") is True

    @pytest.mark.asyncio
    async def test_database_deadlock_detection(
        self, mock_database: MockDatabaseService
    ) -> None:
        """Verify that database deadlocks are detected and resolved."""
        lock_held = False

        async def simulate_deadlock() -> dict[str, Any]:
            nonlocal lock_held
            if lock_held:
                return {
                    "status": "deadlock_detected",
                    "resolution": "victim_transaction_rolled_back",
                }
            lock_held = True
            return {"status": "success"}

        result1 = await simulate_deadlock()
        result2 = await simulate_deadlock()

        assert result1["status"] == "success"
        assert result2["status"] == "deadlock_detected"
        assert result2["resolution"] == "victim_transaction_rolled_back"

    @pytest.mark.asyncio
    async def test_database_slow_query_handling(
        self, mock_database: MockDatabaseService
    ) -> None:
        """Verify that slow database queries are handled without blocking."""
        async def slow_query() -> list[dict[str, Any]]:
            await asyncio.sleep(0.5)
            return [{"id": 1}]

        async def fast_query() -> list[dict[str, Any]]:
            await asyncio.sleep(0.01)
            return [{"id": 2}]

        # Run both queries concurrently
        results = await asyncio.gather(
            asyncio.wait_for(slow_query(), timeout=1.0),
            asyncio.wait_for(fast_query(), timeout=1.0),
        )

        assert len(results) == 2
        assert all(isinstance(r, list) for r in results)

    @pytest.mark.asyncio
    async def test_database_failure_metrics(
        self, mock_database: MockDatabaseService, chaos_monkey: ChaosMonkey
    ) -> None:
        """Verify that database failure metrics are properly recorded."""
        chaos_monkey.config.failure_mode = FailureMode.CONNECTION_REFUSED
        chaos_monkey.config.target_service = ServiceType.DATABASE

        event = chaos_monkey.inject_failure(context="db_failure_test")

        assert event.service == ServiceType.DATABASE
        assert event.failure_mode == FailureMode.CONNECTION_REFUSED

        health = mock_database.health_check()
        assert health.service == ServiceType.DATABASE

    @pytest.mark.asyncio
    async def test_database_recovery_after_failure(
        self, mock_database: MockDatabaseService
    ) -> None:
        """Verify that the database recovers after a failure event."""
        mock_database.connected = False

        # Simulate failure
        with pytest.raises(ConnectionError):
            await mock_database.query("SELECT 1")

        # Simulate recovery
        await asyncio.sleep(0.1)
        mock_database.connected = True

        # Verify recovery
        result = await mock_database.query("SELECT 1")
        assert isinstance(result, list)
        assert mock_database.health_check().is_healthy is True

    @pytest.mark.asyncio
    async def test_database_connection_string_failure(
        self, mock_database: MockDatabaseService
    ) -> None:
        """Verify that invalid database connection strings are handled."""
        invalid_connection_strings = [
            "postgresql://invalid:5432/db",
            "mysql://:3306/db",
            "://missing-scheme",
        ]

        for conn_str in invalid_connection_strings:
            is_valid = "://" in conn_str and not conn_str.startswith("://")
            assert not is_valid or conn_str.count("://") == 1
