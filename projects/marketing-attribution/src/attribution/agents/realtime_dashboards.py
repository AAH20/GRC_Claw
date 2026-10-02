"""Real-time Dashboards Agent - WebSocket streaming of live marketing metrics."""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

import structlog

from attribution.agents.attribution_engine import CampaignAttribution
from attribution.agents.data_collection import RawDataPoint

logger = structlog.get_logger(__name__)


@dataclass
class DashboardMetrics:
    """Real-time metrics for dashboard display."""

    timestamp: datetime
    total_spend: float
    total_revenue: float
    total_conversions: float
    total_impressions: int
    total_clicks: int
    active_campaigns: int
    roas: float
    cpa: float
    ctr: float
    top_campaigns: list[dict[str, Any]]


@dataclass
class DashboardUpdate:
    """A single dashboard update message."""

    update_type: str
    payload: dict[str, Any]
    timestamp: datetime


class ConnectionManager:
    """Manages WebSocket connections for real-time dashboards."""

    def __init__(self) -> None:
        self.active_connections: list[Any] = []
        self.logger = structlog.get_logger(__name__).bind(component="connection_manager")

    async def connect(self, websocket: Any) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.logger.info("Client connected", total_connections=len(self.active_connections))

    def disconnect(self, websocket: Any) -> None:
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.logger.info("Client disconnected", total_connections=len(self.active_connections))

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a message to all connected clients."""
        disconnected: list[Any] = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

    async def send_personal_message(self, message: dict[str, Any], websocket: Any) -> None:
        """Send a message to a specific client."""
        await websocket.send_json(message)


class RealtimeDashboardsAgent:
    """Agent for real-time dashboard updates and metric streaming."""

    def __init__(self, update_interval_seconds: int = 30) -> None:
        self.update_interval_seconds = update_interval_seconds
        self.connection_manager = ConnectionManager()
        self._running = False
        self._task: asyncio.Task | None = None
        self.logger = structlog.get_logger(__name__).bind(agent="realtime_dashboards")

    def compute_metrics(
        self,
        data_points: list[RawDataPoint],
        attribution_results: list[CampaignAttribution] | None = None,
    ) -> DashboardMetrics:
        """Compute current dashboard metrics from data points."""
        total_spend = sum(dp.spend for dp in data_points)
        total_revenue = sum(dp.revenue for dp in data_points)
        total_conversions = sum(dp.conversions for dp in data_points)
        total_impressions = sum(dp.impressions for dp in data_points)
        total_clicks = sum(dp.clicks for dp in data_points)
        active_campaigns = len({dp.campaign_id for dp in data_points})
        roas = total_revenue / total_spend if total_spend > 0 else 0.0
        cpa = total_spend / total_conversions if total_conversions > 0 else 0.0
        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0.0
        top_campaigns: list[dict[str, Any]] = []
        if attribution_results:
            sorted_campaigns = sorted(
                attribution_results, key=lambda x: x.attributed_revenue, reverse=True
            )[:5]
            top_campaigns = [
                {
                    "campaign_id": c.campaign_id,
                    "campaign_name": c.campaign_name,
                    "source": c.source,
                    "attributed_revenue": round(c.attributed_revenue, 2),
                    "roas": round(c.roas, 2),
                }
                for c in sorted_campaigns
            ]
        return DashboardMetrics(
            timestamp=datetime.utcnow(),
            total_spend=round(total_spend, 2),
            total_revenue=round(total_revenue, 2),
            total_conversions=round(total_conversions, 2),
            total_impressions=total_impressions,
            total_clicks=total_clicks,
            active_campaigns=active_campaigns,
            roas=round(roas, 2),
            cpa=round(cpa, 2),
            ctr=round(ctr, 2),
            top_campaigns=top_campaigns,
        )

    def create_update(
        self,
        update_type: str,
        data_points: list[RawDataPoint],
        attribution_results: list[CampaignAttribution] | None = None,
    ) -> DashboardUpdate:
        """Create a dashboard update message."""
        metrics = self.compute_metrics(data_points, attribution_results)
        return DashboardUpdate(
            update_type=update_type, payload=asdict(metrics), timestamp=datetime.utcnow()
        )

    async def start_streaming(
        self,
        data_source: Any,
        attribution_results: list[CampaignAttribution] | None = None,
    ) -> None:
        """Start streaming dashboard updates."""
        self._running = True
        self.logger.info(
            "Starting dashboard streaming",
            interval_seconds=self.update_interval_seconds,
        )
        while self._running:
            try:
                data_points = data_source() if callable(data_source) else data_source
                update = self.create_update("metrics", data_points, attribution_results)
                await self.connection_manager.broadcast(
                    {
                        "type": update.update_type,
                        "payload": update.payload,
                        "timestamp": update.timestamp.isoformat(),
                    }
                )
                await asyncio.sleep(self.update_interval_seconds)
            except asyncio.CancelledError:
                self.logger.info("Dashboard streaming cancelled")
                break
            except Exception as exc:
                self.logger.error("Streaming error", error=str(exc))
                await asyncio.sleep(5)

    def stop_streaming(self) -> None:
        """Stop streaming dashboard updates."""
        self._running = False
        if self._task:
            self._task.cancel()
        self.logger.info("Dashboard streaming stopped")

    async def handle_websocket(self, websocket: Any, data_source: Any) -> None:
        """Handle a WebSocket connection for real-time updates."""
        await self.connection_manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    if message.get("action") == "get_metrics":
                        data_points = data_source() if callable(data_source) else data_source
                        update = self.create_update("metrics", data_points)
                        await self.connection_manager.send_personal_message(
                            {
                                "type": update.update_type,
                                "payload": update.payload,
                                "timestamp": update.timestamp.isoformat(),
                            },
                            websocket,
                        )
                except json.JSONDecodeError:
                    await self.connection_manager.send_personal_message(
                        {"error": "Invalid JSON"}, websocket
                    )
        except Exception:
            pass
        finally:
            self.connection_manager.disconnect(websocket)
