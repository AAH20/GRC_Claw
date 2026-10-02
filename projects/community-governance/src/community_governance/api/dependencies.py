"""API dependencies for community governance."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from community_governance.agents import (
    DisputeResolverAgent,
    GovernanceAnalyticsAgent,
    GovernanceExplainerAgent,
    PolicyManagerAgent,
    RuleEnforcerAgent,
)

from community_governance.integrations import MetricsIntegration

# Global agent instances (initialized in main.py)
_agents: dict[str, Any] = {}
_metrics: MetricsIntegration | None = None


def set_agents(agents: dict[str, Any]) -> None:
    """Set the global agent instances.

    Args:
        agents: Dictionary of agent instances.
    """
    global _agents
    _agents = agents


def get_agents() -> dict[str, Any]:
    """Get the global agent instances.

    Returns:
        Dictionary of agent instances.
    """
    return _agents


def get_rule_enforcer() -> RuleEnforcerAgent:
    """Get the rule enforcer agent.

    Returns:
        The rule enforcer agent instance.
    """
    return _agents["rule_enforcer"]


def get_dispute_resolver() -> DisputeResolverAgent:
    """Get the dispute resolver agent.

    Returns:
        The dispute resolver agent instance.
    """
    return _agents["dispute_resolver"]


def get_policy_manager() -> PolicyManagerAgent:
    """Get the policy manager agent.

    Returns:
        The policy manager agent instance.
    """
    return _agents["policy_manager"]


def get_governance_analytics() -> GovernanceAnalyticsAgent:
    """Get the governance analytics agent.

    Returns:
        The governance analytics agent instance.
    """
    return _agents["governance_analytics"]


def get_governance_explainer() -> GovernanceExplainerAgent:
    """Get the governance explainer agent.

    Returns:
        The governance explainer agent instance.
    """
    return _agents["governance_explainer"]


def set_metrics(metrics: MetricsIntegration) -> None:
    """Set the global metrics integration.

    Args:
        metrics: The metrics integration instance.
    """
    global _metrics
    _metrics = metrics


def get_metrics() -> MetricsIntegration:
    """Get the global metrics integration.

    Returns:
        The metrics integration instance.
    """
    global _metrics

    if _metrics is None:
        _metrics = MetricsIntegration()
    return _metrics
