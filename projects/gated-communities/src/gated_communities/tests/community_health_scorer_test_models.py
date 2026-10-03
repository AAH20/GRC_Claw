"""Tests for community health scorer models."""

from __future__ import annotations

import pytest
from community_health_scorer.models import (AgentRunRequest, AgentRunResponse,
                                            ChurnPrediction, ChurnRisk,
                                            EngagementLevel, EngagementMetrics,
                                            ErrorResponse, GrowthAnalysis,
                                            GrowthTrend, HealthCategory,
                                            HealthExplanation, HealthResponse,
                                            HealthScore, ReadinessResponse,
                                            ScoreRequest, ToxicityLevel,
                                            ToxicityReport)


class TestEngagementMetrics:
    """Tests for EngagementMetrics model."""

    def test_valid_engagement_metrics(self) -> None:
        """Test creating valid engagement metrics."""
        metrics = EngagementMetrics(
            dau=100,
            mau=500,
            avg_session_duration_minutes=15.5,
            avg_sessions_per_user=3.0,
            interaction_depth=0.7,
            content_creation_rate=0.5,
            response_rate=0.8,
            retention_rate_7d=0.6,
            retention_rate_30d=0.4,
        )
        assert metrics.dau == 100
        assert metrics.mau == 500
        assert metrics.dau_mau_ratio == 0.2

    def test_mau_must_be_gte_dau(self) -> None:
        """Test that MAU must be >= DAU."""
        with pytest.raises(ValueError, match="MAU must be >= DAU"):
            EngagementMetrics(
                dau=500,
                mau=100,
                avg_session_duration_minutes=10.0,
                avg_sessions_per_user=2.0,
                interaction_depth=0.5,
                content_creation_rate=0.3,
                response_rate=0.6,
                retention_rate_7d=0.5,
                retention_rate_30d=0.3,
            )

    def test_dau_mau_ratio_zero_when_mau_zero(self) -> None:
        """Test DAU/MAU ratio is 0 when MAU is 0."""
        metrics = EngagementMetrics(
            dau=0,
            mau=0,
            avg_session_duration_minutes=0.0,
            avg_sessions_per_user=0.0,
            interaction_depth=0.0,
            content_creation_rate=0.0,
            response_rate=0.0,
            retention_rate_7d=0.0,
            retention_rate_30d=0.0,
        )
        assert metrics.dau_mau_ratio == 0.0

    def test_default_engagement_level(self) -> None:
        """Test default engagement level."""
        metrics = EngagementMetrics(
            dau=100,
            mau=500,
            avg_session_duration_minutes=10.0,
            avg_sessions_per_user=2.0,
            interaction_depth=0.5,
            content_creation_rate=0.3,
            response_rate=0.6,
            retention_rate_7d=0.5,
            retention_rate_30d=0.3,
        )
        assert metrics.engagement_level == EngagementLevel.MODERATELY_ENGAGED

    def test_default_score(self) -> None:
        """Test default score is 0."""
        metrics = EngagementMetrics(
            dau=100,
            mau=500,
            avg_session_duration_minutes=10.0,
            avg_sessions_per_user=2.0,
            interaction_depth=0.5,
            content_creation_rate=0.3,
            response_rate=0.6,
            retention_rate_7d=0.5,
            retention_rate_30d=0.3,
        )
        assert metrics.score == 0.0


class TestToxicityReport:
    """Tests for ToxicityReport model."""

    def test_valid_toxicity_report(self) -> None:
        """Test creating valid toxicity report."""
        report = ToxicityReport(
            overall_toxicity_score=25.0,
            toxicity_level=ToxicityLevel.LOW,
            toxic_content_count=10,
            total_content_analyzed=1000,
            toxic_user_count=5,
            total_users=500,
        )
        assert report.overall_toxicity_score == 25.0
        assert report.toxicity_level == ToxicityLevel.LOW
        assert report.toxicity_rate == 1.0

    def test_toxicity_rate_zero_when_no_content(self) -> None:
        """Test toxicity rate is 0 when no content analyzed."""
        report = ToxicityReport(
            overall_toxicity_score=0.0,
            total_content_analyzed=0,
        )
        assert report.toxicity_rate == 0.0

    def test_default_toxicity_level(self) -> None:
        """Test default toxicity level."""
        report = ToxicityReport(overall_toxicity_score=0.0)
        assert report.toxicity_level == ToxicityLevel.NONE


class TestGrowthAnalysis:
    """Tests for GrowthAnalysis model."""

    def test_valid_growth_analysis(self) -> None:
        """Test creating valid growth analysis."""
        analysis = GrowthAnalysis(
            current_members=1000,
            new_members_7d=50,
            new_members_30d=200,
            churned_members_7d=10,
            churned_members_30d=30,
            growth_rate_7d=0.05,
            growth_rate_30d=0.20,
            net_growth_rate=0.17,
        )
        assert analysis.current_members == 1000
        assert analysis.growth_trend == GrowthTrend.STABLE

    def test_default_growth_trend(self) -> None:
        """Test default growth trend."""
        analysis = GrowthAnalysis(current_members=100)
        assert analysis.growth_trend == GrowthTrend.STABLE


class TestChurnPrediction:
    """Tests for ChurnPrediction model."""

    def test_valid_churn_prediction(self) -> None:
        """Test creating valid churn prediction."""
        prediction = ChurnPrediction(
            overall_churn_risk=ChurnRisk.LOW,
            churn_probability=0.15,
            at_risk_members=50,
            total_members=1000,
        )
        assert prediction.overall_churn_risk == ChurnRisk.LOW
        assert prediction.at_risk_percentage == 5.0

    def test_at_risk_percentage_zero_when_no_members(self) -> None:
        """Test at-risk percentage is 0 when no members."""
        prediction = ChurnPrediction(
            churn_probability=0.0,
            total_members=0,
        )
        assert prediction.at_risk_percentage == 0.0

    def test_default_churn_risk(self) -> None:
        """Test default churn risk."""
        prediction = ChurnPrediction(churn_probability=0.0)
        assert prediction.overall_churn_risk == ChurnRisk.LOW


