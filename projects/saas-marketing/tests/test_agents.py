"""Tests for marketing agents."""

from __future__ import annotations

import pytest

from saas_marketing.agents.analytics import AnalyticsAgent, AnalyticsQuery, FunnelStage
from saas_marketing.agents.churn_prevention import AccountHealth, ChurnPreventionAgent, ChurnRiskLevel
from saas_marketing.agents.content import ContentAgent, ContentRequest
from saas_marketing.agents.pql_scoring import PQLScoringAgent, PQLTier, UserBehavior
from saas_marketing.agents.reporting import ReportFormat, ReportRequest, ReportType, ReportingAgent


class TestContentAgent:
    """Tests for the ContentAgent."""

    @pytest.fixture
    def agent(self) -> ContentAgent:
        """Create a ContentAgent instance."""
        return ContentAgent()

    @pytest.fixture
    def email_request(self) -> ContentRequest:
        """Create a sample content request."""
        return ContentRequest(
            content_type="email",
            topic="Product Analytics",
            tone="professional",
            target_audience="SaaS product managers",
            call_to_action="Start your free trial",
        )

    @pytest.mark.asyncio
    async def test_generate_email(self, agent: ContentAgent, email_request: ContentRequest) -> None:
        """Test email content generation."""
        result = await agent.generate(email_request)
        assert result.content_type == "email"
        assert result.word_count > 0
        assert "Product Analytics" in result.content
        assert result.metadata["tone"] == "professional"

    @pytest.mark.asyncio
    async def test_generate_social(self, agent: ContentAgent) -> None:
        """Test social media content generation."""
        request = ContentRequest(
            content_type="social",
            topic="AI Marketing",
            tone="casual",
            target_audience="marketers",
        )
        result = await agent.generate(request)
        assert result.content_type == "social"
        assert result.word_count > 0

    @pytest.mark.asyncio
    async def test_invalid_content_type(self, agent: ContentAgent) -> None:
        """Test that invalid content type raises ValueError."""
        request = ContentRequest(
            content_type="invalid",
            topic="Test",
            target_audience="test",
        )
        with pytest.raises(ValueError, match="Unsupported content_type"):
            await agent.generate(request)

    @pytest.mark.asyncio
    async def test_invalid_tone(self, agent: ContentAgent) -> None:
        """Test that invalid tone raises ValueError."""
        request = ContentRequest(
            content_type="email",
            topic="Test",
            tone="invalid_tone",
            target_audience="test",
        )
        with pytest.raises(ValueError, match="Unsupported tone"):
            await agent.generate(request)


class TestPQLScoringAgent:
    """Tests for the PQLScoringAgent."""

    @pytest.fixture
    def agent(self) -> PQLScoringAgent:
        """Create a PQLScoringAgent instance."""
        return PQLScoringAgent()

    @pytest.fixture
    def high_intent_user(self) -> UserBehavior:
        """Create a high-intent user behavior."""
        return UserBehavior(
            user_id="user_123",
            feature_usage_count=8,
            total_sessions=25,
            avg_session_duration_seconds=300,
            days_since_signup=14,
            key_actions_completed=["signup", "invite_team", "create_project", "connect_integration"],
            team_size=5,
            billing_page_visits=3,
            integration_attempts=2,
            nps_score=9,
        )

    @pytest.fixture
    def low_intent_user(self) -> UserBehavior:
        """Create a low-intent user behavior."""
        return UserBehavior(
            user_id="user_456",
            feature_usage_count=1,
            total_sessions=2,
            avg_session_duration_seconds=30,
            days_since_signup=1,
            key_actions_completed=["signup"],
            team_size=1,
            billing_page_visits=0,
            integration_attempts=0,
        )

    @pytest.mark.asyncio
    async def test_score_high_intent(self, agent: PQLScoringAgent, high_intent_user: UserBehavior) -> None:
        """Test scoring a high-intent user."""
        result = await agent.score(high_intent_user)
        assert result.score >= 70
        assert result.tier in (PQLTier.HOT, PQLTier.SQL)
        assert result.confidence > 0.5
        assert len(result.signals) == 4

    @pytest.mark.asyncio
    async def test_score_low_intent(self, agent: PQLScoringAgent, low_intent_user: UserBehavior) -> None:
        """Test scoring a low-intent user."""
        result = await agent.score(low_intent_user)
        assert result.score < 40
        assert result.tier == PQLTier.COLD

    @pytest.mark.asyncio
    async def test_score_bounds(self, agent: PQLScoringAgent, high_intent_user: UserBehavior) -> None:
        """Test that score is within bounds."""
        result = await agent.score(high_intent_user)
        assert 0 <= result.score <= 100

    def test_invalid_weights(self) -> None:
        """Test that invalid weights raise ValueError."""
        with pytest.raises(ValueError, match="weights must sum to 1.0"):
            PQLScoringAgent(weights={"feature_usage": 0.5, "engagement": 0.2})


