"""Tests for Creator Monetization agents."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from creator_monetization.agents.analytics import AnalyticsAgent, MetricPoint, ReportPeriod
from creator_monetization.agents.payout_manager import PayoutManagerAgent, PayoutSchedule
from creator_monetization.agents.revenue_optimizer import RevenueOptimizerAgent, RevenueStream
from creator_monetization.agents.subscription import SubscriptionAgent
from creator_monetization.agents.tier_recommender import CreatorProfile, TierRecommenderAgent
from creator_monetization.models.schemas import Payout, PayoutStatus, Subscription, SubscriptionStatus, TierLevel


class TestRevenueOptimizerAgent:
    """Tests for RevenueOptimizerAgent."""

    @pytest.fixture
    def agent(self) -> RevenueOptimizerAgent:
        return RevenueOptimizerAgent()

    @pytest.fixture
    def sample_streams(self) -> list[RevenueStream]:
        return [
            RevenueStream(
                stream_id="stream-1",
                name="Subscriptions",
                type="subscription",
                monthly_revenue=Decimal("5000.00"),
                growth_rate=0.12,
            ),
            RevenueStream(
                stream_id="stream-2",
                name="Tips",
                type="tips",
                monthly_revenue=Decimal("1000.00"),
                growth_rate=0.08,
            ),
        ]

    @pytest.mark.asyncio
    async def test_analyze_revenue_streams(
        self, agent: RevenueOptimizerAgent, sample_streams: list[RevenueStream]
    ) -> None:
        result = await agent.analyze_revenue_streams("creator-1", sample_streams)
        assert result is not None
        assert result["creator_id"] == "creator-1"
        assert result["total_monthly_revenue"] == Decimal("6000.00")
        assert result["active_stream_count"] == 2

    @pytest.mark.asyncio
    async def test_analyze_empty_streams(
        self, agent: RevenueOptimizerAgent
    ) -> None:
        with pytest.raises(ValueError, match="At least one revenue stream"):
            await agent.analyze_revenue_streams("creator-1", [])

    @pytest.mark.asyncio
    async def test_generate_optimization_plan(
        self, agent: RevenueOptimizerAgent, sample_streams: list[RevenueStream]
    ) -> None:
        await agent.analyze_revenue_streams("creator-1", sample_streams)
        suggestions = await agent.generate_optimization_plan("creator-1")
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

    @pytest.mark.asyncio
    async def test_forecast_revenue(
        self, agent: RevenueOptimizerAgent, sample_streams: list[RevenueStream]
    ) -> None:
        await agent.analyze_revenue_streams("creator-1", sample_streams)
        forecast = await agent.forecast_revenue("creator-1", months=6)
        assert isinstance(forecast, list)
        assert len(forecast) == 6

    def test_get_stream_count(
        self, agent: RevenueOptimizerAgent
    ) -> None:
        count = agent.get_stream_count("nonexistent")
        assert isinstance(count, int)
        assert count == 0


class TestPayoutManagerAgent:
    """Tests for PayoutManagerAgent."""

    @pytest.fixture
    def agent(self) -> PayoutManagerAgent:
        return PayoutManagerAgent()

    @pytest.fixture
    def sample_payout(self) -> Payout:
        return Payout(
            payout_id="payout-1",
            creator_id="creator-1",
            amount=Decimal("100.00"),
            period_start=datetime.now(UTC) - timedelta(days=30),
            period_end=datetime.now(UTC),
        )

    @pytest.mark.asyncio
    async def test_create_payout(
        self, agent: PayoutManagerAgent, sample_payout: Payout
    ) -> None:
        result = await agent.create_payout(sample_payout)
        assert result is not None
        assert result.payout_id == "payout-1"
        assert result.creator_id == "creator-1"

    @pytest.mark.asyncio
    async def test_create_payout_below_minimum(
        self, agent: PayoutManagerAgent
    ) -> None:
        payout = Payout(
            payout_id="payout-low",
            creator_id="creator-1",
            amount=Decimal("10.00"),
            period_start=datetime.now(UTC) - timedelta(days=30),
            period_end=datetime.now(UTC),
        )
        with pytest.raises(ValueError, match="below minimum"):
            await agent.create_payout(payout)

    @pytest.mark.asyncio
    async def test_process_payout(
        self, agent: PayoutManagerAgent, sample_payout: Payout
    ) -> None:
        await agent.create_payout(sample_payout)
        processed = await agent.process_payout("payout-1")
        assert processed.status == PayoutStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_fail_payout(
        self, agent: PayoutManagerAgent, sample_payout: Payout
    ) -> None:
        await agent.create_payout(sample_payout)
        failed = await agent.fail_payout("payout-1", "Insufficient funds")
        assert failed.status == PayoutStatus.FAILED

    @pytest.mark.asyncio
    async def test_batch_process_payouts(
        self, agent: PayoutManagerAgent, sample_payout: Payout
    ) -> None:
        await agent.create_payout(sample_payout)
        payout2 = Payout(
            payout_id="payout-2",
            creator_id="creator-1",
            amount=Decimal("200.00"),
            period_start=datetime.now(UTC) - timedelta(days=30),
            period_end=datetime.now(UTC),
        )
        await agent.create_payout(payout2)
        result = await agent.batch_process_payouts(["payout-1", "payout-2"])
        assert result["total"] == 2
        assert result["successful"] == 2

    def test_get_pending_payouts(self, agent: PayoutManagerAgent) -> None:
        payouts = agent.get_pending_payouts()
        assert isinstance(payouts, list)

    def test_get_creator_balance(self, agent: PayoutManagerAgent) -> None:
        balance = agent.get_creator_balance("creator-1")
        assert isinstance(balance, Decimal)

    def test_get_total_paid(self, agent: PayoutManagerAgent) -> None:
        total = agent.get_total_paid("creator-1")
        assert isinstance(total, Decimal)

    def test_get_payout_count(self, agent: PayoutManagerAgent) -> None:
        count = agent.get_payout_count()
        assert isinstance(count, int)


class TestTierRecommenderAgent:
    """Tests for TierRecommenderAgent."""

    @pytest.fixture
    def agent(self) -> TierRecommenderAgent:
        return TierRecommenderAgent()

    @pytest.fixture
    def sample_profile(self) -> CreatorProfile:
        return CreatorProfile(
            creator_id="creator-1",
            subscriber_count=5000,
            monthly_revenue=Decimal("5000.00"),
            content_category="tech",
            engagement_rate=0.08,
        )

    @pytest.mark.asyncio
    async def test_recommend_tier(
        self, agent: TierRecommenderAgent, sample_profile: CreatorProfile
    ) -> None:
        result = await agent.recommend_tier(sample_profile)
        assert result is not None
        assert result.recommended_tier in TierLevel
        assert 0 <= result.confidence <= 1

    @pytest.mark.asyncio
    async def test_recommend_tier_high_subscribers(
        self, agent: TierRecommenderAgent
    ) -> None:
        profile = CreatorProfile(
            creator_id="creator-2",
            subscriber_count=150000,
            monthly_revenue=Decimal("50000.00"),
            content_category="tech",
            engagement_rate=0.15,
        )
        result = await agent.recommend_tier(profile)
        assert result.recommended_tier == TierLevel.DIAMOND

    @pytest.mark.asyncio
    async def test_recommend_tier_low_subscribers(
        self, agent: TierRecommenderAgent
    ) -> None:
        profile = CreatorProfile(
            creator_id="creator-3",
            subscriber_count=100,
            monthly_revenue=Decimal("100.00"),
            content_category="art",
            engagement_rate=0.02,
        )
        result = await agent.recommend_tier(profile)
        assert result.recommended_tier == TierLevel.BRONZE

    @pytest.mark.asyncio
    async def test_compare_tiers(
        self, agent: TierRecommenderAgent
    ) -> None:
        from creator_monetization.models.schemas import Tier

        tiers = [
            Tier(
                tier_id="tier-1",
                name="Bronze",
                level=TierLevel.BRONZE,
                monthly_price=Decimal("4.99"),
                yearly_price=Decimal("49.99"),
                benefits=["Basic content"],
            ),
            Tier(
                tier_id="tier-2",
                name="Gold",
                level=TierLevel.GOLD,
                monthly_price=Decimal("19.99"),
                yearly_price=Decimal("199.99"),
                benefits=["Premium content", "Discord access", "Early access"],
            ),
        ]
        result = await agent.compare_tiers("creator-1", tiers)
        assert result is not None
        assert result["tier_count"] == 2
        assert "best_value" in result

    @pytest.mark.asyncio
    async def test_optimize_tier_structure(
        self, agent: TierRecommenderAgent
    ) -> None:
        from creator_monetization.models.schemas import Tier

        tiers = [
            Tier(
                tier_id="tier-1",
                name="Bronze",
                level=TierLevel.BRONZE,
                monthly_price=Decimal("4.99"),
                yearly_price=Decimal("49.99"),
                benefits=["Basic content"],
            ),
        ]
        result = await agent.optimize_tier_structure("creator-1", tiers)
        assert result is not None
        assert "recommendations" in result

    def test_get_recommendation_count(
        self, agent: TierRecommenderAgent
    ) -> None:
        count = agent.get_recommendation_count("nonexistent")
        assert isinstance(count, int)
        assert count == 0


class TestSubscriptionAgent:
    """Tests for SubscriptionAgent."""

    @pytest.fixture
    def agent(self) -> SubscriptionAgent:
        return SubscriptionAgent()

    @pytest.fixture
    def sample_subscription(self) -> Subscription:
        return Subscription(
            subscription_id="sub-1",
            creator_id="creator-1",
            subscriber_id="user-1",
            tier_id="tier-1",
            status=SubscriptionStatus.ACTIVE,
            start_date=datetime.now(UTC),
            amount=Decimal("9.99"),
        )

    @pytest.mark.asyncio
    async def test_create_subscription(
        self, agent: SubscriptionAgent, sample_subscription: Subscription
    ) -> None:
        result = await agent.create_subscription(sample_subscription)
        assert result is not None
        assert result.subscription_id == "sub-1"
        assert result.creator_id == "creator-1"

    @pytest.mark.asyncio
    async def test_cancel_subscription(
        self, agent: SubscriptionAgent, sample_subscription: Subscription
    ) -> None:
        await agent.create_subscription(sample_subscription)
        cancelled = await agent.cancel_subscription("sub-1", "Too expensive")
        assert cancelled.status == SubscriptionStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_renew_subscription(
        self, agent: SubscriptionAgent, sample_subscription: Subscription
    ) -> None:
        await agent.create_subscription(sample_subscription)
        renewed = await agent.renew_subscription("sub-1")
        assert renewed.status == SubscriptionStatus.ACTIVE
        assert renewed.end_date is not None

    @pytest.mark.asyncio
    async def test_get_subscription_metrics(
        self, agent: SubscriptionAgent, sample_subscription: Subscription
    ) -> None:
        await agent.create_subscription(sample_subscription)
        metrics = await agent.get_subscription_metrics("creator-1")
        assert metrics is not None
        assert metrics.creator_id == "creator-1"
        assert metrics.total_subscribers == 1

    @pytest.mark.asyncio
    async def test_identify_churn_risk(
        self, agent: SubscriptionAgent, sample_subscription: Subscription
    ) -> None:
        await agent.create_subscription(sample_subscription)
        at_risk = await agent.identify_churn_risk("creator-1")
        assert isinstance(at_risk, list)

    def test_get_subscription_count(
        self, agent: SubscriptionAgent
    ) -> None:
        count = agent.get_subscription_count("nonexistent")
        assert isinstance(count, int)
        assert count == 0


class TestAnalyticsAgent:
    """Tests for AnalyticsAgent."""

    @pytest.fixture
    def agent(self) -> AnalyticsAgent:
        return AnalyticsAgent()

    @pytest.mark.asyncio
    async def test_record_metric(self, agent: AnalyticsAgent) -> None:
        point = await agent.record_metric("revenue", 100.0)
        assert point is not None
        assert point.value == 100.0

    @pytest.mark.asyncio
    async def test_generate_report(self, agent: AnalyticsAgent) -> None:
        await agent.record_metric("revenue", 100.0)
        await agent.record_metric("revenue", 200.0)
        period = ReportPeriod(
            start=datetime.now(UTC) - timedelta(days=1),
            end=datetime.now(UTC) + timedelta(days=1),
        )
        report = await agent.generate_report("report-1", "creator-1", period)
        assert report is not None
        assert report["report_id"] == "report-1"

    @pytest.mark.asyncio
    async def test_forecast_metric(self, agent: AnalyticsAgent) -> None:
        await agent.record_metric("revenue", 100.0)
        await agent.record_metric("revenue", 110.0)
        await agent.record_metric("revenue", 120.0)
        forecast = await agent.forecast_metric("revenue", days=7)
        assert isinstance(forecast, list)
        assert len(forecast) == 7

    def test_get_report(self, agent: AnalyticsAgent) -> None:
        report = agent.get_report("nonexistent")
        assert report is None

    def test_get_available_metrics(self, agent: AnalyticsAgent) -> None:
        metrics = agent.get_available_metrics()
        assert isinstance(metrics, list)

    def test_get_report_count(self, agent: AnalyticsAgent) -> None:
        count = agent.get_report_count()
        assert isinstance(count, int)