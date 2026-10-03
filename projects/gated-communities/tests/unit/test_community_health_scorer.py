"""Unit tests for the Community Health Scorer module."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from src.agents.community_health_scorer import (
    CommunityHealthScorer,
    HealthScoreResult,
    RiskItem,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def scorer():
    """Return a default CommunityHealthScorer instance."""
    return CommunityHealthScorer()


@pytest.fixture
def sample_metrics():
    """Return a representative set of community health metrics."""
    return {
        "total_members": 500,
        "active_members_7d": 120,
        "active_members_30d": 250,
        "posts_last_7d": 80,
        "posts_last_30d": 300,
        "comments_last_7d": 200,
        "comments_last_30d": 900,
        "reactions_last_7d": 400,
        "reactions_last_30d": 1500,
        "new_members_7d": 15,
        "new_members_30d": 60,
        "churned_members_7d": 5,
        "churned_members_30d": 20,
        "moderation_actions_7d": 3,
        "moderation_actions_30d": 10,
        "reported_content_7d": 2,
        "reported_content_30d": 8,
        "avg_response_time_hours": 4.5,
        "days_since_last_admin_post": 2,
    }


@pytest.fixture
def healthy_metrics():
    """Return metrics representing a very healthy community."""
    return {
        "total_members": 2000,
        "active_members_7d": 800,
        "active_members_30d": 1500,
        "posts_last_7d": 300,
        "posts_last_30d": 1200,
        "comments_last_7d": 800,
        "comments_last_30d": 3500,
        "reactions_last_7d": 2000,
        "reactions_last_30d": 8000,
        "new_members_7d": 50,
        "new_members_30d": 200,
        "churned_members_7d": 2,
        "churned_members_30d": 8,
        "moderation_actions_7d": 1,
        "moderation_actions_30d": 3,
        "reported_content_7d": 0,
        "reported_content_30d": 2,
        "avg_response_time_hours": 1.0,
        "days_since_last_admin_post": 0,
    }


@pytest.fixture
def unhealthy_metrics():
    """Return metrics representing a struggling community."""
    return {
        "total_members": 300,
        "active_members_7d": 10,
        "active_members_30d": 30,
        "posts_last_7d": 2,
        "posts_last_30d": 10,
        "comments_last_7d": 5,
        "comments_last_30d": 20,
        "reactions_last_7d": 10,
        "reactions_last_30d": 50,
        "new_members_7d": 0,
        "new_members_30d": 1,
        "churned_members_7d": 8,
        "churned_members_30d": 25,
        "moderation_actions_7d": 10,
        "moderation_actions_30d": 40,
        "reported_content_7d": 15,
        "reported_content_30d": 60,
        "avg_response_time_hours": 72.0,
        "days_since_last_admin_post": 30,
    }


@pytest.fixture
def empty_metrics():
    """Return metrics with all zeros (edge case)."""
    return {
        "total_members": 0,
        "active_members_7d": 0,
        "active_members_30d": 0,
        "posts_last_7d": 0,
        "posts_last_30d": 0,
        "comments_last_7d": 0,
        "comments_last_30d": 0,
        "reactions_last_7d": 0,
        "reactions_last_30d": 0,
        "new_members_7d": 0,
        "new_members_30d": 0,
        "churned_members_7d": 0,
        "churned_members_30d": 0,
        "moderation_actions_7d": 0,
        "moderation_actions_30d": 0,
        "reported_content_7d": 0,
        "reported_content_30d": 0,
        "avg_response_time_hours": 0.0,
        "days_since_last_admin_post": 0,
    }


# ---------------------------------------------------------------------------
# Tests: calculate_health_score
# ---------------------------------------------------------------------------


class TestCalculateHealthScore:
    """Tests for CommunityHealthScorer.calculate_health_score."""

    def test_returns_health_score_result(self, scorer, sample_metrics):
        """Should return a HealthScoreResult instance."""
        result = scorer.calculate_health_score(sample_metrics)
        assert isinstance(result, HealthScoreResult)

    def test_score_is_between_0_and_100(self, scorer, sample_metrics):
        """Score must always be in the range [0, 100]."""
        result = scorer.calculate_health_score(sample_metrics)
        assert 0 <= result.score <= 100

    def test_healthy_community_scores_high(self, scorer, healthy_metrics):
        """A healthy community should score above 70."""
        result = scorer.calculate_health_score(healthy_metrics)
        assert result.score > 70

    def test_unhealthy_community_scores_low(self, scorer, unhealthy_metrics):
        """An unhealthy community should score below 40."""
        result = scorer.calculate_health_score(unhealthy_metrics)
        assert result.score < 40

    def test_empty_metrics_returns_zero(self, scorer, empty_metrics):
        """All-zero metrics should yield a score of 0."""
        result = scorer.calculate_health_score(empty_metrics)
        assert result.score == 0

    def test_score_increases_with_better_metrics(self, scorer):
        """Better metrics should produce a higher score."""
        poor = {
            "total_members": 100,
            "active_members_7d": 5,
            "active_members_30d": 10,
            "posts_last_7d": 1,
            "posts_last_30d": 5,
            "comments_last_7d": 2,
            "comments_last_30d": 10,
            "reactions_last_7d": 5,
            "reactions_last_30d": 20,
            "new_members_7d": 0,
            "new_members_30d": 0,
            "churned_members_7d": 5,
            "churned_members_30d": 15,
            "moderation_actions_7d": 8,
            "moderation_actions_30d": 30,
            "reported_content_7d": 10,
            "reported_content_30d": 40,
            "avg_response_time_hours": 48.0,
            "days_since_last_admin_post": 20,
        }
        good = {
            "total_members": 1000,
            "active_members_7d": 400,
            "active_members_30d": 800,
            "posts_last_7d": 150,
            "posts_last_30d": 600,
            "comments_last_7d": 400,
            "comments_last_30d": 1800,
            "reactions_last_7d": 1000,
            "reactions_last_30d": 4000,
            "new_members_7d": 25,
            "new_members_30d": 100,
            "churned_members_7d": 1,
            "churned_members_30d": 4,
            "moderation_actions_7d": 0,
            "moderation_actions_30d": 2,
            "reported_content_7d": 0,
            "reported_content_30d": 1,
            "avg_response_time_hours": 2.0,
            "days_since_last_admin_post": 0,
        }
        poor_result = scorer.calculate_health_score(poor)
        good_result = scorer.calculate_health_score(good)
        assert good_result.score > poor_result.score

    def test_result_contains_component_scores(self, scorer, sample_metrics):
        """Result should include individual component scores."""
        result = scorer.calculate_health_score(sample_metrics)
        assert hasattr(result, "engagement_score")
        assert hasattr(result, "growth_score")
        assert hasattr(result, "moderation_score")
        assert hasattr(result, "activity_score")

    def test_result_contains_overall_grade(self, scorer, sample_metrics):
        """Result should include an overall letter grade."""
        result = scorer.calculate_health_score(sample_metrics)
        assert hasattr(result, "grade")
        assert result.grade in ("A", "B", "C", "D", "F")

    def test_grade_a_for_excellent_metrics(self, scorer, healthy_metrics):
        """Excellent metrics should yield grade A."""
        result = scorer.calculate_health_score(healthy_metrics)
        assert result.grade == "A"

    def test_grade_f_for_poor_metrics(self, scorer, unhealthy_metrics):
        """Poor metrics should yield grade F."""
        result = scorer.calculate_health_score(unhealthy_metrics)
        assert result.grade == "F"

    def test_missing_key_raises_key_error(self, scorer):
        """Missing required metric should raise KeyError."""
        incomplete = {"total_members": 100}
        with pytest.raises(KeyError):
            scorer.calculate_health_score(incomplete)

    def test_negative_values_handled(self, scorer):
        """Negative metric values should not crash the scorer."""
        metrics = {
            "total_members": 100,
            "active_members_7d": -5,
            "active_members_30d": 10,
            "posts_last_7d": 1,
            "posts_last_30d": 5,
            "comments_last_7d": 2,
            "comments_last_30d": 10,
            "reactions_last_7d": 5,
            "reactions_last_30d": 20,
            "new_members_7d": 0,
            "new_members_30d": 0,
            "churned_members_7d": 5,
            "churned_members_30d": 15,
            "moderation_actions_7d": 8,
            "moderation_actions_30d": 30,
            "reported_content_7d": 10,
            "reported_content_30d": 40,
            "avg_response_time_hours": 48.0,
            "days_since_last_admin_post": 20,
        }
        result = scorer.calculate_health_score(metrics)
        assert 0 <= result.score <= 100


# ---------------------------------------------------------------------------
# Tests: identify_risks
# ---------------------------------------------------------------------------


class TestIdentifyRisks:
    """Tests for CommunityHealthScorer.identify_risks."""

    def test_returns_list_of_risk_items(self, scorer, sample_metrics):
        """Should return a list of RiskItem instances."""
        risks = scorer.identify_risks(sample_metrics)
        assert isinstance(risks, list)
        for risk in risks:
            assert isinstance(risk, RiskItem)

    def test_healthy_community_has_few_or_no_risks(self, scorer, healthy_metrics):
        """A healthy community should have zero or very few risks."""
        risks = scorer.identify_risks(healthy_metrics)
        assert len(risks) <= 2

    def test_unhealthy_community_has_multiple_risks(self, scorer, unhealthy_metrics):
        """An unhealthy community should have several risks."""
        risks = scorer.identify_risks(unhealthy_metrics)
        assert len(risks) >= 3

    def test_risk_item_has_required_fields(self, scorer, unhealthy_metrics):
        """Each RiskItem should have category, severity, and description."""
        risks = scorer.identify_risks(unhealthy_metrics)
        for risk in risks:
            assert hasattr(risk, "category")
            assert hasattr(risk, "severity")
            assert hasattr(risk, "description")
            assert risk.severity in ("low", "medium", "high", "critical")

    def test_low_active_membership_flagged(self, scorer):
        """Low active-member ratio should be flagged as a risk."""
        metrics = {
            "total_members": 1000,
            "active_members_7d": 20,
            "active_members_30d": 50,
            "posts_last_7d": 5,
            "posts_last_30d": 20,
            "comments_last_7d": 10,
            "comments_last_30d": 40,
            "reactions_last_7d": 20,
            "reactions_last_30d": 80,
            "new_members_7d": 1,
            "new_members_30d": 5,
            "churned_members_7d": 10,
            "churned_members_30d": 30,
            "moderation_actions_7d": 5,
            "moderation_actions_30d": 20,
            "reported_content_7d": 8,
            "reported_content_30d": 30,
            "avg_response_time_hours": 36.0,
            "days_since_last_admin_post": 14,
        }
        risks = scorer.identify_risks(metrics)
        categories = [r.category for r in risks]
        assert "engagement" in categories or "activity" in categories

    def test_high_churn_flagged(self, scorer):
        """High churn rate should be flagged."""
        metrics = {
            "total_members": 500,
            "active_members_7d": 200,
            "active_members_30d": 350,
            "posts_last_7d": 100,
            "posts_last_30d": 400,
            "comments_last_7d": 250,
            "comments_last_30d": 1000,
            "reactions_last_7d": 500,
            "reactions_last_30d": 2000,
            "new_members_7d": 5,
            "new_members_30d": 20,
            "churned_members_7d": 50,
            "churned_members_30d": 150,
            "moderation_actions_7d": 2,
            "moderation_actions_30d": 8,
            "reported_content_7d": 1,
            "reported_content_30d": 4,
            "avg_response_time_hours": 3.0,
            "days_since_last_admin_post": 1,
        }
        risks = scorer.identify_risks(metrics)
        categories = [r.category for r in risks]
        assert "churn" in categories or "retention" in categories

    def test_high_moderation_load_flagged(self, scorer):
        """Excessive moderation actions should be flagged."""
        metrics = {
            "total_members": 500,
            "active_members_7d": 200,
            "active_members_30d": 350,
            "posts_last_7d": 100,
            "posts_last_30d": 400,
            "comments_last_7d": 250,
            "comments_last_30d": 1000,
            "reactions_last_7d": 500,
            "reactions_last_30d": 2000,
            "new_members_7d": 10,
            "new_members_30d": 40,
            "churned_members_7d": 3,
            "churned_members_30d": 10,
            "moderation_actions_7d": 50,
            "moderation_actions_30d": 200,
            "reported_content_7d": 30,
            "reported_content_30d": 120,
            "avg_response_time_hours": 2.0,
            "days_since_last_admin_post": 0,
        }
        risks = scorer.identify_risks(metrics)
        categories = [r.category for r in risks]
        assert "moderation" in categories or "safety" in categories

    def test_stale_admin_presence_flagged(self, scorer):
        """Long gap since last admin post should be flagged."""
        metrics = {
            "total_members": 500,
            "active_members_7d": 200,
            "active_members_30d": 350,
            "posts_last_7d": 100,
            "posts_last_30d": 400,
            "comments_last_7d": 250,
            "comments_last_30d": 1000,
            "reactions_last_7d": 500,
            "reactions_last_30d": 2000,
            "new_members_7d": 10,
            "new_members_30d": 40,
            "churned_members_7d": 3,
            "churned_members_30d": 10,
            "moderation_actions_7d": 2,
            "moderation_actions_30d": 8,
            "reported_content_7d": 1,
            "reported_content_30d": 4,
            "avg_response_time_hours": 2.0,
            "days_since_last_admin_post": 45,
        }
        risks = scorer.identify_risks(metrics)
        categories = [r.category for r in risks]
        assert "leadership" in categories or "admin" in categories

    def test_empty_metrics_returns_empty_list(self, scorer, empty_metrics):
        """All-zero metrics should return an empty risk list."""
        risks = scorer.identify_risks(empty_metrics)
        assert risks == []

    def test_risks_sorted_by_severity(self, scorer, unhealthy_metrics):
        """Risks should be sorted by severity (most severe first)."""
        risks = scorer.identify_risks(unhealthy_metrics)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        severities = [severity_order.get(r.severity, 4) for r in risks]
        assert severities == sorted(severities)


# ---------------------------------------------------------------------------
# Tests: health_breakdown
# ---------------------------------------------------------------------------


class TestHealthBreakdown:
    """Tests for CommunityHealthScorer.health_breakdown."""

    def test_returns_dict(self, scorer, sample_metrics):
        """Should return a dictionary."""
        breakdown = scorer.health_breakdown(sample_metrics)
        assert isinstance(breakdown, dict)

    def test_contains_engagement_key(self, scorer, sample_metrics):
        """Breakdown should contain an 'engagement' key."""
        breakdown = scorer.health_breakdown(sample_metrics)
        assert "engagement" in breakdown

    def test_contains_growth_key(self, scorer, sample_metrics):
        """Breakdown should contain a 'growth' key."""
        breakdown = scorer.health_breakdown(sample_metrics)
        assert "growth" in breakdown

    def test_contains_moderation_key(self, scorer, sample_metrics):
        """Breakdown should contain a 'moderation' key."""
        breakdown = scorer.health_breakdown(sample_metrics)
        assert "moderation" in breakdown

    def test_contains_activity_key(self, scorer, sample_metrics):
        """Breakdown should contain an 'activity' key."""
        breakdown = scorer.health_breakdown(sample_metrics)
        assert "activity" in breakdown

    def test_each_component_has_score_and_weight(self, scorer, sample_metrics):
        """Each component should have a numeric score and weight."""
        breakdown = scorer.health_breakdown(sample_metrics)
        for key, value in breakdown.items():
            assert "score" in value, f"Component '{key}' missing 'score'"
            assert "weight" in value, f"Component '{key}' missing 'weight'"
            assert isinstance(value["score"], (int, float))
            assert isinstance(value["weight"], (int, float))

    def test_weights_sum_to_one(self, scorer, sample_metrics):
        """Component weights should sum to approximately 1.0."""
        breakdown = scorer.health_breakdown(sample_metrics)
        total_weight = sum(v["weight"] for v in breakdown.values())
        assert abs(total_weight - 1.0) < 0.01

    def test_healthy_community_high_component_scores(self, scorer, healthy_metrics):
        """Healthy community should have high component scores."""
        breakdown = scorer.health_breakdown(healthy_metrics)
        for key, value in breakdown.items():
            assert value["score"] > 60, (
                f"Component '{key}' score {value['score']} too low for healthy community"
            )

    def test_unhealthy_community_low_component_scores(self, scorer, unhealthy_metrics):
        """Unhealthy community should have low component scores."""
        breakdown = scorer.health_breakdown(unhealthy_metrics)
        for key, value in breakdown.items():
            assert value["score"] < 50, (
                f"Component '{key}' score {value['score']} too high for unhealthy community"
            )

    def test_empty_metrics_zero_component_scores(self, scorer, empty_metrics):
        """All-zero metrics should yield zero component scores."""
        breakdown = scorer.health_breakdown(empty_metrics)
        for key, value in breakdown.items():
            assert value["score"] == 0, (
                f"Component '{key}' should be 0 for empty metrics, got {value['score']}"
            )

    def test_breakdown_includes_recommendations(self, scorer, sample_metrics):
        """Breakdown should include actionable recommendations."""
        breakdown = scorer.health_breakdown(sample_metrics)
        assert "recommendations" in breakdown or any(
            "recommendations" in v for v in breakdown.values()
        )

    def test_component_scores_within_valid_range(self, scorer, sample_metrics):
        """All component scores should be between 0 and 100."""
        breakdown = scorer.health_breakdown(sample_metrics)
        for key, value in breakdown.items():
            assert 0 <= value["score"] <= 100, (
                f"Component '{key}' score {value['score']} out of range [0, 100]"
            )

    def test_consistent_with_calculate_health_score(self, scorer, sample_metrics):
        """Breakdown component scores should be consistent with overall score."""
        result = scorer.calculate_health_score(sample_metrics)
        breakdown = scorer.health_breakdown(sample_metrics)
        weighted_sum = sum(
            v["score"] * v["weight"] for v in breakdown.values()
        )
        # Allow tolerance for rounding
        assert abs(weighted_sum - result.score) < 5