class TestChurnPreventionAgent:
    """Tests for the ChurnPreventionAgent."""

    @pytest.fixture
    def agent(self) -> ChurnPreventionAgent:
        """Create a ChurnPreventionAgent instance."""
        return ChurnPreventionAgent()

    @pytest.fixture
    def healthy_account(self) -> AccountHealth:
        """Create a healthy account."""
        return AccountHealth(
            account_id="acc_123",
            mrr=5000,
            active_users=8,
            total_seats=10,
            days_since_last_login=1,
            support_tickets_30d=0,
            nps_score=9,
            feature_adoption_rate=0.8,
            contract_end_days=365,
            payment_failures=0,
            engagement_trend="up",
        )

    @pytest.fixture
    def at_risk_account(self) -> AccountHealth:
        """Create an at-risk account."""
        return AccountHealth(
            account_id="acc_456",
            mrr=2000,
            active_users=2,
            total_seats=10,
            days_since_last_login=21,
            support_tickets_30d=8,
            nps_score=3,
            feature_adoption_rate=0.15,
            contract_end_days=14,
            payment_failures=2,
            engagement_trend="down",
        )

    @pytest.mark.asyncio
    async def test_healthy_account(self, agent: ChurnPreventionAgent, healthy_account: AccountHealth) -> None:
        """Test assessment of a healthy account."""
        result = await agent.assess(healthy_account)
        assert result.risk_level == ChurnRiskLevel.LOW
        assert result.risk_score < 0.3
        assert len(result.contributing_factors) == 0

    @pytest.mark.asyncio
    async def test_at_risk_account(self, agent: ChurnPreventionAgent, at_risk_account: AccountHealth) -> None:
        """Test assessment of an at-risk account."""
        result = await agent.assess(at_risk_account)
        assert result.risk_level in (ChurnRiskLevel.HIGH, ChurnRiskLevel.CRITICAL)
        assert result.risk_score > 0.6
        assert len(result.contributing_factors) > 0
        assert len(result.recommended_actions) > 0

    @pytest.mark.asyncio
    async def test_risk_score_bounds(self, agent: ChurnPreventionAgent, at_risk_account: AccountHealth) -> None:
        """Test that risk score is within bounds."""
        result = await agent.assess(at_risk_account)
        assert 0 <= result.risk_score <= 1


class TestAnalyticsAgent:
    """Tests for the AnalyticsAgent."""

    @pytest.fixture
    def agent(self) -> AnalyticsAgent:
        """Create an AnalyticsAgent instance."""
        return AnalyticsAgent()

    @pytest.fixture
    def query(self) -> AnalyticsQuery:
        """Create a sample analytics query."""
        from datetime import datetime, timedelta

        end = datetime.utcnow()
        start = end - timedelta(days=30)
        return AnalyticsQuery(
            start_date=start,
            end_date=end,
            granularity="day",
        )

    @pytest.mark.asyncio
    async def test_analyze(self, agent: AnalyticsAgent, query: AnalyticsQuery) -> None:
        """Test analytics analysis."""
        result = await agent.analyze(query)
        assert len(result.funnel) == len(FunnelStage)
        assert len(result.cohorts) > 0
        assert "total_visitors" in result.summary
        assert "overall_conversion_rate" in result.summary

    @pytest.mark.asyncio
    async def test_invalid_date_range(self, agent: AnalyticsAgent) -> None:
        """Test that invalid date range raises ValueError."""
        from datetime import datetime

        query = AnalyticsQuery(
            start_date=datetime(2024, 1, 31),
            end_date=datetime(2024, 1, 1),
            granularity="day",
        )
        with pytest.raises(ValueError, match="end_date must be after start_date"):
            await agent.analyze(query)

    @pytest.mark.asyncio
    async def test_invalid_granularity(self, agent: AnalyticsAgent) -> None:
        """Test that invalid granularity raises ValueError."""
        from datetime import datetime, timedelta

        query = AnalyticsQuery(
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow(),
            granularity="invalid",
        )
        with pytest.raises(ValueError, match="Invalid granularity"):
            await agent.analyze(query)


class TestReportingAgent:
    """Tests for the ReportingAgent."""

    @pytest.fixture
    def agent(self) -> ReportingAgent:
        """Create a ReportingAgent instance."""
        return ReportingAgent()

    @pytest.fixture
    def report_request(self) -> ReportRequest:
        """Create a sample report request."""
        from datetime import datetime, timedelta

        end = datetime.utcnow()
        start = end - timedelta(days=30)
        return ReportRequest(
            report_type=ReportType.EXECUTIVE_SUMMARY,
            format=ReportFormat.MARKDOWN,
            title="Monthly Executive Summary",
            date_range_start=start,
            date_range_end=end,
        )

    @pytest.mark.asyncio
    async def test_generate_executive_summary(self, agent: ReportingAgent, report_request: ReportRequest) -> None:
        """Test executive summary report generation."""
        result = await agent.generate(report_request)
        assert result.id.startswith("report_executive_summary")
        assert len(result.sections) > 0
        assert result.summary != ""
        assert result.generated_at is not None

    @pytest.mark.asyncio
    async def test_generate_funnel_report(self, agent: ReportingAgent) -> None:
        """Test funnel analysis report generation."""
        from datetime import datetime, timedelta

        request = ReportRequest(
            report_type=ReportType.FUNNEL_ANALYSIS,
            format=ReportFormat.MARKDOWN,
            title="Funnel Analysis",
            date_range_start=datetime.utcnow() - timedelta(days=30),
            date_range_end=datetime.utcnow(),
        )
        result = await agent.generate(request)
        assert len(result.sections) > 0

    @pytest.mark.asyncio
    async def test_invalid_date_range(self, agent: ReportingAgent) -> None:
        """Test that invalid date range raises ValueError."""
        from datetime import datetime

        request = ReportRequest(
            report_type=ReportType.EXECUTIVE_SUMMARY,
            title="Test",
            date_range_start=datetime(2024, 1, 31),
            date_range_end=datetime(2024, 1, 1),
        )
        with pytest.raises(ValueError, match="date_range_end must be after date_range_start"):
            await agent.generate(request)
