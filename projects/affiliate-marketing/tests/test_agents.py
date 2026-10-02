"""Tests for Affiliate Marketing agents."""

from __future__ import annotations

from decimal import Decimal

import pytest

from affiliate_marketing.agents.analytics import AnalyticsAgent
from affiliate_marketing.agents.optimization import OptimizationAgent
from affiliate_marketing.agents.payout import PayoutAgent
from affiliate_marketing.agents.recruitment import RecruitmentAgent
from affiliate_marketing.agents.tracking import TrackingAgent


class TestTrackingAgent:
    """Tests for TrackingAgent."""

    @pytest.fixture
    def agent(self) -> TrackingAgent:
        return TrackingAgent()

    @pytest.mark.asyncio
    async def test_track_click(self, agent: TrackingAgent) -> None:
        from affiliate_marketing.agents.tracking import ClickEvent

        event = ClickEvent(
            affiliate_id="aff-123",
            campaign_id="camp-456",
            ip_address="192.168.1.1",
        )
        result = await agent.track_click(event)
        assert result is not None
        assert result.affiliate_id == "aff-123"

    @pytest.mark.asyncio
    async def test_track_conversion(self, agent: TrackingAgent) -> None:
        from affiliate_marketing.agents.tracking import ConversionEvent

        event = ConversionEvent(
            affiliate_id="aff-123",
            campaign_id="camp-456",
            amount=Decimal("100.00"),
        )
        result = await agent.track_conversion(event)
        assert result is not None
        assert result.affiliate_id == "aff-123"

    @pytest.mark.asyncio
    async def test_update_conversion_status(self, agent: TrackingAgent) -> None:
        from affiliate_marketing.agents.tracking import ConversionEvent

        event = ConversionEvent(
            affiliate_id="aff-123",
            campaign_id="camp-456",
            amount=Decimal("100.00"),
        )
        tracked = await agent.track_conversion(event)
        updated = await agent.update_conversion_status(tracked.id, "approved")
        assert updated.status == "approved"


class TestPayoutAgent:
    """Tests for PayoutAgent."""

    @pytest.fixture
    def agent(self) -> PayoutAgent:
        return PayoutAgent()

    def test_calculate_commission(self, agent: PayoutAgent) -> None:
        commission = agent.calculate_commission(Decimal("100.00"))
        assert commission == Decimal("10.00")

    @pytest.mark.asyncio
    async def test_create_payout(self, agent: PayoutAgent) -> None:
        from affiliate_marketing.agents.payout import PayoutRecord

        record = PayoutRecord(
            affiliate_id="aff-123",
            amount=Decimal("100.00"),
        )
        result = await agent.create_payout(record)
        assert result is not None
        assert result.affiliate_id == "aff-123"

    @pytest.mark.asyncio
    async def test_process_payout(self, agent: PayoutAgent) -> None:
        from affiliate_marketing.agents.payout import PayoutRecord

        record = PayoutRecord(
            affiliate_id="aff-123",
            amount=Decimal("100.00"),
        )
        created = await agent.create_payout(record)
        processed = await agent.process_payout(created.id)
        assert processed.status == "processed"

    @pytest.mark.asyncio
    async def test_fail_payout(self, agent: PayoutAgent) -> None:
        from affiliate_marketing.agents.payout import PayoutRecord

        record = PayoutRecord(
            affiliate_id="aff-123",
            amount=Decimal("100.00"),
        )
        created = await agent.create_payout(record)
        failed = await agent.fail_payout(created.id, "Insufficient funds")
        assert failed.status == "failed"

    def test_get_pending_payouts(self, agent: PayoutAgent) -> None:
        payouts = agent.get_pending_payouts()
        assert isinstance(payouts, list)

    def test_get_partner_payouts(self, agent: PayoutAgent) -> None:
        payouts = agent.get_partner_payouts("aff-123")
        assert isinstance(payouts, list)

    def test_get_total_paid(self, agent: PayoutAgent) -> None:
        total = agent.get_total_paid("aff-123")
        assert isinstance(total, Decimal)


