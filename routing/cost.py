"""Cost monitoring and tracking system.

Provides real-time cost tracking, reporting, and alerting for
AI model usage across multiple dimensions.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class CostAlertLevel(Enum):
    """Cost alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class CostEntry:
    """Single cost record.

    Attributes:
        timestamp: Unix timestamp of the cost event.
        model: Model that incurred the cost.
        tokens_input: Number of input tokens.
        tokens_output: Number of output tokens.
        cost_usd: Total cost in USD.
        project_id: Optional project identifier.
        metadata: Additional metadata.
    """

    timestamp: float
    model: str
    tokens_input: int
    tokens_output: int
    cost_usd: float
    project_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        """Get total tokens (input + output).

        Returns:
            Sum of input and output tokens.
        """
        return self.tokens_input + self.tokens_output


@dataclass
class CostAlert:
    """Cost alert configuration.

    Attributes:
        name: Alert name.
        threshold_usd: Cost threshold in USD.
        level: Alert severity level.
        callback: Optional callback function.
        window_seconds: Time window for the alert (0 = cumulative).
    """

    name: str
    threshold_usd: float
    level: CostAlertLevel = CostAlertLevel.WARNING
    callback: Optional[Callable[[CostAlert, float], None]] = None
    window_seconds: float = 0.0


@dataclass
class CostSummary:
    """Summary of costs over a period.

    Attributes:
        total_cost_usd: Total cost in USD.
        total_tokens: Total tokens consumed.
        total_requests: Total number of requests.
        avg_cost_per_request: Average cost per request.
        cost_by_model: Cost breakdown by model.
        cost_by_project: Cost breakdown by project.
        period_start: Start of the summary period.
        period_end: End of the summary period.
    """

    total_cost_usd: float
    total_tokens: int
    total_requests: int
    avg_cost_per_request: float
    cost_by_model: Dict[str, float]
    cost_by_project: Dict[str, float]
    period_start: float
    period_end: float


