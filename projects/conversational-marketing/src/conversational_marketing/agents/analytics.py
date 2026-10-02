"""Analytics Agent for tracking metrics and generating insights."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog

from conversational_marketing.config.settings import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


@dataclass(frozen=True)
class ConversationMetrics:
    """Metrics for a single conversation."""

    conversation_id: str
    start_time: datetime
    end_time: datetime | None
    message_count: int
    intent: str
    handed_off: bool
    satisfaction_score: float | None
    platform: str


@dataclass(frozen=True)
class AnalyticsSummary:
    """Aggregated analytics summary."""

    total_conversations: int
    active_conversations: int
    handed_off_conversations: int
    average_messages_per_conversation: float
    average_satisfaction: float | None
    intent_distribution: dict[str, int]
    platform_distribution: dict[str, int]
    period_start: datetime
    period_end: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


class AnalyticsAgent:
    """Agent responsible for tracking conversation metrics and generating insights.

    Collects, aggregates, and analyzes conversation data to provide actionable
    business intelligence for marketing optimization.
    """

    def __init__(self) -> None:
        """Initialize the Analytics Agent."""
        self._enabled = settings.agents.analytics.enabled
        self._retention_days = settings.agents.analytics.retention_days
        self._realtime = settings.agents.analytics.realtime_metrics

    async def track_conversation(self, metrics: ConversationMetrics) -> None:
        """Track a conversation's metrics.

        Args:
            metrics: Conversation metrics to track.
        """
        if not self._enabled:
            return

        logger.info(
            "Tracking conversation metrics",
            conversation_id=metrics.conversation_id,
            intent=metrics.intent,
            message_count=metrics.message_count,
            handed_off=metrics.handed_off,
        )

        # In production, this would persist to a database or analytics store
        # For now, we log the metrics for demonstration

    async def get_summary(
        self,
        conversations: list[dict[str, Any]] | None = None,
        days: int = 30,
    ) -> AnalyticsSummary:
        """Generate analytics summary for a given period.

        Args:
            conversations: Optional list of conversation data.
            days: Number of days to include in summary.

        Returns:
            AnalyticsSummary with aggregated metrics.
        """
        if not self._enabled:
            now = datetime.now(timezone.utc)
            return AnalyticsSummary(
                total_conversations=0,
                active_conversations=0,
                handed_off_conversations=0,
                average_messages_per_conversation=0.0,
                average_satisfaction=None,
                intent_distribution={},
                platform_distribution={},
                period_start=now - timedelta(days=days),
                period_end=now,
                metadata={"disabled": True},
            )

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        if conversations is None:
            conversations = []

        # Filter by date range
        filtered = [
            c for c in conversations
            if start_date
            <= datetime.fromisoformat(c.get("start_time", "").replace("Z", "+00:00"))
            <= end_date
        ]

        total = len(filtered)
        active = len([c for c in filtered if not c.get("end_time")])
        handed_off = len([c for c in filtered if c.get("handed_off", False)])

        # Calculate averages
        message_counts = [c.get("message_count", 0) for c in filtered]
        avg_messages = sum(message_counts) / total if total > 0 else 0.0

        satisfaction_scores = [
            c["satisfaction_score"]
            for c in filtered
            if c.get("satisfaction_score") is not None
        ]
        avg_satisfaction = (
            sum(satisfaction_scores) / len(satisfaction_scores)
            if satisfaction_scores
            else None
        )

        # Intent distribution
        intent_dist: dict[str, int] = {}
        for c in filtered:
            intent = c.get("intent", "unknown")
            intent_dist[intent] = intent_dist.get(intent, 0) + 1

        # Platform distribution
        platform_dist: dict[str, int] = {}
        for c in filtered:
            platform = c.get("platform", "unknown")
            platform_dist[platform] = platform_dist.get(platform, 0) + 1

        logger.info(
            "Analytics summary generated",
            total_conversations=total,
            period_days=days,
        )

        return AnalyticsSummary(
            total_conversations=total,
            active_conversations=active,
            handed_off_conversations=handed_off,
            average_messages_per_conversation=avg_messages,
            average_satisfaction=avg_satisfaction,
            intent_distribution=intent_dist,
            platform_distribution=platform_dist,
            period_start=start_date,
            period_end=end_date,
        )

    async def get_realtime_metrics(self) -> dict[str, Any]:
        """Get real-time metrics snapshot.

        Returns:
            Dictionary with current real-time metrics.
        """
        if not self._enabled or not self._realtime:
            return {"enabled": False}

        # In production, this would query a real-time data store
        return {
            "enabled": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active_conversations": 0,
            "messages_last_hour": 0,
            "average_response_time_ms": 0,
        }
