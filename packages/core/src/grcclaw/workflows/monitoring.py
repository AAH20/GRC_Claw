"""
Workflow monitoring for GRC_Claw.

Provides real-time monitoring, metrics collection, health checks,
alerting, and observability for workflow runs.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional

from .engine import WorkflowEngine
from .schema import StepStatus, WorkflowRun

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class WorkflowMetrics:
    """Aggregated metrics for workflow execution."""

    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    cancelled_runs: int = 0
    timed_out_runs: int = 0
    avg_duration_seconds: float = 0.0
    min_duration_seconds: float = 0.0
    max_duration_seconds: float = 0.0
    total_steps_executed: int = 0
    total_steps_failed: int = 0
    total_steps_retried: int = 0
    runs_per_minute: float = 0.0
    success_rate: float = 0.0
    p50_duration_seconds: float = 0.0
    p95_duration_seconds: float = 0.0
    p99_duration_seconds: float = 0.0
    last_updated: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "failed_runs": self.failed_runs,
            "cancelled_runs": self.cancelled_runs,
            "timed_out_runs": self.timed_out_runs,
            "avg_duration_seconds": self.avg_duration_seconds,
            "min_duration_seconds": self.min_duration_seconds,
            "max_duration_seconds": self.max_duration_seconds,
            "total_steps_executed": self.total_steps_executed,
            "total_steps_failed": self.total_steps_failed,
            "total_steps_retried": self.total_steps_retried,
            "runs_per_minute": self.runs_per_minute,
            "success_rate": self.success_rate,
            "p50_duration_seconds": self.p50_duration_seconds,
            "p95_duration_seconds": self.p95_duration_seconds,
            "p99_duration_seconds": self.p99_duration_seconds,
            "last_updated": self.last_updated,
        }


@dataclass
class AlertRule:
    name: str
    condition: Callable[[WorkflowMetrics], bool]
    severity: str = "warning"
    message: str = ""
    cooldown_seconds: float = 300.0
    _last_triggered: float = 0.0

    def evaluate(self, metrics: WorkflowMetrics) -> bool:
        try:
            return self.condition(metrics)
        except Exception:
            return False

    def should_notify(self) -> bool:
        return (time.monotonic() - self._last_triggered) >= self.cooldown_seconds

    def mark_triggered(self) -> None:
        self._last_triggered = time.monotonic()


@dataclass
class Alert:
    rule_name: str
    severity: str
    message: str
    timestamp: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)


class WorkflowMonitor:
    """Real-time workflow monitoring and observability."""

    def __init__(self, engine: WorkflowEngine):
        self.engine = engine
        self._metrics = WorkflowMetrics()
        self._run_durations: list[float] = []
        self._step_durations: list[float] = []
        self._alert_rules: list[AlertRule] = []
        self._alert_handlers: list[Callable] = []
        self._watch_task: Optional[asyncio.Task] = None
        self._watch_interval: float = 5.0
        self._max_history: int = 10000
        self._alerts: list[Alert] = []
        self._active_runs: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def start(self, interval: float = 5.0) -> None:
        self._watch_interval = interval
        if self._watch_task is None or self._watch_task.done():
            self._watch_task = asyncio.create_task(self._watch_loop())
            logger.info("workflow monitor started (interval=%.1fs)", interval)

    async def stop(self) -> None:
        if self._watch_task and not self._watch_task.done():
            self._watch_task.cancel()
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass
            self._watch_task = None
            logger.info("workflow monitor stopped")

    def add_alert_rule(self, rule: AlertRule) -> None:
        self._alert_rules.append(rule)

    def add_alert_handler(self, handler: Callable) -> None:
        self._alert_handlers.append(handler)

    def get_metrics(self) -> WorkflowMetrics:
        return self._metrics

    def get_health(self) -> HealthStatus:
        if self._metrics.total_runs == 0:
            return HealthStatus.HEALTHY
        failure_rate = self._metrics.failed_runs / self._metrics.total_runs
        if failure_rate > 0.5:
            return HealthStatus.UNHEALTHY
        if failure_rate > 0.2:
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY

    def get_active_runs(self) -> list[str]:
        return list(self._active_runs.keys())

    def get_recent_alerts(self, limit: int = 50) -> list[Alert]:
        return self._alerts[-limit:]

    def get_run_summary(self, run_id: str) -> Optional[dict[str, Any]]:
        run = self.engine._runs.get(run_id)
        if run is None:
            return None
        return {
            "run_id": run.run_id,
            "workflow_name": run.workflow_name,
            "status": run.status.value,
            "progress_pct": run.progress_pct,
            "duration_seconds": run.duration_seconds,
            "step_count": len(run.step_results),
            "completed_steps": sum(
                1 for r in run.step_results.values() if r.is_terminal
            ),
        }

    async def _watch_loop(self) -> None:
        while True:
            try:
                await self._collect_metrics()
                await self._evaluate_alerts()
                await asyncio.sleep(self._watch_interval)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("monitor watch loop error")
                await asyncio.sleep(self._watch_interval)

    async def _collect_metrics(self) -> None:
        async with self._lock:
            runs = list(self.engine._runs.values())
            now = time.monotonic()

            # Update active runs
            for run in runs:
                if not run.is_complete and run.run_id not in self._active_runs:
                    self._active_runs[run.run_id] = now
                elif run.is_complete and run.run_id in self._active_runs:
                    del self._active_runs[run.run_id]

            completed_runs = [r for r in runs if r.is_complete]
            durations = [r.duration_seconds for r in completed_runs if r.duration_seconds > 0]

            self._run_durations.extend(durations)
            if len(self._run_durations) > self._max_history:
                self._run_durations = self._run_durations[-self._max_history:]

            step_durations: list[float] = []
            total_steps = 0
            failed_steps = 0
            retried_steps = 0
            for run in runs:
                for sr in run.step_results.values():
                    total_steps += 1
                    if sr.status == StepStatus.FAILED:
                        failed_steps += 1
                    if sr.attempt > 1:
                        retried_steps += 1
                    if sr.duration_seconds > 0:
                        step_durations.append(sr.duration_seconds)

            self._step_durations.extend(step_durations)
            if len(self._step_durations) > self._max_history:
                self._step_durations = self._step_durations[-self._max_history:]

            m = self._metrics
            m.total_runs = len(runs)
            m.successful_runs = sum(1 for r in runs if r.status == StepStatus.SUCCEEDED)
            m.failed_runs = sum(1 for r in runs if r.status == StepStatus.FAILED)
            m.cancelled_runs = sum(1 for r in runs if r.status == StepStatus.CANCELLED)
            m.timed_out_runs = sum(1 for r in runs if r.status == StepStatus.TIMED_OUT)
            m.total_steps_executed = total_steps
            m.total_steps_failed = failed_steps
            m.total_steps_retried = retried_steps

            if self._run_durations:
                sorted_d = sorted(self._run_durations)
                m.avg_duration_seconds = sum(sorted_d) / len(sorted_d)
                m.min_duration_seconds = sorted_d[0]
                m.max_duration_seconds = sorted_d[-1]
                m.p50_duration_seconds = self._percentile(sorted_d, 50)
                m.p95_duration_seconds = self._percentile(sorted_d, 95)
                m.p99_duration_seconds = self._percentile(sorted_d, 99)

            if m.total_runs > 0:
                m.success_rate = round(m.successful_runs / m.total_runs, 4)

            # Runs per minute (approximate)
            recent = [
                r for r in runs
                if r.started_at and (now - self._parse_ts(r.started_at)) < 60
            ]
            m.runs_per_minute = len(recent)
            m.last_updated = datetime.now(timezone.utc).isoformat()

    def _percentile(self, sorted_data: list[float], pct: float) -> float:
        if not sorted_data:
            return 0.0
        idx = int(len(sorted_data) * pct / 100)
        idx = min(idx, len(sorted_data) - 1)
        return sorted_data[idx]

    def _parse_ts(self, ts: str) -> float:
        try:
            dt = datetime.fromisoformat(ts)
            return dt.timestamp()
        except Exception:
            return 0.0

    async def _evaluate_alerts(self) -> None:
        for rule in self._alert_rules:
            if rule.evaluate(self._metrics) and rule.should_notify():
                rule.mark_triggered()
                alert = Alert(
                    rule_name=rule.name,
                    severity=rule.severity,
                    message=rule.message,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    metrics=self._metrics.to_dict(),
                )
                self._alerts.append(alert)
                for handler in self._alert_handlers:
                    try:
                        await handler(alert)
                    except Exception:
                        logger.exception("alert handler failed")

    def create_default_alert_rules(self) -> None:
        self.add_alert_rule(AlertRule(
            name="high_failure_rate",
            condition=lambda m: m.total_runs >= 5 and m.success_rate < 0.5,
            severity="critical",
            message="Workflow failure rate exceeds 50%",
        ))
        self.add_alert_rule(AlertRule(
            name="elevated_failure_rate",
            condition=lambda m: m.total_runs >= 5 and m.success_rate < 0.8,
            severity="warning",
            message="Workflow success rate below 80%",
        ))
        self.add_alert_rule(AlertRule(
            name="high_retry_rate",
            condition=lambda m: (
                m.total_steps_executed >= 10
                and m.total_steps_retried / m.total_steps_executed > 0.3
            ),
            severity="warning",
            message="Step retry rate exceeds 30%",
        ))
        self.add_alert_rule(AlertRule(
            name="slow_workflows",
            condition=lambda m: m.p95_duration_seconds > 600,
            severity="warning",
            message="P95 workflow duration exceeds 10 minutes",
        ))
