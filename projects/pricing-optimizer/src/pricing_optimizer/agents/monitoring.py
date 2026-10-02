"""Monitoring Agent.

Tracks KPIs, detects anomalies in pricing performance, and triggers
re-optimization when needed.
"""

from __future__ import annotations

import statistics
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class MetricType(str, Enum):
    """Types of metrics tracked by the monitoring agent."""

    CONVERSION_RATE = "conversion_rate"
    AVERAGE_ORDER_VALUE = "average_order_value"
    REVENUE_PER_VISITOR = "revenue_per_visitor"
    PRICE_ELASTICITY = "price_elasticity"
    COMPETITIVE_POSITION = "competitive_position"
    MARGIN_PERCENT = "margin_percent"


class AnomalySeverity(str, Enum):
    """Severity levels for detected anomalies."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MetricDataPoint(BaseModel):
    """A single metric data point."""

    metric_type: MetricType
    product_id: str
    value: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnomalyAlert(BaseModel):
    """An alert generated when an anomaly is detected."""

    alert_id: str
    product_id: str
    metric_type: MetricType
    severity: AnomalySeverity
    expected_value: float
    actual_value: float
    deviation_std: float
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged: bool = False


class MonitoringConfig(BaseModel):
    """Configuration for the Monitoring Agent."""

    metrics_interval_minutes: int = 5
    anomaly_threshold_std: float = 2.0
    history_window_size: int = 100
    alert_cooldown_minutes: int = 30


@dataclass
class _MetricHistory:
    """Internal storage for metric history."""

    values: deque[float] = field(default_factory=lambda: deque(maxlen=100))
    timestamps: deque[datetime] = field(default_factory=lambda: deque(maxlen=100))

    def add(self, value: float, timestamp: datetime) -> None:
        """Add a data point to the history."""
        self.values.append(value)
        self.timestamps.append(timestamp)

    def get_stats(self) -> tuple[float, float] | None:
        """Get mean and standard deviation of the history.

        Returns:
            Tuple of (mean, std_dev) or None if insufficient data.
        """
        if len(self.values) < 10:
            return None
        mean = statistics.mean(self.values)
        std_dev = statistics.stdev(self.values) if len(self.values) > 1 else 0.0
        return mean, std_dev

    def is_ready(self) -> bool:
        """Check if enough data has been collected for analysis."""
        return len(self.values) >= 10


class MonitoringAgent:
    """Agent responsible for monitoring pricing performance and detecting anomalies.

    Continuously tracks key pricing metrics, establishes baselines,
    and generates alerts when performance deviates significantly
    from expected ranges.
    """

    def __init__(self, config: MonitoringConfig | None = None) -> None:
        """Initialize the Monitoring Agent.

        Args:
            config: Agent configuration. Uses defaults if not provided.
        """
        self.config = config or MonitoringConfig()
        self._history: dict[str, _MetricHistory] = {}
        self._alerts: dict[str, AnomalyAlert] = {}
        self._last_alert_time: dict[str, datetime] = {}
        logger.info(
            "monitoring_agent_initialized",
            interval_minutes=self.config.metrics_interval_minutes,
            threshold_std=self.config.anomaly_threshold_std,
        )

    def _get_key(self, metric_type: MetricType, product_id: str) -> str:
        """Generate a unique key for metric storage.

        Args:
            metric_type: The type of metric.
            product_id: The product identifier.

        Returns:
            Unique storage key.
        """
        return f"{metric_type.value}:{product_id}"

    def record_metric(self, data_point: MetricDataPoint) -> None:
        """Record a metric data point.

        Args:
            data_point: The metric data point to record.
        """
        key = self._get_key(data_point.metric_type, data_point.product_id)

        if key not in self._history:
            self._history[key] = _MetricHistory()

        self._history[key].add(data_point.value, data_point.timestamp)

        logger.debug(
            "metric_recorded",
            metric_type=data_point.metric_type.value,
            product_id=data_point.product_id,
            value=data_point.value,
        )

    def check_anomaly(self, data_point: MetricDataPoint) -> AnomalyAlert | None:
        """Check if a metric data point is anomalous.

        Args:
            data_point: The metric data point to check.

        Returns:
            An anomaly alert if detected, None otherwise.
        """
        key = self._get_key(data_point.metric_type, data_point.product_id)
        history = self._history.get(key)

        if history is None or not history.is_ready():
            return None

        stats = history.get_stats()
        if stats is None:
            return None

        mean, std_dev = stats
        if std_dev == 0:
            return None

        deviation = abs(data_point.value - mean) / std_dev

        if deviation < self.config.anomaly_threshold_std:
            return None

        # Check cooldown
        cooldown_key = key
        last_alert = self._last_alert_time.get(cooldown_key)
        if last_alert and datetime.utcnow() - last_alert < timedelta(
            minutes=self.config.alert_cooldown_minutes
        ):
            return None

        # Determine severity
        if deviation >= 4.0:
            severity = AnomalySeverity.CRITICAL
        elif deviation >= 3.0:
            severity = AnomalySeverity.HIGH
        elif deviation >= 2.5:
            severity = AnomalySeverity.MEDIUM
        else:
            severity = AnomalySeverity.LOW

        direction = "above" if data_point.value > mean else "below"

        alert = AnomalyAlert(
            alert_id=f"alert_{key}_{datetime.utcnow().timestamp()}",
            product_id=data_point.product_id,
            metric_type=data_point.metric_type,
            severity=severity,
            expected_value=round(mean, 4),
            actual_value=round(data_point.value, 4),
            deviation_std=round(deviation, 2),
            description=(
                f"{data_point.metric_type.value} for {data_point.product_id} is "
                f"{deviation:.1f} std dev {direction} expected value "
                f"({data_point.value:.4f} vs {mean:.4f})"
            ),
        )

        self._alerts[alert.alert_id] = alert
        self._last_alert_time[cooldown_key] = datetime.utcnow()

        logger.warning(
            "anomaly_detected",
            alert_id=alert.alert_id,
            product_id=data_point.product_id,
            metric_type=data_point.metric_type.value,
            severity=severity.value,
            deviation_std=deviation,
        )

        return alert

    def get_alerts(
        self,
        product_id: str | None = None,
        severity: AnomalySeverity | None = None,
        acknowledged: bool | None = None,
    ) -> list[AnomalyAlert]:
        """Get alerts with optional filtering.

        Args:
            product_id: Filter by product.
            severity: Filter by severity.
            acknowledged: Filter by acknowledgment status.

        Returns:
            List of matching alerts.
        """
        alerts = list(self._alerts.values())

        if product_id:
            alerts = [a for a in alerts if a.product_id == product_id]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if acknowledged is not None:
            alerts = [a for a in alerts if a.acknowledged == acknowledged]

        return sorted(alerts, key=lambda a: a.created_at, reverse=True)

    def acknowledge_alert(self, alert_id: str) -> AnomalyAlert:
        """Acknowledge an alert.

        Args:
            alert_id: The alert to acknowledge.

        Returns:
            The updated alert.

        Raises:
            KeyError: If alert is not found.
        """
        alert = self._alerts.get(alert_id)
        if alert is None:
            raise KeyError(f"Alert {alert_id} not found")

        alert.acknowledged = True
        logger.info("alert_acknowledged", alert_id=alert_id)
        return alert

    def get_metric_summary(
        self,
        metric_type: MetricType,
        product_id: str,
    ) -> dict[str, Any] | None:
        """Get a summary of a metric's historical performance.

        Args:
            metric_type: The metric type.
            product_id: The product identifier.

        Returns:
            Summary dict with statistics, or None if no data.
        """
        key = self._get_key(metric_type, product_id)
        history = self._history.get(key)

        if history is None or not history.is_ready():
            return None

        stats = history.get_stats()
        if stats is None:
            return None

        mean, std_dev = stats
        values = list(history.values)

        return {
            "metric_type": metric_type.value,
            "product_id": product_id,
            "count": len(values),
            "mean": round(mean, 4),
            "std_dev": round(std_dev, 4),
            "min": round(min(values), 4),
            "max": round(max(values), 4),
            "latest": round(values[-1], 4),
        }

    def should_trigger_reoptimization(
        self,
        product_id: str,
        metric_type: MetricType = MetricType.CONVERSION_RATE,
    ) -> bool:
        """Determine if re-optimization should be triggered for a product.

        Args:
            product_id: The product to check.
            metric_type: The metric to evaluate.

        Returns:
            True if re-optimization is recommended.
        """
        recent_alerts = [
            a
            for a in self.get_alerts(product_id=product_id)
            if a.metric_type == metric_type
            and not a.acknowledged
            and a.severity in (AnomalySeverity.HIGH, AnomalySeverity.CRITICAL)
            and datetime.utcnow() - a.created_at < timedelta(hours=24)
        ]

        should_trigger = len(recent_alerts) >= 2

        if should_trigger:
            logger.info(
                "reoptimization_triggered",
                product_id=product_id,
                metric_type=metric_type.value,
                alert_count=len(recent_alerts),
            )

        return should_trigger
