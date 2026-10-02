"""Tests for agent implementations."""

from __future__ import annotations

import pytest

from community_governance.agents import (
    DisputeResolverAgent,
    GovernanceAnalyticsAgent,
    GovernanceExplainerAgent,
    PolicyManagerAgent,
    RuleEnforcerAgent,
)
from community_governance.models.dispute import Dispute, DisputeCreate, DisputePriority, DisputeStatus
from community_governance.models.governance_action import (
    ActionStatus,
    ActionType,
    GovernanceAction,
    GovernanceActionCreate,
)
from community_governance.models.policy import PolicyCreate, PolicyScope
from community_governance.models.rule import Rule, RuleCategory, RuleCreate, RuleSeverity


@pytest.mark.asyncio
async def test_rule_enforcer_agent() -> None:
    """Test the RuleEnforcerAgent."""
    rules = [
        Rule(
            name="Test Rule",
            description="A test rule",
            category=RuleCategory.CONTENT_MODERATION,
            severity=RuleSeverity.HIGH,
            conditions={"action_types": ["create"]},
        )
    ]
    agent = RuleEnforcerAgent(rules=rules)
    await agent.initialize()

    action = GovernanceAction(
        action_type=ActionType.CREATE,
        target_id="post_123",
        target_type="post",
        actor_id="user_456",
    )

    results = await agent.execute({"action": action, "context": {}})
    assert len(results) == 1
    assert results[0].rule_name == "Test Rule"
    assert results[0].is_violation is True


@pytest.mark.asyncio
async def test_dispute_resolver_agent() -> None:
    """Test the DisputeResolverAgent."""
    dispute = Dispute(
        title="Test Dispute",
        description="A test dispute",
        category="test",
        initiator_id="user_1",
        priority=DisputePriority.HIGH,
    )
    agent = DisputeResolverAgent(disputes=[dispute])
    await agent.initialize()

    resolution = await agent.execute({"dispute_id": dispute.id, "context": {}})
    assert resolution.resolution_type is not None
    assert resolution.outcome is not None
    assert dispute.status == DisputeStatus.RESOLVED


@pytest.mark.asyncio
async def test_policy_manager_agent() -> None:
    """Test the PolicyManagerAgent."""
    agent = PolicyManagerAgent()
    await agent.initialize()

    policy_data = PolicyCreate(
        name="Test Policy",
        description="A test policy",
        scope=PolicyScope.GLOBAL,
    )
    policy = await agent.execute(
        {"operation": "create", "policy_data": policy_data.model_dump()}
    )
    assert policy.name == "Test Policy"
    assert policy.status.value == "draft"


@pytest.mark.asyncio
async def test_governance_analytics_agent() -> None:
    """Test the GovernanceAnalyticsAgent."""
    agent = GovernanceAnalyticsAgent()
    await agent.initialize()

    analytics = await agent.execute({})
    assert analytics.health_score is not None
    assert isinstance(analytics.recommendations, list)


@pytest.mark.asyncio
async def test_governance_explainer_agent() -> None:
    """Test the GovernanceExplainerAgent."""
    agent = GovernanceExplainerAgent()
    await agent.initialize()

    explanation = await agent.execute(
        {
            "explanation_type": "action",
            "target_data": {
                "action_type": "create",
                "status": "approved",
                "reason": "Test reason",
            },
            "audience": "member",
            "detail_level": "standard",
        }
    )
    assert "summary" in explanation
    assert "details" in explanation


@pytest.mark.asyncio
async def test_agent_health_checks() -> None:
    """Test health check for all agents."""
    agents = [
        RuleEnforcerAgent(),
        DisputeResolverAgent(),
        PolicyManagerAgent(),
        GovernanceAnalyticsAgent(),
        GovernanceExplainerAgent(),
    ]

    for agent in agents:
        await agent.initialize()
        health = await agent.health_check()
        assert health["status"] == "healthy"
        assert health["agent_name"] is not None
