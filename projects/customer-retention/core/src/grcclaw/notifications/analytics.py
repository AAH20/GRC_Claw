"""
Notification analytics for GRC_Claw — tracks delivery metrics and trends.
"""

from __future__ import annotations

import logging
import statistics
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

from .models import (
    AnalyticsSummary,
    DeliveryResult,
    Notification,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)

logger = logging.getLogger(__name__)


class NotificationAnalytics:
    """
    Collects and analyzes notification delivery metrics.

    Tracks:
    - Delivery rates by channel, priority, and type
    - Latency percentiles (p50, p95, p99)
    - Failure analysis and top error patterns
    - Trend analysis over time
    - Channel health scoring
    """

    def __init__(self, retention_hours: int = 168):
        self._events: list[dict[str, Any]] = []
        self._retention_hours = retention_hours
        self._channel_stats: dict[str, dict[str, Any]] = defaultdict(lambda: {
            "sent": 0,
            "delivered": 0,
            "failed": 0,
            "latencies": [],
            "errors": defaultdict(int),
        })
        self._hourly_stats: dict[str, dict[str, Any]] = defaultdict(lambda: {
            "sent": 0,
            "delivered": 0,
            "failed": 0,
        })
        self._alert_correlations: dict[str, int] = defaultdict(int)

    # ─── Event Recording ─────────────────────────────────────────────────────

    def record(self, notification: Notification) -> None:
        """Record a notification and its delivery results for analytics."""
        event = {
            "notification_id": notification.id,
            "type": notification.type.value,
            "priority": notification.priority.value,
            "status": notification.status.value,
            "source": notification.source,
            "channels": notification.channels,
            "recipients_count": len(notification.recipients),
            "created_at": notification.created_at,
            "delivered_at": notification.delivered_at,
            "retry_count": notification.retry_count,
            "correlation_id": notification.correlation_id,
            "results": [r.to_dict() for r in notification.delivery_results],
        }
        self._events.append(event)

        # Update channel stats
        for result in notification.delivery_results:
            self._update_channel_stats(result)

        # Update hourly stats
        self._update_hourly_stats(notification)

        # Track alert correlations
        if notification.correlation_id:
            self._alert_correlations[notification.correlation_id] += 1

        # Prune old events
        self._prune_old_events()

    def record_delivery_result(self, result: DeliveryResult, notification: Notification) -> None:
        """Record a single delivery result."""
        self._update_channel_stats(result)

    # ─── Channel Statistics ──────────────────────────────────────────────────

    def _update_channel_stats(self, result: DeliveryResult) -> None:
        """Update statistics for a channel based on a delivery result."""
        stats = self._channel_stats[result.channel]
        stats["sent"] += 1
        if result.success:
            stats["delivered"] += 1
        else:
            stats["failed"] += 1
            if result.error:
                stats["errors"][result.error] += 1
        stats["latencies"].append(result.latency_ms)

    def _update_hourly_stats(self, notification: Notification) -> None:
        """Update hourly aggregated statistics."""
        try:
            dt = datetime.fromisoformat(notification.created_at.replace("Z", "+00:00"))
            hour_key = dt.strftime("%Y-%m-%d-%H")
            stats = self._hourly_stats[hour_key]
            stats["sent"] += 1
            if notification.status == NotificationStatus.DELIVERED:
                stats["delivered"] += 1
            elif notification.status == NotificationStatus.FAILED:
                stats["failed"] += 1
        except (ValueError, TypeError):
            pass

    # ─── Analytics Queries ───────────────────────────────────────────────────

    def get_summary(
        self,
        hours: int = 24,
        channel: Optional[str] = None,
    ) -> AnalyticsSummary:
        """Get an analytics summary for the specified time period."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()

        # Filter events in the time window
        relevant = [
            e for e in self._events
            if e.get("created_at", "") >= cutoff_str
            and (channel is None or channel in e.get("channels", []))
        ]

        total_sent = len(relevant)
        total_delivered = sum(1 for e in relevant if e["status"] == NotificationStatus.DELIVERED.value)
        total_failed = sum(1 for e in relevant if e["status"] == NotificationStatus.FAILED.value)
        total_suppressed = sum(1 for e in relevant if e["status"] == NotificationStatus.SUPPRESSED.value)

        # Compute latencies
        all_latencies = []
        for event in relevant:
            for result in event.get("results", []):
                if result.get("success") and result.get("latency_ms", 0) > 0:
                    all_latencies.append(result["latency_ms"])

        delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0.0

        # By channel
        by_channel = self._compute_channel_breakdown(relevant)

        # By priority
        by_priority = self._compute_priority_breakdown(relevant)

        # By type
        by_type = self._compute_type_breakdown(relevant)

        # By status
        by_status: dict[str, int] = defaultdict(int)
        for event in relevant:
            by_status[event["status"]] += 1

        # Top failures
        top_failures = self._compute_top_failures(relevant)

        return AnalyticsSummary(
            total_sent=total_sent,
            total_delivered=total_delivered,
            total_failed=total_failed,
            total_suppressed=total_suppressed,
            delivery_rate=round(delivery_rate, 2),
            avg_latency_ms=round(statistics.mean(all_latencies), 2) if all_latencies else 0.0,
            p50_latency_ms=round(self._percentile(all_latencies, 50), 2) if all_latencies else 0.0,
            p95_latency_ms=round(self._percentile(all_latencies, 95), 2) if all_latencies else 0.0,
            p99_latency_ms=round(self._percentile(all_latencies, 99), 2) if all_latencies else 0.0,
            by_channel=by_channel,
            by_priority=by_priority,
            by_type=by_type,
            by_status=dict(by_status),
            top_failures=top_failures,
            period_start=cutoff.isoformat(),
            period_end=datetime.now(timezone.utc).isoformat(),
        )

    def get_channel_health(self) -> dict[str, dict[str, Any]]:
        """Get health metrics for each channel."""
        health = {}
        for channel_name, stats in self._channel_stats.items():
            total = stats["sent"]
            delivered = stats["delivered"]
            failed = stats["failed"]
            latencies = stats["latencies"]

            delivery_rate = (delivered / total * 100) if total > 0 else 100.0
            avg_latency = statistics.mean(latencies) if latencies else 0.0
            p95_latency = self._percentile(latencies, 95) if latencies else 0.0

            # Health score: 0-100
            # 50% weight on delivery rate, 30% on latency, 20% on volume consistency
            delivery_score = delivery_rate * 0.5
            latency_score = max(0, 30 - (p95_latency / 100)) if p95_latency > 0 else 30
            volume_score = 20 if total > 0 else 0
            health_score = min(100, delivery_score + latency_score + volume_score)

            # Determine status
            if health_score >= 90:
                status = "healthy"
            elif health_score >= 70:
                status = "degraded"
            elif health_score >= 50:
                status = "unhealthy"
            else:
                status = "critical"

            health[channel_name] = {
                "total_sent": total,
                "total_delivered": delivered,
                "total_failed": failed,
                "delivery_rate": round(delivery_rate, 2),
                "avg_latency_ms": round(avg_latency, 2),
                "p95_latency_ms": round(p95_latency, 2),
                "health_score": round(health_score, 1),
                "status": status,
                "top_errors": dict(sorted(stats["errors"].items(), key=lambda x: -x[1])[:5]),
            }

        return health

    def get_trends(self, hours: int = 24, bucket_minutes: int = 60) -> list[dict[str, Any]]:
        """Get notification volume trends over time."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        bucket_delta = timedelta(minutes=bucket_minutes)

        # Create time buckets
        buckets: dict[str, dict[str, Any]] = {}
        current = cutoff
        while current < datetime.now(timezone.utc):
            key = current.strftime("%Y-%m-%d %H:%M")
            buckets[key] = {
                "timestamp": key,
                "sent": 0,
                "delivered": 0,
                "failed": 0,
                "avg_latency_ms": 0.0,
            }
            current += bucket_delta

        # Fill buckets from events
        for event in self._events:
            try:
                dt = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))
                if dt < cutoff:
                    continue
                key = dt.strftime("%Y-%m-%d %H:%M")
                # Round to nearest bucket
                bucket_key = dt.replace(
                    minute=(dt.minute // bucket_minutes) * bucket_minutes,
                    second=0,
                    microsecond=0,
                ).strftime("%Y-%m-%d %H:%M")

                if bucket_key in buckets:
                    bucket = buckets[bucket_key]
                    bucket["sent"] += 1
                    if event["status"] == NotificationStatus.DELIVERED.value:
                        bucket["delivered"] += 1
                    elif event["status"] == NotificationStatus.FAILED.value:
                        bucket["failed"] += 1
            except (ValueError, TypeError):
                continue

        return list(buckets.values())

    def get_top_failures(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get the most common failure patterns."""
        error_counts: dict[str, int] = defaultdict(int)
        error_channels: dict[str, set[str]] = defaultdict(set)

        for event in self._events:
            for result in event.get("results", []):
                if not result.get("success") and result.get("error"):
                    error_key = result["error"][:200]  # Truncate long errors
                    error_counts[error_key] += 1
                    error_channels[error_key].add(result.get("channel", "unknown"))

        sorted_errors = sorted(error_counts.items(), key=lambda x: -x[1])[:limit]
        return [
            {
                "error": error,
                "count": count,
                "channels": list(error_channels[error]),
            }
            for error, count in sorted_errors
        ]

    def get_alert_correlation(self, alert_id: str) -> dict[str, Any]:
        """Get notification correlation data for a specific alert."""
        related = [
            e for e in self._events
            if e.get("correlation_id") == alert_id
        ]

        return {
            "alert_id": alert_id,
            "notification_count": len(related),
            "channels_used": list(set(
                ch for e in related for ch in e.get("channels", [])
            )),
            "all_delivered": all(
                e["status"] == NotificationStatus.DELIVERED.value for e in related
            ) if related else False,
            "first_sent": related[0]["created_at"] if related else None,
            "last_sent": related[-1]["created_at"] if related else None,
        }

    # ─── Helper Methods ──────────────────────────────────────────────────────

    def _compute_channel_breakdown(self, events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Compute per-channel breakdown."""
        breakdown: dict[str, dict[str, Any]] = defaultdict(lambda: {
            "sent": 0, "delivered": 0, "failed": 0, "avg_latency_ms": 0.0,
        })

        for event in events:
            for result in event.get("results", []):
                ch = result.get("channel", "unknown")
                breakdown[ch]["sent"] += 1
                if result.get("success"):
                    breakdown[ch]["delivered"] += 1
                else:
                    breakdown[ch]["failed"] += 1

        # Compute average latencies
        for ch in breakdown:
            latencies = []
            for event in events:
                for result in event.get("results", []):
                    if result.get("channel") == ch and result.get("latency_ms", 0) > 0:
                        latencies.append(result["latency_ms"])
            breakdown[ch]["avg_latency_ms"] = round(statistics.mean(latencies), 2) if latencies else 0.0

        return dict(breakdown)

    def _compute_priority_breakdown(self, events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Compute per-priority breakdown."""
        breakdown: dict[str, dict[str, Any]] = defaultdict(lambda: {
            "sent": 0, "delivered": 0, "failed": 0,
        })

        for event in events:
            priority = event.get("priority", "unknown")
            breakdown[priority]["sent"] += 1
            if event["status"] == NotificationStatus.DELIVERED.value:
                breakdown[priority]["delivered"] += 1
            elif event["status"] == NotificationStatus.FAILED.value:
                breakdown[priority]["failed"] += 1

        return dict(breakdown)

    def _compute_type_breakdown(self, events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Compute per-type breakdown."""
        breakdown: dict[str, dict[str, Any]] = defaultdict(lambda: {
            "sent": 0, "delivered": 0, "failed": 0,
        })

        for event in events:
            ntype = event.get("type", "unknown")
            breakdown[ntype]["sent"] += 1
            if event["status"] == NotificationStatus.DELIVERED.value:
                breakdown[ntype]["delivered"] += 1
            elif event["status"] == NotificationStatus.FAILED.value:
                breakdown[ntype]["failed"] += 1

        return dict(breakdown)

    def _compute_top_failures(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Compute top failure patterns from events."""
        error_counts: dict[str, int] = defaultdict(int)
        for event in events:
            for result in event.get("results", []):
                if not result.get("success") and result.get("error"):
                    error_counts[result["error"][:200]] += 1

        sorted_errors = sorted(error_counts.items(), key=lambda x: -x[1])[:5]
        return [{"error": e, "count": c} for e, c in sorted_errors]

    def _percentile(self, data: list[float], p: float) -> float:
        """Compute the p-th percentile of a dataset."""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        k = (len(sorted_data) - 1) * (p / 100)
        f = int(k)
        c = f + 1 if f + 1 < len(sorted_data) else f
        d = k - f
        return sorted_data[f] + d * (sorted_data[c] - sorted_data[f])

    def _prune_old_events(self) -> None:
        """Remove events older than the retention period."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=self._retention_hours)
        cutoff_str = cutoff.isoformat()
        self._events = [e for e in self._events if e.get("created_at", "") >= cutoff_str]

    # ─── Export ──────────────────────────────────────────────────────────────

    def export_events(self, format: str = "json") -> str:
        """Export all recorded events."""
        if format == "json":
            import json
            return json.dumps(self._events, indent=2, default=str)
        elif format == "csv":
            if not self._events:
                return ""
            import csv
            import io
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=self._events[0].keys())
            writer.writeheader()
            for event in self._events:
                row = {k: str(v) if isinstance(v, (list, dict)) else v for k, v in event.items()}
                writer.writerow(row)
            return output.getvalue()
        return ""

    def clear(self) -> None:
        """Clear all recorded analytics data."""
        self._events.clear()
        self._channel_stats.clear()
        self._hourly_stats.clear()
        self._alert_correlations.clear()