class TestHealthScore:
    """Tests for HealthScore model."""

    def test_valid_health_score(self) -> None:
        """Test creating valid health score."""
        score = HealthScore(
            community_id="test-community",
            overall_score=75.0,
            category=HealthCategory.GOOD,
            engagement_score=80.0,
            toxicity_score=70.0,
            growth_score=75.0,
            churn_score=72.0,
        )
        assert score.community_id == "test-community"
        assert score.overall_score == 75.0
        assert score.category == HealthCategory.GOOD

    def test_auto_derive_category_excellent(self) -> None:
        """Test auto-deriving category for excellent score."""
        score = HealthScore(
            community_id="test",
            overall_score=85.0,
            engagement_score=85.0,
            toxicity_score=85.0,
            growth_score=85.0,
            churn_score=85.0,
        )
        assert score.category == HealthCategory.EXCELLENT

    def test_auto_derive_category_good(self) -> None:
        """Test auto-deriving category for good score."""
        score = HealthScore(
            community_id="test",
            overall_score=65.0,
            engagement_score=65.0,
            toxicity_score=65.0,
            growth_score=65.0,
            churn_score=65.0,
        )
        assert score.category == HealthCategory.GOOD

    def test_auto_derive_category_fair(self) -> None:
        """Test auto-deriving category for fair score."""
        score = HealthScore(
            community_id="test",
            overall_score=45.0,
            engagement_score=45.0,
            toxicity_score=45.0,
            growth_score=45.0,
            churn_score=45.0,
        )
        assert score.category == HealthCategory.FAIR

    def test_auto_derive_category_poor(self) -> None:
        """Test auto-deriving category for poor score."""
        score = HealthScore(
            community_id="test",
            overall_score=25.0,
            engagement_score=25.0,
            toxicity_score=25.0,
            growth_score=25.0,
            churn_score=25.0,
        )
        assert score.category == HealthCategory.POOR

    def test_auto_derive_category_critical(self) -> None:
        """Test auto-deriving category for critical score."""
        score = HealthScore(
            community_id="test",
            overall_score=10.0,
            engagement_score=10.0,
            toxicity_score=10.0,
            growth_score=10.0,
            churn_score=10.0,
        )
        assert score.category == HealthCategory.CRITICAL

    def test_default_weights(self) -> None:
        """Test default weights."""
        score = HealthScore(
            community_id="test",
            overall_score=50.0,
            engagement_score=50.0,
            toxicity_score=50.0,
            growth_score=50.0,
            churn_score=50.0,
        )
        assert score.engagement_weight == 0.30
        assert score.toxicity_weight == 0.25
        assert score.growth_weight == 0.25
        assert score.churn_weight == 0.20


class TestHealthExplanation:
    """Tests for HealthExplanation model."""

    def test_valid_health_explanation(self) -> None:
        """Test creating valid health explanation."""
        explanation = HealthExplanation(
            community_id="test-community",
            summary="Community is healthy",
            engagement_summary="Good engagement",
            toxicity_summary="Low toxicity",
            growth_summary="Steady growth",
            churn_summary="Low churn risk",
        )
        assert explanation.community_id == "test-community"
        assert explanation.model_used == "gpt-4o-mini"


class TestScoreRequest:
    """Tests for ScoreRequest model."""

    def test_valid_score_request(self) -> None:
        """Test creating valid score request."""
        request = ScoreRequest(community_id="test-community")
        assert request.community_id == "test-community"
        assert request.period_days == 30
        assert request.include_explanation is True

    def test_community_id_required(self) -> None:
        """Test that community_id is required."""
        with pytest.raises(ValueError):
            ScoreRequest(community_id="")

    def test_period_days_validation(self) -> None:
        """Test period_days validation."""
        with pytest.raises(ValueError):
            ScoreRequest(community_id="test", period_days=0)
        with pytest.raises(ValueError):
            ScoreRequest(community_id="test", period_days=366)


class TestAgentRunRequest:
    """Tests for AgentRunRequest model."""

    def test_valid_agent_run_request(self) -> None:
        """Test creating valid agent run request."""
        request = AgentRunRequest(community_id="test-community")
        assert request.community_id == "test-community"
        assert request.parameters == {}


class TestAgentRunResponse:
    """Tests for AgentRunResponse model."""

    def test_valid_agent_run_response(self) -> None:
        """Test creating valid agent run response."""
        response = AgentRunResponse(
            agent_name="test_agent",
            community_id="test-community",
            status="success",
            execution_time_ms=100.0,
        )
        assert response.agent_name == "test_agent"
        assert response.status == "success"
        assert response.error is None


class TestHealthResponse:
    """Tests for HealthResponse model."""

    def test_valid_health_response(self) -> None:
        """Test creating valid health response."""
        response = HealthResponse()
        assert response.status == "healthy"
        assert response.version == "0.1.0"


class TestReadinessResponse:
    """Tests for ReadinessResponse model."""

    def test_valid_readiness_response(self) -> None:
        """Test creating valid readiness response."""
        response = ReadinessResponse(ready=True)
        assert response.ready is True
        assert response.checks == {}


class TestErrorResponse:
    """Tests for ErrorResponse model."""

    def test_valid_error_response(self) -> None:
        """Test creating valid error response."""
        response = ErrorResponse(error="not_found", message="Resource not found")
        assert response.error == "not_found"
        assert response.message == "Resource not found"
        assert response.details is None
