"""
Tests for Customer Retention agents.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from customer_retention.agents.retention import (
    ActionType,
    CustomerHealth,
    RetentionAction,
    RetentionAgent,
    RiskLevel,
)


class TestRetentionAgent:
    """Tests for RetentionAgent."""

    @pytest.fixture
    def agent(self) -> RetentionAgent:
        return RetentionAgent()

    def test_assess_health_low_risk(self, agent: RetentionAgent) -> None:
        health = agent.assess_health(
            customer_id="c1",
            days_since_last_active=2,
            total_spend=500.0,
            engagement_trend="improving",
        )
        assert isinstance(health, CustomerHealth)
        assert health.risk_level == RiskLevel.LOW
        assert health.health_score >= 70

    def test_assess_health_critical_risk(self, agent: RetentionAgent) -> None:
        health = agent.assess_health(
            customer_id="c2",
            days_since_last_active=60,
            total_spend=10.0,
            engagement_trend="declining",
        )
        assert isinstance(health, CustomerHealth)
        assert health.risk_level == RiskLevel.CRITICAL
        assert health.health_score < 30

    def test_assess_health_medium_risk(self, agent: RetentionAgent) -> None:
        health = agent.assess_health(
            customer_id="c3",
            days_since_last_active=15,
            total_spend=100.0,
            engagement_trend="stable",
        )
        assert isinstance(health, CustomerHealth)
        assert health.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH)

    def test_generate_actions_critical(self, agent: RetentionAgent) -> None:
        health = CustomerHealth(
            customer_id="c1",
            health_score=15.0,
            risk_level=RiskLevel.CRITICAL,
            days_since_last_active=45,
            total_spend=50.0,
            engagement_trend="declining",
        )
        actions = agent.generate_actions(health)
        assert len(actions) >= 2
        assert any(a.action_type == ActionType.CALL for a in actions)
        assert any(a.action_type == ActionType.DISCOUNT for a in actions)

    def test_generate_actions_low_risk(self, agent: RetentionAgent) -> None:
        health = CustomerHealth(
            customer_id="c2",
            health_score=85.0,
            risk_level=RiskLevel.LOW,
            days_since_last_active=2,
            total_spend=500.0,
            engagement_trend="improving",
        )
        actions = agent.generate_actions(health)
        assert len(actions) == 0

    def test_should_intervene_high_risk(self, agent: RetentionAgent) -> None:
        health = CustomerHealth(
            customer_id="c1",
            health_score=25.0,
            risk_level=RiskLevel.HIGH,
            days_since_last_active=30,
            total_spend=50.0,
            engagement_trend="declining",
        )
        assert agent.should_intervene(health) is True

    def test_should_not_intervene_low_risk(self, agent: RetentionAgent) -> None:
        health = CustomerHealth(
            customer_id="c2",
            health_score=90.0,
            risk_level=RiskLevel.LOW,
            days_since_last_active=1,
            total_spend=1000.0,
            engagement_trend="improving",
        )
        assert agent.should_intervene(health) is False
