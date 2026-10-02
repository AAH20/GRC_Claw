"""Tests for Pydantic models."""

from datetime import datetime

from creator_analytics.models import (
    AgeGroup,
    Audience,
    AudienceDemographics,
    AudienceSegment,
    ContentMetrics,
    ContentPerformance,
    ContentType,
    EngagementMetrics,
    EngagementReport,
    EngagementType,
    Gender,
    GrowthPrediction,
    GrowthScenario,
    RevenueBreakdown,
    RevenueReport,
    RevenueStream,
)


def test_audience_demographics() -> None:
    """Test AudienceDemographics model."""
    demo = AudienceDemographics(
        age_distribution={AgeGroup.AGE_18_24: 0.35, AgeGroup.AGE_25_34: 0.40},
        gender_distribution={Gender.MALE: 0.55, Gender.FEMALE: 0.45},
        top_countries={"US": 0.40},
        interests=["gaming", "technology"],
    )
    assert demo.age_distribution[AgeGroup.AGE_18_24] == 0.35
    assert demo.interests == ["gaming", "technology"]


def test_audience_segment() -> None:
    """Test AudienceSegment model."""
    demo = AudienceDemographics()
    segment = AudienceSegment(
        segment_id="seg-1",
        name="Active Gamers",
        size=5000,
        engagement_rate=0.15,
        demographics=demo,
        characteristics=["high engagement", "regular interaction"],
    )
    assert segment.segment_id == "seg-1"
    assert segment.engagement_rate == 0.15


def test_audience() -> None:
    """Test Audience model."""
    demo = AudienceDemographics()
    audience = Audience(
        creator_id="creator-123",
        total_followers=50000,
        active_followers=35000,
        demographics=demo,
        growth_rate=0.05,
        churn_rate=0.02,
    )
    assert audience.creator_id == "creator-123"
    assert audience.total_followers == 50000


def test_content_metrics() -> None:
    """Test ContentMetrics model."""
    metrics = ContentMetrics(
        views=10000,
        likes=500,
        comments=100,
        shares=50,
        saves=30,
        engagement_rate=0.068,
        sentiment_score=0.75,
    )
    assert metrics.views == 10000
    assert metrics.engagement_rate == 0.068


def test_content_performance() -> None:
    """Test ContentPerformance model."""
    metrics = ContentMetrics(views=10000, likes=500)
    perf = ContentPerformance(
        content_id="content-1",
        creator_id="creator-123",
        content_type=ContentType.VIDEO,
        title="Test Video",
        published_at=datetime.utcnow(),
        metrics=metrics,
        performance_score=75.0,
    )
    assert perf.content_id == "content-1"
    assert perf.performance_score == 75.0


def test_revenue_breakdown() -> None:
    """Test RevenueBreakdown model."""
    breakdown = RevenueBreakdown(
        stream=RevenueStream.ADVERTISING,
        amount=5000.0,
        percentage_of_total=50.0,
        growth_rate=0.03,
        transactions=100,
        average_transaction_value=50.0,
    )
    assert breakdown.stream == RevenueStream.ADVERTISING
    assert breakdown.amount == 5000.0


def test_revenue_report() -> None:
    """Test RevenueReport model."""
    report = RevenueReport(
        creator_id="creator-123",
        report_period_start=datetime.utcnow(),
        report_period_end=datetime.utcnow(),
        total_revenue=10000.0,
        recurring_revenue=5000.0,
        one_time_revenue=5000.0,
    )
    assert report.total_revenue == 10000.0


def test_growth_prediction() -> None:
    """Test GrowthPrediction model."""
    prediction = GrowthPrediction(
        creator_id="creator-123",
        prediction_period_months=12,
        current_followers=50000,
        predicted_followers={
            GrowthScenario.CONSERVATIVE: 55000,
            GrowthScenario.MODERATE: 60000,
            GrowthScenario.AGGRESSIVE: 70000,
        },
        current_monthly_revenue=10000.0,
        predicted_monthly_revenue={
            GrowthScenario.CONSERVATIVE: 11000.0,
            GrowthScenario.MODERATE: 12000.0,
            GrowthScenario.AGGRESSIVE: 15000.0,
        },
        growth_rate_predictions={
            GrowthScenario.CONSERVATIVE: 0.02,
            GrowthScenario.MODERATE: 0.05,
            GrowthScenario.AGGRESSIVE: 0.10,
        },
        confidence_score=0.85,
    )
    assert prediction.confidence_score == 0.85
    assert prediction.predicted_followers[GrowthScenario.MODERATE] == 60000


def test_engagement_metrics() -> None:
    """Test EngagementMetrics model."""
    metrics = EngagementMetrics(
        total_interactions=50000,
        interactions_by_type={EngagementType.LIKE: 30000, EngagementType.COMMENT: 10000},
        engagement_rate=0.068,
        response_rate=0.8,
    )
    assert metrics.total_interactions == 50000
    assert metrics.engagement_rate == 0.068


def test_engagement_report() -> None:
    """Test EngagementReport model."""
    metrics = EngagementMetrics(total_interactions=50000)
    report = EngagementReport(
        creator_id="creator-123",
        report_period_start=datetime.utcnow(),
        report_period_end=datetime.utcnow(),
        metrics=metrics,
        audience_loyalty_score=75.0,
        community_health_score=80.0,
    )
    assert report.audience_loyalty_score == 75.0
    assert report.community_health_score == 80.0
