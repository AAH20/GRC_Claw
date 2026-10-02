"""Analytics router.

Provides endpoints for analytics collection and reporting.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from app.agents.analytics_collector import AnalyticsCollectorAgent
from app.models.analytics import AnalyticsEvent, CrossDomainAnalytics

logger = logging.getLogger(__name__)

router = APIRouter()

# Module-level agent instance (in production, use dependency injection)
_collector = AnalyticsCollectorAgent()


@router.post("/collect", response_model=AnalyticsEvent)
async def collect_analytics_event(event: AnalyticsEvent) -> AnalyticsEvent:
    """Collect an analytics event.

    Args:
        event: The event to collect.

    Returns:
        The collected event.
    """
    _collector.collect_event(event)
    return event


@router.get("/summary", response_model=CrossDomainAnalytics)
async def get_analytics_summary() -> CrossDomainAnalytics:
    """Get cross-domain analytics summary.

    Returns:
        Aggregated analytics across all domains.
    """
    return _collector.get_cross_domain_analytics()


@router.get("/cross-domain", response_model=CrossDomainAnalytics)
async def get_cross_domain_analytics() -> CrossDomainAnalytics:
    """Get detailed cross-domain analytics.

    Returns:
        Detailed cross-domain analytics.
    """
    return _collector.get_cross_domain_analytics()


@router.get("/domains/{domain_name}")
async def get_domain_analytics(domain_name: str) -> dict:
    """Get analytics for a specific domain.

    Args:
        domain_name: Domain name.

    Returns:
        Domain-specific analytics.
    """
    metrics = _collector.get_domain_metrics(domain_name)
    if metrics is None:
        return {"domain": domain_name, "events": [], "metrics": None}
    return {
        "domain": domain_name,
        "metrics": metrics,
        "events": _collector.get_events_by_domain(domain_name),
    }


@router.get("/agents/{agent_name}")
async def get_agent_analytics(agent_name: str) -> dict:
    """Get analytics for a specific agent.

    Args:
        agent_name: Agent name.

    Returns:
        Agent-specific analytics.
    """
    return {
        "agent": agent_name,
        "event_count": _collector.agent_metrics.get(agent_name, 0),
        "events": _collector.get_events_by_agent(agent_name),
    }


@router.post("/record")
async def record_event(
    event_type: str,
    domain: str,
    agent: str,
    data: dict | None = None,
) -> AnalyticsEvent:
    """Record a new analytics event.

    Args:
        event_type: Type of event.
        domain: Source domain.
        agent: Source agent.
        data: Optional event data.

    Returns:
        The recorded event.
    """
    return _collector.record_event(event_type, domain, agent, data)


@router.delete("/events", status_code=204)
async def clear_analytics() -> None:
    """Clear all collected analytics data."""
    _collector.clear_events()
