"""Tests for Pydantic models."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from moderation_analytics.models import (
    ModerationAction,
    ModerationAnalytics,
    ModerationPrediction,
    ModeratorPerformance,
    PolicyEffectiveness,
    SeverityLevel,
    Trend,
    TrendDirection,
)
from pydantic import ValidationError


def test_moderation_analytics_valid():
    """Test valid ModerationAnalytics creation."""
    now = datetime.utcnow()
    analytics = ModerationAnalytics(
        total_events=100,
        total_actions=80,
        action_breakdown={ModerationAction.APPROVE: 50, ModerationAction.REJECT: 30},
        severity_distribution={SeverityLevel.LOW: 40, SeverityLevel.HIGH: 10},
        average_response_time_seconds=2.5,
        period_start=now - timedelta(days=1),
        period_end=now,
    )
    assert analytics.total_events == 100


def test_moderation_analytics_invalid_period():
    """Test ModerationAnalytics with invalid period raises error."""
    now = datetime.utcnow()
    with pytest.raises(ValidationError):
        ModerationAnalytics(
            total_events=100,
            total_actions=80,
            average_response_time_seconds=2.5,
            period_start=now,
            period_end=now - timedelta(days=1),
        )


def test_trend_valid():
    """Test valid Trend creation."""
    now = datetime.utcnow()
    trend = Trend(
        metric_name="test_metric",
        direction=TrendDirection.INCREASING,
        change_percentage=15.5,
        confidence=0.85,
        data_points=[1.0, 2.0, 3.0],
        start_date=now - timedelta(days=7),
        end_date=now,
    )
    assert trend.metric_name == "test_metric"


def test_moderator_performance_valid():
    """Test valid ModeratorPerformance creation."""
    now = datetime.utcnow()
    perf = ModeratorPerformance(
        moderator_id="mod_001",
        moderator_name="Test Mod",
        total_reviews=100,
        accuracy=0.95,
        average_response_time_seconds=1.5,
        consistency_score=0.9,
        escalation_rate=0.05,
        period_start=now - timedelta(days=30),
        period_end=now,
    )
    assert perf.accuracy == 0.95


def test_policy_effectiveness_valid():
    """Test valid PolicyEffectiveness creation."""
    now = datetime.utcnow()
    eff = PolicyEffectiveness(
        policy_id="pol_001",
        policy_name="Test Policy",
        policy_version="1.0",
        total_violations=100,
        total_enforcements=90,
        detection_rate=0.9,
        false_positive_rate=0.1,
        false_negative_rate=0.05,
        user_appeal_rate=0.2,
        appeal_success_rate=0.25,
        period_start=now - timedelta(days=30),
        period_end=now,
        effectiveness_score=0.85,
    )
    assert eff.effectiveness_score == 0.85


def test_moderation_prediction_valid():
    """Test valid ModerationPrediction creation."""
    pred = ModerationPrediction(
        prediction_type="workload",
        target_date=datetime.utcnow() + timedelta(days=7),
        predicted_value=150.0,
        confidence_interval=(120.0, 180.0),
        confidence=0.75,
    )
    assert pred.predicted_value == 150.0
