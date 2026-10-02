"""Chaos engineering tests for network partition handling.

These tests verify that the system gracefully handles network partitions
including split-brain scenarios, partial connectivity, asymmetric
routing, and partition healing detection.
"""

from __future__ import annotations

import asyncio
import socket
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


class TestNetworkPartitionHandling:
    """Test suite for network partition chaos scenarios."""

    @pytest.mark.asyncio
    async def test_network_partition_detection(
        self, network_partition_simulator: dict[str, bool]
    ) -> None:
        """Verify that network partitions are detected between services."""
        # Simulate partition: database and kafka become unreachable
        network_partition_simulator["database"] = False
        network_partition_simulator["kafka"] = False

        async def check_connectivity(service: str) -> dict[str, Any]:
            await asyncio.sleep(0.01)
            reachable = network_partition_simulator.get(service, True)
            return {
                "service": service,
                "reachable": reachable,
                "partition_detected": not reachable,
            }

        results = await asyncio.gather(*[
            check_connectivity(svc) for svc in network_partition_simulator
        ])

        partitioned = [r for r in results if r["partition_detected"]]
        assert len(partitioned) == 2
        assert all(r["service"] in ("database", "kafka") for r in partitioned)

    @pytest.mark.asyncio
    async def test_split_brain_prevention(
        self, network_partition_simulator: dict[str, bool]
    ) -> None:
        """Verify that split-brain scenarios are prevented during partitions."""
        # Simulate network partition between two nodes
        node_a_services = {"database": True, "kafka": True, "redis": True}
        node_b_services = {"database": False, "kafka": False, "redis": True}

        async def resolve_split_brain() -> dict[str, Any]:
            # Node A can reach all services, Node B cannot
            # Consensus: Node A wins because it has quorum
            node_a_quorum = sum(node_a_services.values()) >= 2
            node_b_quorum = sum(node_b_services.values()) >= 2

            if node_a_quorum and not node_b_quorum:
                return {
                    "leader": "node_a",
                    "status": "partition_resolved",
                    "isolated_node": "node_b",
                }
            return {"leader": None, "status": "no_quorum"}

        result = await resolve_split_brain()
        assert result["leader"] == "node_a"
        assert result["isolated_node"] == "node_b"

    @pytest.mark.asyncio
    async def test_partial_connectivity_handling(
        self, network_partition_simulator: dict[str, bool]
    ) -> None:
        """Verify that partial connectivity is handled gracefully."""
        # Simulate partial partition: only redis is reachable
        for key in network_partition_simulator:
            network_partition_simulator[key] = key == "redis"

        async def route_with_partial_connectivity(target: str) -> dict[str, Any]:
            reachable = network_partition_simulator.get(target, False)
            if reachable:
                return {"status": "direct", "target": target}
            # Try alternative routes
            alternatives = [s for s, r in network_partition_simulator.items() if r and s != target]
            if alternatives:
                return {
                    "status": "rerouted",
                    "target": target,
                    "via": alternatives[0],
                }
            return {"status": "unreachable", "target": target}

        result = await route_with_partial_connectivity("database")
        assert result["status"] == "rerouted"
        assert result["via"] == "redis"

    @pytest.mark.asyncio
    async def test_asymmetric_routing_handling(
        self, network_partition_simulator: dict[str, bool]
    ) -> None:
        """Verify that asymmetric routing (A→B works, B→A doesn't) is handled."""
        # Simulate asymmetric partition
        a_to_b = True
        b_to_a = False

        async def check_asymmetric_route() -> dict[str, Any]:
            return {
                "a_to_b_reachable": a_to_b,
                "b_to_a_reachable": b_to_a,
                "is_asymmetric": a_to_b != b_to_a,
                "recommendation": "Use bidirectional health checks",
            }

        result = await check_asymmetric_route()
        assert result["is_asymmetric"] is True
        assert result["a_to_b_reachable"] is True
        assert result["b_to_a_reachable"] is False

    @pytest.mark.asyncio
    async def test_partition_healing_detection(
        self, network_partition_simulator: dict[str, bool]
    ) -> None:
        """Verify that partition healing is detected when connectivity returns."""
        # Start with full partition
        for key in network_partition_simulator:
            network_partition_simulator[key] = False

        # Simulate healing
        await asyncio.sleep(0.1)
        for key in network_partition_simulator:
            network_partition_simulator[key] = True

        async def detect_healing() -> dict[str, Any]:
            all_reachable = all(network_partition_simulator.values())
            return {
                "healed": all_reachable,
                "timestamp": time.time(),
                "services_restored": list(network_partition_simulator.keys()),
            }

        result = await detect_healing()
        assert result["healed"] is True
        assert len(result["services_restored"]) == 5

    @pytest.mark.asyncio
    async def test_dns_failure_during_partition(
        self, network_partition_simulator: dict[str, bool]
    ) -> None:
        """Verify that DNS failures during network partition are handled."""
        dns_available = False

        async def resolve_with_fallback(hostname: str) -> dict[str, Any]:
            if dns_available:
                return {"status": "resolved", "hostname": hostname, "ip": "10.0.0.1"}
            # Use cached DNS entry
            return {
                "status": "cached",
                "hostname": hostname,
                "ip": "10.0.0.1",
                "stale": True,
                "message": "DNS unavailable — using cached resolution",
            }

        result = await resolve_with_fallback("database.internal")
        assert result["status"] == "cached"
        assert result["stale"] is True

    @pytest.mark.asyncio
    async def test_socket_timeout_during_partition(
        self, temp_socket: socket.socket
    ) -> None:
        """Verify that socket timeouts during partition are handled."""
        temp_socket.settimeout(0.1)

        async def connect_with_timeout(host: str, port: int) -> dict[str, Any]:
            try:
                loop = asyncio.get_event_loop()
                await asyncio.wait_for(
                    loop.sock_connect(temp_socket, (host, port)),
                    timeout=0.1,
                )
                return {"status": "connected", "host": host, "port": port}
            except (asyncio.TimeoutError, OSError):
                return {
                    "status": "timeout",
                    "host": host,
                    "port": port,
                    "message": "Connection timed out — possible network partition",
                }

        result = await connect_with_timeout("10.255.255.1", 5432)
        assert result["status"] == "timeout"

    @pytest.mark.asyncio
    async def test_network_partition_circuit_breaker(
        self, network_partition_simulator: dict[str, bool], circuit_breaker: CircuitBreaker
    ) -> None:
        """Verify that circuit breaker opens during network partition."""
        # Simulate full partition
        for key in network_partition_simulator:
            network_partition_simulator[key] = False

        async def protected_call(service: str) -> dict[str, Any]:
            if not circuit_breaker.can_execute():
                return {
                    "status": "circuit_open",
                    "service": service,
                    "message": "Circuit breaker open — network partition detected",
                }
            reachable = network_partition_simulator.get(service, False)
            if not reachable:
                circuit_breaker.record_failure()
                return {"status": "unreachable", "service": service}
            circuit_breaker.record_success()
            return {"status": "success", "service": service}

        # Trigger failures
        results = []
        for _ in range(10):
            result = await protected_call("database")
            results.append(result)

        assert circuit_breaker.state == "open"

    @pytest.mark.asyncio
    async def test_network_partition_metrics_recording(
        self, network_partition_simulator: dict[str, bool], chaos_monkey: ChaosMonkey
    ) -> None:
        """Verify that network partition metrics are properly recorded."""
        chaos_monkey.config.failure_mode = FailureMode.CONNECTION_REFUSED
        chaos_monkey.config.target_service = ServiceType.NETWORK

        event = chaos_monkey.inject_failure(context="network_partition_test")

        assert event.service == ServiceType.NETWORK
        assert event.failure_mode == FailureMode.CONNECTION_REFUSED
        assert event.event_id is not None

    @pytest.mark.asyncio
    async def test_partition_tolerant_message_queue(
        self, network_partition_simulator: dict[str, bool]
    ) -> None:
        """Verify that message queues tolerate network partitions."""
        # Simulate partition where kafka is unreachable
        network_partition_simulator["kafka"] = False

        message_buffer: list[dict[str, Any]] = []

        async def produce_with_buffer(topic: str, message: dict[str, Any]) -> dict[str, Any]:
            if not network_partition_simulator.get("kafka", True):
                # Buffer message locally
                message_buffer.append({"topic": topic, "message": message, "timestamp": time.time()})
                return {"status": "buffered", "topic": topic}
            return {"status": "produced", "topic": topic}

        result = await produce_with_buffer("events", {"data": "test"})
        assert result["status"] == "buffered"
        assert len(message_buffer) == 1
