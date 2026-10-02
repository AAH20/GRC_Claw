"""Analytics Collector Agent.

Collects, aggregates, and reports analytics across all domains and
agents in the orchestration system.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from typing import Any

from app.models.analytics import AnalyticsEvent, CrossDomainAnalytics, DomainMetrics

logger = logging.getLogger(__name__)


class AnalyticsCollectorAgent:
    """Agent responsible for collecting and aggregating analytics.

    Tracks events across domains and agents, computes metrics,
    and provides cross-domain analytics summaries.

    Attributes:
        events: Collected analytics events.
        domain_metrics: Per-domain metrics.
        agent_metrics: Per-agent event counts.
    """

    def __init__(self) -> None:
        """Initialize the Analytics Collector Agent."""
        self.events: list[AnalyticsEvent] = []
        self.domain_metrics: dict[str, DomainMetrics] = {}
        self.agent_metrics: dict[str, int] = defaultdict(int)

    def collect_event(self, event: AnalyticsEvent) -> None:
        """Collect a single analytics event.

        Args:
            event: The event to collect.
        """
        self.events.append(event)
        self.agent_metrics[event.agent] += 1

        # Update domain metrics
        if event.domain not in self.domain_metrics:
            self.domain_metrics[event.domain] = DomainMetrics(domain=event.domain)

        metrics = self.domain_metrics[event.domain]
        metrics.total_requests += 1
        metrics.last_activity = event.timestamp

        if event.data.get("success", False):
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1

        # Update average latency if available
        if "latency_ms" in event.data:
            latency = event.data["latency_ms"]
            total = metrics.total_requests
            metrics.average_latency_ms = (
                (metrics.average_latency_ms * (total - 1) + latency) / total
            )

        logger.debug(
            "Collected event: %s (domain=%s, agent=%s)",
            event.event_type,
            event.domain,
            event.agent,
        )

    def record_event(
        self,
        event_type: str,
        domain: str,
        agent: str,
        data: dict[str, Any] | None = None,
    ) -> AnalyticsEvent:
        """Record a new analytics event.

        Args:
            event_type: Type of event.
            domain: Source domain.
            agent: Source agent.
            data: Optional event data.

        Returns:
            The created event.
        """
        event = AnalyticsEvent(
            event_type=event_type,
            domain=domain,
            agent=agent,
            data=data or {},
        )
        self.collect_event(event)
        return event

    def get_domain_metrics(self, domain: str) -> DomainMetrics | None:
        """Get metrics for a specific domain.

        Args:
            domain: Domain name.

        Returns:
            Domain metrics or None if not found.
        """
        return self.domain_metrics.get(domain)

    def get_agent_metrics(self) -> dict[str, int]:
        """Get event counts per agent.

        Returns:
            Dictionary mapping agent names to event counts.
        """
        return dict(self.agent_metrics)

    def get_cross_domain_analytics(self) -> CrossDomainAnalytics:
        """Get aggregated cross-domain analytics.

        Returns:
            Cross-domain analytics summary.
        """
        total_events = len(self.events)

        # Calculate summary statistics
        domain_success_rates: dict[str, float] = {}
        for domain, metrics in self.domain_metrics.items():
            if metrics.total_requests > 0:
                domain_success_rates[domain] = (
                    metrics.successful_requests / metrics.total_requests
                )

        overall_success_rate = (
            sum(domain_success_rates.values()) / len(domain_success_rates)
            if domain_success_rates
            else 0.0
        )

        return CrossDomainAnalytics(
            total_events=total_events,
            domain_metrics=self.domain_metrics,
            agent_metrics=dict(self.agent_metrics),
            period_start=self.events[0].timestamp if self.events else datetime.utcnow(),
            period_end=self.events[-1].timestamp if self.events else datetime.utcnow(),
            summary={
                "overall_success_rate": overall_success_rate,
                "domain_success_rates": domain_success_rates,
                "total_domains": len(self.domain_metrics),
                "total_agents": len(self.agent_metrics),
            },
        )

    def get_events_by_domain(self, domain: str) -> list[AnalyticsEvent]:
        """Get all events for a specific domain.

        Args:
            domain: Domain name.

        Returns:
            List of events for the domain.
        """
        return [e for e in self.events if e.domain == domain]

    def get_events_by_agent(self, agent: str) -> list[AnalyticsEvent]:
        """Get all events for a specific agent.

        Args:
            agent: Agent name.

        Returns:
            List of events for the agent.
        """
        return [e for e in self.events if e.agent == agent]

    def clear_events(self) -> None:
        """Clear all collected events and metrics."""
        self.events.clear()
        self.domain_metrics.clear()
        self.agent_metrics.clear()
        logger.info("Analytics data cleared")
