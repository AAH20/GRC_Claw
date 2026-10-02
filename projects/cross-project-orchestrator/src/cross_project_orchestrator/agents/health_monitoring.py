"""Health Monitoring Agent — tracks project health metrics, uptime, and SLA compliance."""

from __future__ import annotations

import asyncio
import contextlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class HealthStatus(StrEnum):
    """Health status of a project."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthThresholds:
    """Thresholds for determining health status."""

    cpu_percent: float = 80.0
    memory_percent: float = 85.0
    error_rate: float = 0.05
    latency_p99_ms: float = 1000.0


@dataclass
class HealthSnapshot:
    """A point-in-time health snapshot for a project."""

    project_id: str
    status: HealthStatus
    cpu_percent: float
    memory_percent: float
    error_rate: float
    latency_p99_ms: float
    uptime_seconds: float
    last_check: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SLAReport:
    """SLA compliance report for a project."""

    project_id: str
    target_uptime_percent: float
    actual_uptime_percent: float
    compliant: bool
    period_start: datetime
    period_end: datetime
    violations: list[dict[str, Any]] = field(default_factory=list)


class HealthMonitoringAgent:
    """Tracks project health metrics, uptime, and SLA compliance.

    Periodically checks project health endpoints and maintains
    a rolling window of health snapshots for trend analysis.
    """

    def __init__(
        self,
        check_interval: int = 60,
        thresholds: HealthThresholds | None = None,
        retention_days: int = 30,
    ) -> None:
        """Initialize the Health Monitoring Agent.

        Args:
            check_interval: Seconds between health checks.
            thresholds: Health status thresholds.
            retention_days: Number of days to retain health history.
        """
        self._check_interval = check_interval
        self._thresholds = thresholds or HealthThresholds()
        self._retention_days = retention_days
        self._snapshots: dict[str, list[HealthSnapshot]] = {}
        self._start_times: dict[str, float] = {}
        self._running = False
        self._monitor_task: asyncio.Task[None] | None = None

    @property
    def is_running(self) -> bool:
        """Check if the background monitoring loop is active."""
        return self._running

    async def start(self) -> None:
        """Start the background health monitoring loop."""
        if self._running:
            logger.warning("HealthMonitoringAgent already running")
            return
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("HealthMonitoringAgent started", interval=self._check_interval)

    async def stop(self) -> None:
        """Stop the background health monitoring loop."""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._monitor_task
        logger.info("HealthMonitoringAgent stopped")

    async def _monitor_loop(self) -> None:
        """Background loop that periodically checks project health."""
        while self._running:
            try:
                await self.check_all()
            except Exception as exc:
                logger.error("Health check cycle failed", error=str(exc))
            await asyncio.sleep(self._check_interval)

    async def check_all(self) -> list[HealthSnapshot]:
        """Check health for all registered projects.

        Returns:
            List of health snapshots from this check cycle.
        """
        snapshots: list[HealthSnapshot] = []
        for project_id in list(self._start_times.keys()):
            snapshot = await self.check_project(project_id)
            if snapshot:
                snapshots.append(snapshot)
        return snapshots

    async def check_project(self, project_id: str) -> HealthSnapshot | None:
        """Check the health of a single project.

        Args:
            project_id: The project to check.

        Returns:
            Health snapshot or None if project is not registered.
        """
        if project_id not in self._start_times:
            return None

        try:
            # In production, this would make actual HTTP calls to project health endpoints
            metrics = await self._fetch_metrics(project_id)
            status = self._evaluate_status(metrics)
            uptime = time.monotonic() - self._start_times[project_id]

            snapshot = HealthSnapshot(
                project_id=project_id,
                status=status,
                cpu_percent=metrics.get("cpu_percent", 0.0),
                memory_percent=metrics.get("memory_percent", 0.0),
                error_rate=metrics.get("error_rate", 0.0),
                latency_p99_ms=metrics.get("latency_p99_ms", 0.0),
                uptime_seconds=uptime,
            )

            self._record_snapshot(snapshot)
            return snapshot
        except Exception as exc:
            logger.error("Health check failed", project_id=project_id, error=str(exc))
            return HealthSnapshot(
                project_id=project_id,
                status=HealthStatus.UNHEALTHY,
                cpu_percent=0.0,
                memory_percent=0.0,
                error_rate=1.0,
                latency_p99_ms=0.0,
                uptime_seconds=0.0,
                metadata={"error": str(exc)},
            )

    async def _fetch_metrics(self, project_id: str) -> dict[str, float]:
        """Fetch metrics from a project's metrics endpoint.

        In production, this would query Prometheus or the project's
        /metrics endpoint. Returns simulated data for now.

        Args:
            project_id: The project to fetch metrics for.

        Returns:
            Dictionary of metric values.
        """
        # Placeholder: would integrate with Prometheus or project endpoints
        return {
            "cpu_percent": 45.0,
            "memory_percent": 60.0,
            "error_rate": 0.01,
            "latency_p99_ms": 250.0,
        }

    def _evaluate_status(self, metrics: dict[str, float]) -> HealthStatus:
        """Evaluate health status from metrics.

        Args:
            metrics: Dictionary of metric values.

        Returns:
            Computed health status.
        """
        if (
            metrics.get("cpu_percent", 0) > self._thresholds.cpu_percent
            or metrics.get("memory_percent", 0) > self._thresholds.memory_percent
            or metrics.get("error_rate", 0) > self._thresholds.error_rate
        ):
            return HealthStatus.UNHEALTHY
        if (
            metrics.get("cpu_percent", 0) > self._thresholds.cpu_percent * 0.8
            or metrics.get("memory_percent", 0) > self._thresholds.memory_percent * 0.8
            or metrics.get("error_rate", 0) > self._thresholds.error_rate * 0.5
        ):
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY

    def _record_snapshot(self, snapshot: HealthSnapshot) -> None:
        """Record a health snapshot, maintaining the retention window.

        Args:
            snapshot: The snapshot to record.
        """
        if snapshot.project_id not in self._snapshots:
            self._snapshots[snapshot.project_id] = []
        self._snapshots[snapshot.project_id].append(snapshot)
        self._prune_old_snapshots(snapshot.project_id)

    def _prune_old_snapshots(self, project_id: str) -> None:
        """Remove snapshots older than the retention period.

        Args:
            project_id: The project whose snapshots to prune.
        """
        cutoff = datetime.utcnow() - timedelta(days=self._retention_days)
        self._snapshots[project_id] = [
            s for s in self._snapshots[project_id] if s.last_check > cutoff
        ]

    def register_project(self, project_id: str) -> None:
        """Register a project for health monitoring.

        Args:
            project_id: The project to register.
        """
        if project_id not in self._start_times:
            self._start_times[project_id] = time.monotonic()
            logger.info("Project registered for health monitoring", project_id=project_id)

    def unregister_project(self, project_id: str) -> bool:
        """Unregister a project from health monitoring.

        Args:
            project_id: The project to unregister.

        Returns:
            True if the project was registered and is now removed.
        """
        removed = self._start_times.pop(project_id, None) is not None
        if removed:
            self._snapshots.pop(project_id, None)
            logger.info("Project unregistered from health monitoring", project_id=project_id)
        return removed

    def get_latest_snapshot(self, project_id: str) -> HealthSnapshot | None:
        """Get the most recent health snapshot for a project.

        Args:
            project_id: The project to look up.

        Returns:
            The latest snapshot or None.
        """
        snapshots = self._snapshots.get(project_id, [])
        return snapshots[-1] if snapshots else None

    def get_sla_report(
        self, project_id: str, target_uptime: float = 99.9
    ) -> SLAReport | None:
        """Generate an SLA compliance report for a project.

        Args:
            project_id: The project to generate the report for.
            target_uptime: Target uptime percentage.

        Returns:
            SLA report or None if no data is available.
        """
        snapshots = self._snapshots.get(project_id, [])
        if not snapshots:
            return None

        total = len(snapshots)
        healthy = sum(1 for s in snapshots if s.status == HealthStatus.HEALTHY)
        uptime_pct = (healthy / total) * 100 if total > 0 else 0.0

        violations = [
            {"timestamp": s.last_check.isoformat(), "status": s.status.value}
            for s in snapshots
            if s.status != HealthStatus.HEALTHY
        ]

        return SLAReport(
            project_id=project_id,
            target_uptime_percent=target_uptime,
            actual_uptime_percent=uptime_pct,
            compliant=uptime_pct >= target_uptime,
            period_start=snapshots[0].last_check,
            period_end=snapshots[-1].last_check,
            violations=violations,
        )
