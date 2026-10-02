"""Tests for tier management agents."""

from __future__ import annotations

import pytest

from tier_management.agents.access_controller import AccessControllerAgent
from tier_management.agents.benefit_manager import BenefitManagerAgent
from tier_management.agents.tier_analytics import TierAnalyticsAgent
from tier_management.agents.tier_evaluator import TierEvaluatorAgent
from tier_management.agents.upgrade_recommender import UpgradeRecommenderAgent
from tier_management.models.schemas import (
    AccessCheckRequest,
    AccessDecision,
    BenefitType,
    UpgradeEligibility,
)


@pytest.mark.asyncio
async def test_tier_evaluator_agent() -> None:
    """Test TierEvaluatorAgent evaluates members correctly."""
    agent = TierEvaluatorAgent()
    await agent.initialize()

    from uuid import uuid4

    result = await agent.execute({
        "member_id": str(uuid4()),
        "current_tier_id": str(uuid4()),
        "target_tier_id": str(uuid4()),
        "member_metrics": {
            "activity_score": 85.0,
            "contribution_score": 80.0,
            "engagement_score": 90.0,
            "tenure_score": 70.0,
        },
    })

    assert result.score > 0
    assert result.score <= 100
    assert result.eligible is True
    assert result.evaluated_by == "TierEvaluatorAgent"
    assert len(result.recommendations) > 0


@pytest.mark.asyncio
async def test_tier_evaluator_agent_low_score() -> None:
    """Test TierEvaluatorAgent with low-scoring member."""
    agent = TierEvaluatorAgent()
    await agent.initialize()

    from uuid import uuid4

    result = await agent.execute({
        "member_id": str(uuid4()),
        "current_tier_id": str(uuid4()),
        "target_tier_id": str(uuid4()),
        "member_metrics": {
            "activity_score": 30.0,
            "contribution_score": 20.0,
            "engagement_score": 25.0,
            "tenure_score": 10.0,
        },
    })

    assert result.score < 70
    assert result.eligible is False
    assert len(result.gaps) > 0


@pytest.mark.asyncio
async def test_upgrade_recommender_agent() -> None:
    """Test UpgradeRecommenderAgent generates recommendations."""
    agent = UpgradeRecommenderAgent()
    await agent.initialize()

    from uuid import uuid4

    result = await agent.execute({
        "member_id": str(uuid4()),
        "current_tier_id": str(uuid4()),
        "member_metrics": {
            "overall_score": 85.0,
        },
    })

    assert result.eligibility == UpgradeEligibility.ELIGIBLE
    assert result.status == "recommended"
    assert result.reason is not None


@pytest.mark.asyncio
async def test_access_controller_agent() -> None:
    """Test AccessControllerAgent makes access decisions."""
    agent = AccessControllerAgent()
    await agent.initialize()

    from uuid import uuid4

    request = AccessCheckRequest(
        member_id=uuid4(),
        resource="test_resource",
        action="read",
    )

    result = await agent.execute(request)

    assert result.decision in [AccessDecision.GRANTED, AccessDecision.DENIED]
    assert result.member_id == request.member_id
    assert result.resource == request.resource


@pytest.mark.asyncio
async def test_access_controller_agent_with_policy() -> None:
    """Test AccessControllerAgent with configured policy."""
    agent = AccessControllerAgent()
    await agent.initialize()

    from datetime import datetime, timezone
    from uuid import uuid4

    from tier_management.models.schemas import AccessPolicy

    policy = AccessPolicy(
        id=uuid4(),
        name="Test Policy",
        tier_id=uuid4(),
        resource="premium_content",
        action="read",
        effect=AccessDecision.GRANTED,
        conditions={},
        priority=10,
        enabled=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    agent.add_policy(policy)

    request = AccessCheckRequest(
        member_id=uuid4(),
        resource="premium_content",
        action="read",
    )

    result = await agent.execute(request)
    assert result.decision == AccessDecision.GRANTED


@pytest.mark.asyncio
async def test_benefit_manager_agent_create() -> None:
    """Test BenefitManagerAgent creates benefits."""
    agent = BenefitManagerAgent()
    await agent.initialize()

    from uuid import uuid4

    result = await agent.execute({
        "operation": "create",
        "benefit_data": {
            "name": "Test Benefit",
            "benefit_type": "percentage_discount",
            "value": 15.0,
            "tier_ids": [str(uuid4())],
        },
    })

    assert result.name == "Test Benefit"
    assert result.benefit_type == BenefitType.PERCENTAGE_DISCOUNT
    assert result.active is True


@pytest.mark.asyncio
async def test_benefit_manager_agent_deactivate() -> None:
    """Test BenefitManagerAgent deactivates benefits."""
    agent = BenefitManagerAgent()
    await agent.initialize()

    from uuid import uuid4

    # Create a benefit
    created = await agent.execute({
        "operation": "create",
        "benefit_data": {
            "name": "Test Benefit",
            "benefit_type": "free_shipping",
            "value": 0.0,
            "tier_ids": [str(uuid4())],
        },
    })

    # Deactivate it
    result = await agent.execute({
        "operation": "deactivate",
        "benefit_id": str(created.id),
    })

    assert result.active is False


@pytest.mark.asyncio
async def test_tier_analytics_agent() -> None:
    """Test TierAnalyticsAgent generates analytics."""
    agent = TierAnalyticsAgent()
    await agent.initialize()

    from datetime import datetime, timezone
    from uuid import uuid4

    result = await agent.execute({
        "tier_id": str(uuid4()),
        "period_start": datetime(2024, 1, 1, tzinfo=timezone.utc),
        "period_end": datetime(2024, 1, 31, tzinfo=timezone.utc),
        "metrics": {
            "total_members": 500,
            "active_members": 350,
            "new_members": 50,
            "churned_members": 10,
            "monthly_fee": 29.99,
            "daily_active_rate": 0.7,
            "weekly_active_rate": 0.8,
        },
    })

    assert result.total_members == 500
    assert result.active_members == 350
    assert result.revenue > 0
    assert len(result.insights) > 0
    assert result.generated_by == "TierAnalyticsAgent"


@pytest.mark.asyncio
async def test_agent_health_checks() -> None:
    """Test all agents pass health checks after initialization."""
    agents = [
        TierEvaluatorAgent(),
        UpgradeRecommenderAgent(),
        AccessControllerAgent(),
        BenefitManagerAgent(),
        TierAnalyticsAgent(),
    ]

    for agent in agents:
        await agent.initialize()
        assert await agent.health_check() is True