class TestRecruitmentAgent:
    """Tests for RecruitmentAgent."""

    @pytest.fixture
    def agent(self) -> RecruitmentAgent:
        return RecruitmentAgent()

    @pytest.mark.asyncio
    async def test_discover_partners(self, agent: RecruitmentAgent) -> None:
        partners = await agent.discover_partners("tech", limit=5)
        assert isinstance(partners, list)
        assert len(partners) <= 5

    @pytest.mark.asyncio
    async def test_evaluate_partner(self, agent: RecruitmentAgent) -> None:
        from affiliate_marketing.agents.recruitment import PartnerProfile

        profile = PartnerProfile(
            name="Test Partner",
            website="https://example.com",
            niche="tech",
        )
        result = await agent.evaluate_partner(profile)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_generate_outreach(self, agent: RecruitmentAgent) -> None:
        from affiliate_marketing.agents.recruitment import PartnerProfile

        profile = PartnerProfile(
            name="Test Partner",
            website="https://example.com",
            niche="tech",
        )
        message = await agent.generate_outreach(profile)
        assert isinstance(message, str)
        assert len(message) > 0

    def test_get_discovered_count(self, agent: RecruitmentAgent) -> None:
        count = agent.get_discovered_count()
        assert isinstance(count, int)


class TestAnalyticsAgent:
    """Tests for AnalyticsAgent."""

    @pytest.fixture
    def agent(self) -> AnalyticsAgent:
        return AnalyticsAgent()

    @pytest.mark.asyncio
    async def test_record_metric(self, agent: AnalyticsAgent) -> None:
        await agent.record_metric("clicks", 100.0)

    @pytest.mark.asyncio
    async def test_generate_report(self, agent: AnalyticsAgent) -> None:
        await agent.record_metric("clicks", 100.0)
        await agent.record_metric("conversions", 10.0)
        report = await agent.generate_report()
        assert report is not None

    @pytest.mark.asyncio
    async def test_forecast_metric(self, agent: AnalyticsAgent) -> None:
        await agent.record_metric("clicks", 100.0)
        forecast = await agent.forecast_metric("clicks")
        assert forecast is not None

    def test_get_report(self, agent: AnalyticsAgent) -> None:
        report = agent.get_report("nonexistent")
        assert report is None

    def test_get_available_metrics(self, agent: AnalyticsAgent) -> None:
        metrics = agent.get_available_metrics()
        assert isinstance(metrics, list)


class TestOptimizationAgent:
    """Tests for OptimizationAgent."""

    @pytest.fixture
    def agent(self) -> OptimizationAgent:
        return OptimizationAgent()

    @pytest.mark.asyncio
    async def test_create_campaign(self, agent: OptimizationAgent) -> None:
        from affiliate_marketing.agents.optimization import Campaign

        campaign = Campaign(
            name="Test Campaign",
            niche="tech",
            budget=1000.0,
        )
        result = await agent.create_campaign(campaign)
        assert result is not None
        assert result.name == "Test Campaign"

    @pytest.mark.asyncio
    async def test_analyze_ab_test(self, agent: OptimizationAgent) -> None:
        from affiliate_marketing.agents.optimization import Campaign

        campaign = Campaign(
            name="Test Campaign",
            niche="tech",
            budget=1000.0,
        )
        created = await agent.create_campaign(campaign)
        result = await agent.analyze_ab_test(created.id)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_optimize_bids(self, agent: OptimizationAgent) -> None:
        from affiliate_marketing.agents.optimization import Campaign

        campaign = Campaign(
            name="Test Campaign",
            niche="tech",
            budget=1000.0,
        )
        created = await agent.create_campaign(campaign)
        result = await agent.optimize_bids(created.id)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_recommendations(self, agent: OptimizationAgent) -> None:
        from affiliate_marketing.agents.optimization import Campaign

        campaign = Campaign(
            name="Test Campaign",
            niche="tech",
            budget=1000.0,
        )
        created = await agent.create_campaign(campaign)
        recs = await agent.get_recommendations(created.id)
        assert isinstance(recs, list)

    def test_get_campaign_count(self, agent: OptimizationAgent) -> None:
        count = agent.get_campaign_count()
        assert isinstance(count, int)
