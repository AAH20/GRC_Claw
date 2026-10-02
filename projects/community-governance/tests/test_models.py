"""Tests for Pydantic models."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from community_governance.models.analytics import GovernanceHealthScore, GovernanceSummary
from community_governance.models.dispute import Dispute, DisputeCreate, DisputePriority, DisputeStatus
from community_governance.models.governance_action import (
    ActionStatus,
    ActionType,
    GovernanceAction,
    GovernanceActionCreate,
)
from community_governance.models.policy import PolicyCreate, PolicyScope, PolicyStatus
from community_governance.models.rule import Rule, RuleCategory, RuleCreate, RuleSeverity


def test_governance_action_create() -> None:
    """Test creating a governance action."""
    action = GovernanceActionCreate(
        action_type=ActionType.CREATE,
        target_id="post_123",
        target_type="post",
        actor_id="user_456",
    )
    assert action.action_type == ActionType.CREATE
    assert action.target_id == "post_123"


def test_governance_action() -> None:
    """Test a full governance action."""
    action = GovernanceAction(
        action_type=ActionType.CREATE,
        target_id="post_123",
        target_type="post",
        actor_id="user_456",
    )
    assert action.status == ActionStatus.PENDING
    assert action.id is not None


def test_rule_create() -> None:
    """Test creating a rule."""
    rule = RuleCreate(
        name="Test Rule",
        description="A test rule",
        category=RuleCategory.CONTENT_MODERATION,
    )
    assert rule.name == "Test Rule"
    assert rule.severity == RuleSeverity.MEDIUM


def test_rule() -> None:
    """Test a full rule."""
    rule = Rule(
        name="Test Rule",
        description="A test rule",
        category=RuleCategory.CONTENT_MODERATION,
    )
    assert rule.is_active is True
    assert rule.version == 1


def test_dispute_create() -> None:
    """Test creating a dispute."""
    dispute = DisputeCreate(
        title="Test Dispute",
        description="A test dispute",
        category="test",
        initiator_id="user_1",
    )
    assert dispute.title == "Test Dispute"
    assert dispute.priority == DisputePriority.MEDIUM


def test_dispute() -> None:
    """Test a full dispute."""
    dispute = Dispute(
        title="Test Dispute",
        description="A test dispute",
        category="test",
        initiator_id="user_1",
    )
    assert dispute.status == DisputeStatus.OPEN
    assert dispute.id is not None


def test_policy_create() -> None:
    """Test creating a policy."""
    policy = PolicyCreate(
        name="Test Policy",
        description="A test policy",
        scope=PolicyScope.GLOBAL,
    )
    assert policy.name == "Test Policy"


def test_governance_health_score() -> None:
    """Test governance health score."""
    score = GovernanceHealthScore(
        overall_score=85.5,
        rule_compliance_rate=90.0,
        dispute_resolution_rate=80.0,
        policy_adherence_rate=85.0,
        average_resolution_time_hours=24.0,
        active_violations_count=5,
        pending_disputes_count=3,
    )
    assert score.overall_score == 85.5


def test_governance_summary() -> None:
    """Test governance summary."""
    summary = GovernanceSummary(
        total_active_rules=10,
        total_active_policies=5,
        open_disputes=3,
        pending_actions=7,
        violations_last_24h=2,
        health_score=88.5,
    )
    assert summary.total_active_rules == 10


def test_invalid_rule_name() -> None:
    """Test that empty rule name raises validation error."""
    with pytest.raises(ValidationError):
        RuleCreate(
            name="",
            description="A test rule",
            category=RuleCategory.CONTENT_MODERATION,
        )


def test_invalid_severity() -> None:
    """Test that invalid severity raises validation error."""
    with pytest.raises(ValidationError):
        RuleCreate(
            name="Test Rule",
            description="A test rule",
            category=RuleCategory.CONTENT_MODERATION,
            severity="invalid",
        )
