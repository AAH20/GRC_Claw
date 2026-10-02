"""Real-time Dashboards Agent - WebSocket streaming for live metrics."""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class MetricType(StrEnum):
    """Types of real-time metrics."""

    REVENUE = "revenue"
    CONVERSIONS = "conversions"
    ACTIVE_USERS = "active_users"
    CAMPAIGN_PERFORMANCE = "campaign_performance"
    CHANNEL_PERFORMANCE = "channel_performance"
    FUNNEL = "funnel"


@dataclass
class MetricValue:
    """A single metric value."""

    metric_type: MetricType
    name: str
    value: float
    timestamp: datetime
    labels: dict[str, str] = field(default_factory=dict)


@dataclass
class DashboardSnapshot:
    """A snapshot of all dashboard metrics."""

    timestamp: datetime
    metrics: list[MetricValue]
    metadata: dict[str, Any] = field(default_factory=dict)


class ConnectionManager:
    """Manages WebSocket connections for real-time dashboards."""

    def __init__(self) -> None:
        self._connections: set[Any] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: Any) -> None:
        """Accept a new WebSocket connection."""
        async with self._lock:
            self._connections.add(websocket)
        logger.info("websocket_connected", total_connections=len(self._connections))

    async def disconnect(self, websocket: Any) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            self._connections.discard(websocket)
        logger.info("websocket_disconnected", total_connections=len(self._connections))

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a message to all connected clients."""
        disconnected: set[Any] = set()
        for ws in self._connections:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.add(ws)

        if disconnected:
            async with self._lock:
                self._connections -= disconnected

    @property
    def connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self._connections)


class RealtimeDashboardsAgent:
    """Agent for streaming real-time dashboard metrics."""

    def __init__(
        self,
        refresh_interval_seconds: float = 5.0,
        buffer_size: int = 1000,
    ) -> None:
        self.refresh_interval = refresh_interval_seconds
        self.buffer_size = buffer_size
        self.connection_manager = ConnectionManager()
        self.logger = logger.bind(agent="realtime_dashboards")
        self._metrics_buffer: list[MetricValue] = []
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the real-time metrics streaming loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._streaming_loop())
        self.logger.info("realtime_dashboards_started")

    async def stop(self) -> None:
        """Stop the real-time metrics streaming loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
        self.logger.info("realtime_dashboards_stopped")

    async def _streaming_loop(self) -> None:
        """Main streaming loop that broadcasts metrics periodically."""
        while self._running:
            try:
                snapshot = await self._collect_metrics()
                await self.connection_manager.broadcast(
                    {
                        "type": "metrics_update",
                        "data": {
                            "timestamp": snapshot.timestamp.isoformat(),
                            "metrics": [
                                {
                                    "type": m.metric_type.value,
                                    "name": m.name,
                                    "value": m.value,
                                    "labels": m.labels,
                                }
                                for m in snapshot.metrics
                            ],
                        },
                    }
                )
            except Exception as exc:
                self.logger.error("streaming_error", error=str(exc))

            await asyncio.sleep(self.refresh_interval)

    async def _collect_metrics(self) -> DashboardSnapshot:
        """Collect current metrics from all sources."""
        now = datetime.utcnow()
        metrics: list[MetricValue] = []

        # In production, these would query actual data sources
        # For now, generate placeholder metrics
        metrics.extend(
            [
                MetricValue(
                    metric_type=MetricType.REVENUE,
                    name="total_revenue_today",
                    value=0.0,  # Would be calculated from actual data
                    timestamp=now,
                ),
                MetricValue(
                    metric_type=MetricType.CONVERSIONS,
                    name="total_conversions_today",
                    value=0.0,
                    timestamp=now,
                ),
                MetricValue(
                    metric_type=MetricType.ACTIVE_USERS,
                    name="active_users_now",
                    value=0.0,
                    timestamp=now,
                ),
            ]
        )

        # Add to buffer
        self._metrics_buffer.extend(metrics)
        if len(self._metrics_buffer) > self.buffer_size:
            self._metrics_buffer = self._metrics_buffer[-self.buffer_size :]

        return DashboardSnapshot(
            timestamp=now,
            metrics=metrics,
            metadata={
                "buffer_size": len(self._metrics_buffer),
                "connections": self.connection_manager.connection_count,
            },
        )

    def get_current_snapshot(self) -> DashboardSnapshot:
        """Get the most recent metrics snapshot."""
        return DashboardSnapshot(
            timestamp=datetime.utcnow(),
            metrics=self._metrics_buffer[-10:] if self._metrics_buffer else [],
            metadata={
                "buffer_size": len(self._metrics_buffer),
                "connections": self.connection_manager.connection_count,
            },
        )

    def get_historical_metrics(
        self,
        metric_type: MetricType | None = None,
        limit: int = 100,
    ) -> list[MetricValue]:
        """Get historical metrics from the buffer."""
        metrics = self._metrics_buffer
        if metric_type:
            metrics = [m for m in metrics if m.metric_type == metric_type]
        return metrics[-limit:]

    async def handle_websocket(self, websocket: Any) -> None:
        """Handle a WebSocket connection lifecycle."""
        await self.connection_manager.connect(websocket)
        try:
            # Send initial snapshot
            snapshot = self.get_current_snapshot()
            await websocket.send_json(
                {
                    "type": "initial_snapshot",
                    "data": {
                        "timestamp": snapshot.timestamp.isoformat(),
                        "metrics": [
                            {
                                "type": m.metric_type.value,
                                "name": m.name,
                                "value": m.value,
                                "labels": m.labels,
                            }
                            for m in snapshot.metrics
                        ],
                    },
                }
            )

            # Keep connection alive and handle incoming messages
            while True:
                try:
                    data = await websocket.receive_json()
                    await self._handle_client_message(websocket, data)
                except Exception:
                    break
        finally:
            await self.connection_manager.disconnect(websocket)

    async def _handle_client_message(self, websocket: Any, data: dict[str, Any]) -> None:
        """Handle a message from a WebSocket client."""
        msg_type = data.get("type", "")

        if msg_type == "subscribe":
            metric_types = data.get("metric_types", [])
            self.logger.info("client_subscribed", metric_types=metric_types)
            await websocket.send_json(
                {"type": "subscribed", "metric_types": metric_types}
            )
        elif msg_type == "ping":
            await websocket.send_json({"type": "pong"})
        elif msg_type == "get_snapshot":
            snapshot = self.get_current_snapshot()
            await websocket.send_json(
                {
                    "type": "snapshot",
                    "data": {
                        "timestamp": snapshot.timestamp.isoformat(),
                        "metrics": [
                            {
                                "type": m.metric_type.value,
                                "name": m.name,
                                "value": m.value,
                                "labels": m.labels,
                            }
                            for m in snapshot.metrics
                        ],
                    },
                }
            )
