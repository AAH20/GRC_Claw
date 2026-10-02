"""Tests for Pydantic models."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from tier_management.models.schemas import (
    AccessCheckRequest,
    AccessCheckResponse,
    AccessDecision,
    AccessPolicy,
    Benefit,
    BenefitType,
    HealthResponse,
    Tier,
    TierAnalytics,
    TierEvaluation,
    TierLevel,
    TierStatus,
    UpgradeEligibility,
    UpgradeRequest,
)


def test_tier_model_creation() -> None:
    """Test creating a Tier model instance."""
    tier = Tier(
        name="Gold",
        level=TierLevel.GOLD,
        status=TierStatus.ACTIVE,
        monthly_fee=29.99,
    )
    assert tier.name == "Gold"
    assert tier.level == TierLevel.GOLD
    assert tier.status == TierStatus.ACTIVE
    assert tier.monthly_fee == 29.99
    assert tier.id is not None


def test_tier_model_validation_empty_name() -> None:
    """Test Tier model rejects empty name."""
    with pytest.raises(ValidationError):
        Tier(name="", level=TierLevel.BRONZE)


def test_tier_model_validation_negative_fee() -> None:
    """Test Tier model rejects negative fee."""
    with pytest.raises(ValidationError):
        Tier(
            name="Test",
            level=TierLevel.BRONZE,
            monthly_fee=-10.0,
        )


def test_tier_evaluation_model() -> None:
    """Test creating a TierEvaluation model."""
    evaluation = TierEvaluation(
        member_id=uuid4(),
        current_tier_id=uuid4(),
        target_tier_id=uuid4(),
        eligible=True,
        score=85.0,
    )
    assert evaluation.eligible is True
    assert evaluation.score == 85.0
    assert evaluation.confidence == 0.8


def test_tier_evaluation_score_range() -> None:
    """Test TierEvaluation score must be 0-100."""
    with pytest.raises(ValidationError):
        TierEvaluation(
            member_id=uuid4(),
            current_tier_id=uuid4(),
            target_tier_id=uuid4(),
            eligible=False,
            score=150.0,
        )


def test_upgrade_request_model() -> None:
    """Test creating an UpgradeRequest model."""
    request = UpgradeRequest(
        member_id=uuid4(),
        current_tier_id=uuid4(),
        target_tier_id=uuid4(),
        eligibility=UpgradeEligibility.ELIGIBLE,
    )
    assert request.eligibility == UpgradeEligibility.ELIGIBLE
    assert request.status == "pending"


def test_access_policy_model() -> None:
    """Test creating an AccessPolicy model."""
    policy = AccessPolicy(
        name="Test Policy",
        tier_id=uuid4(),
        resource="forum",
        action="read",
        effect=AccessDecision.GRANTED,
    )
    assert policy.name == "Test Policy"
    assert policy.effect == AccessDecision.GRANTED
    assert policy.enabled is True


def test_access_check_request_model() -> None:
    """Test creating an AccessCheckRequest model."""
    request = AccessCheckRequest(
        member_id=uuid4(),
        resource="api",
        action="write",
    )
    assert request.member_id is not None
    assert request.action == "write"


def test_access_check_response_model() -> None:
    """Test creating an AccessCheckResponse model."""
    response = AccessCheckResponse(
        member_id=uuid4(),
        resource="api",
        action="read",
        decision=AccessDecision.DENIED,
        reason="Tier not sufficient",
    )
    assert response.decision == AccessDecision.DENIED
    assert response.reason == "Tier not sufficient"


def test_benefit_model() -> None:
    """Test creating a Benefit model."""
    benefit = Benefit(
        name="10% Discount",
        benefit_type=BenefitType.PERCENTAGE_DISCOUNT,
        value=10.0,
    )
    assert benefit.name == "10% Discount"
    assert benefit.benefit_type == BenefitType.PERCENTAGE_DISCOUNT
    assert benefit.active is True


def test_tier_analytics_model() -> None:
    """Test creating a TierAnalytics model."""
    analytics = TierAnalytics(
        tier_id=uuid4(),
        period_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        period_end=datetime(2024, 1, 31, tzinfo=timezone.utc),
        total_members=100,
        active_members=80,
    )
    assert analytics.total_members == 100
    assert analytics.active_members == 80
    assert analytics.avg_engagement_score == 0.0


def test_health_response_model() -> None:
    """Test creating a HealthResponse model."""
    response = HealthResponse(
        status="healthy",
        version="1.0.0",
    )
    assert response.status == "healthy"
    assert response.version == "1.0.0"
    assert response.checks == {}