class CostMonitor:
    """Real-time cost monitor for AI model usage.

    Tracks costs by model, project, and time period with configurable
    alerts and export capabilities.

    Example:
        >>> monitor = CostMonitor()
        >>> monitor.record(CostEntry(
        ...     timestamp=time.time(),
        ...     model="gpt-4o",
        ...     tokens_input=100,
        ...     tokens_output=50,
        ...     cost_usd=0.003,
        ... ))
        >>> summary = monitor.get_summary()
        >>> print(f"Total: ${summary.total_cost_usd:.4f}")
    """

    def __init__(self, retention_hours: float = 168.0) -> None:
        """Initialize the cost monitor.

        Args:
            retention_hours: Hours of cost data to retain (default 7 days).
        """
        self._entries: List[CostEntry] = []
        self._lock = threading.Lock()
        self._retention_seconds = retention_hours * 3600
        self._alerts: List[CostAlert] = []
        self._alert_history: List[Tuple[float, CostAlert, float]] = []

    def record(self, entry: CostEntry) -> None:
        """Record a cost entry.

        Args:
            entry: The cost entry to record.
        """
        with self._lock:
            self._entries.append(entry)
            self._cleanup_old_entries()
            self._check_alerts(entry)

    def record_usage(
        self,
        model: str,
        tokens_input: int,
        tokens_output: int,
        cost_per_1k_input: float,
        cost_per_1k_output: float,
        project_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CostEntry:
        """Record usage with automatic cost calculation.

        Args:
            model: Model name.
            tokens_input: Number of input tokens.
            tokens_output: Number of output tokens.
            cost_per_1k_input: Cost per 1K input tokens.
            cost_per_1k_output: Cost per 1K output tokens.
            project_id: Optional project identifier.
            metadata: Additional metadata.

        Returns:
            The created CostEntry.
        """
        cost = (
            (tokens_input / 1000) * cost_per_1k_input
            + (tokens_output / 1000) * cost_per_1k_output
        )
        entry = CostEntry(
            timestamp=time.time(),
            model=model,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost_usd=cost,
            project_id=project_id,
            metadata=metadata or {},
        )
        self.record(entry)
        return entry

    def get_summary(
        self,
        since: Optional[float] = None,
        project_id: Optional[str] = None,
    ) -> CostSummary:
        """Get cost summary for a period.

        Args:
            since: Start timestamp. Uses retention window if None.
            project_id: Filter by project. None means all projects.

        Returns:
            CostSummary for the specified period.
        """
        with self._lock:
            if since is None:
                since = time.time() - self._retention_seconds

            entries = [
                e for e in self._entries
                if e.timestamp >= since
                and (project_id is None or e.project_id == project_id)
            ]

            if not entries:
                return CostSummary(
                    total_cost_usd=0.0,
                    total_tokens=0,
                    total_requests=0,
                    avg_cost_per_request=0.0,
                    cost_by_model={},
                    cost_by_project={},
                    period_start=since,
                    period_end=time.time(),
                )

            total_cost = sum(e.cost_usd for e in entries)
            total_tokens = sum(e.total_tokens for e in entries)

            cost_by_model: Dict[str, float] = defaultdict(float)
            cost_by_project: Dict[str, float] = defaultdict(float)

            for entry in entries:
                cost_by_model[entry.model] += entry.cost_usd
                proj = entry.project_id or "default"
                cost_by_project[proj] += entry.cost_usd

            return CostSummary(
                total_cost_usd=total_cost,
                total_tokens=total_tokens,
                total_requests=len(entries),
                avg_cost_per_request=total_cost / len(entries),
                cost_by_model=dict(cost_by_model),
                cost_by_project=dict(cost_by_project),
                period_start=since,
                period_end=time.time(),
            )

    def get_model_costs(self, since: Optional[float] = None) -> Dict[str, float]:
        """Get costs grouped by model.

        Args:
            since: Start timestamp. Uses retention window if None.

        Returns:
            Dictionary mapping model names to total cost.
        """
        summary = self.get_summary(since=since)
        return summary.cost_by_model

    def get_project_costs(self, since: Optional[float] = None) -> Dict[str, float]:
        """Get costs grouped by project.

        Args:
            since: Start timestamp. Uses retention window if None.

        Returns:
            Dictionary mapping project IDs to total cost.
        """
        summary = self.get_summary(since=since)
        return summary.cost_by_project

    def add_alert(self, alert: CostAlert) -> None:
        """Add a cost alert.

        Args:
            alert: The cost alert configuration.
        """
        self._alerts.append(alert)
        logger.info(
            "Added cost alert: %s (threshold: $%.2f)",
            alert.name,
            alert.threshold_usd,
        )

    def get_alert_history(self) -> List[Tuple[float, CostAlert, float]]:
        """Get history of fired alerts.

        Returns:
            List of (timestamp, alert, current_cost) tuples.
        """
        return list(self._alert_history)

    def export_entries(self, format: str = "json") -> str:
        """Export cost entries.

        Args:
            format: Export format ("json" or "csv").

        Returns:
            Exported data as a string.

        Raises:
            ValueError: If format is not supported.
        """
        import json
        import csv
        import io

        with self._lock:
            if format == "json":
                data = [
                    {
                        "timestamp": e.timestamp,
                        "model": e.model,
                        "tokens_input": e.tokens_input,
                        "tokens_output": e.tokens_output,
                        "cost_usd": e.cost_usd,
                        "project_id": e.project_id,
                        "metadata": e.metadata,
                    }
                    for e in self._entries
                ]
                return json.dumps(data, indent=2)
            elif format == "csv":
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow([
                    "timestamp", "model", "tokens_input", "tokens_output",
                    "cost_usd", "project_id",
                ])
                for e in self._entries:
                    writer.writerow([
                        e.timestamp, e.model, e.tokens_input,
                        e.tokens_output, e.cost_usd, e.project_id or "",
                    ])
                return output.getvalue()
            else:
                raise ValueError(f"Unsupported export format: {format}")

    def reset(self) -> None:
        """Clear all cost data."""
        with self._lock:
            self._entries.clear()
            self._alert_history.clear()
            logger.info("Cost monitor data reset")

    def _cleanup_old_entries(self) -> None:
        """Remove entries older than the retention period."""
        cutoff = time.time() - self._retention_seconds
        self._entries = [e for e in self._entries if e.timestamp >= cutoff]

    def _check_alerts(self, entry: CostEntry) -> None:
        """Check if any alerts should fire.

        Args:
            entry: The latest cost entry.
        """
        for alert in self._alerts:
            if alert.window_seconds > 0:
                window_start = time.time() - alert.window_seconds
                window_cost = sum(
                    e.cost_usd for e in self._entries
                    if e.timestamp >= window_start
                )
                current_cost = window_cost
            else:
                current_cost = sum(e.cost_usd for e in self._entries)

            if current_cost >= alert.threshold_usd:
                self._alert_history.append((time.time(), alert, current_cost))
                logger.warning(
                    "Cost alert fired: %s (cost: $%.2f, threshold: $%.2f)",
                    alert.name,
                    current_cost,
                    alert.threshold_usd,
                )
                if alert.callback:
                    try:
                        alert.callback(alert, current_cost)
                    except Exception as exc:
                        logger.error("Alert callback failed: %s", exc)
