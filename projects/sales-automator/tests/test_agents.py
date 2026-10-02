"""Tests for agent implementations."""

from __future__ import annotations

from datetime import datetime

import pytest

from sales_automator.agents.demo_scheduling import DemoBooking, DemoSchedulingAgent, TimeSlot
from sales_automator.agents.followup import FollowUpAction, FollowUpAgent
from sales_automator.agents.outreach import Channel, OutreachAgent, OutreachSequence
from sales_automator.agents.prospecting import Prospect, ProspectingAgent, ProspectScore
from sales_automator.agents.qualification import (
    BANTScore,
    QualificationAgent,
    QualificationFramework,
    QualificationResult,
)
from sales_automator.agents.sales_forecasting import (
    ForecastResult,
    SalesForecastingAgent,
)


class TestProspectingAgent:
    """Tests for ProspectingAgent."""

    @pytest.fixture
    def agent(self) -> ProspectingAgent:
        return ProspectingAgent(scoring_threshold=0.6)

    @pytest.fixture
    def sample_prospect(self) -> Prospect:
        return Prospect(
            id="p1",
            name="Jane Doe",
            company="Acme Corp",
            title="VP of Sales",
            email="jane@acme.com",
        )

    async def test_score_prospect(self, agent: ProspectingAgent, sample_prospect: Prospect) -> None:
        score = await agent.score(sample_prospect)
        assert isinstance(score, ProspectScore)
        assert 0.0 <= score.overall <= 1.0

    async def test_is_qualified(self, agent: ProspectingAgent) -> None:
        high_score = ProspectScore(overall=0.8, firmographic=0.8, technographic=0.8, intent=0.8)
        low_score = ProspectScore(overall=0.3, firmographic=0.3, technographic=0.3, intent=0.3)
        assert agent.is_qualified(high_score) is True
        assert agent.is_qualified(low_score) is False

    async def test_discover(self, agent: ProspectingAgent) -> None:
        results = await agent.discover({"industry": "SaaS"}, limit=10)
        assert isinstance(results, list)

    async def test_enrich(self, agent: ProspectingAgent, sample_prospect: Prospect) -> None:
        enriched = await agent.enrich(sample_prospect)
        assert enriched.id == sample_prospect.id


class TestOutreachAgent:
    """Tests for OutreachAgent."""

    @pytest.fixture
    def agent(self) -> OutreachAgent:
        return OutreachAgent(channels=[Channel.EMAIL, Channel.LINKEDIN])

    async def test_generate_sequence(self, agent: OutreachAgent) -> None:
        sequence = await agent.generate_sequence("p1", {"pain": "efficiency"}, steps=3)
        assert isinstance(sequence, OutreachSequence)
        assert len(sequence.steps) == 3
        assert sequence.target_prospect_id == "p1"

    async def test_personalize_message(self, agent: OutreachAgent) -> None:
        result = await agent.personalize_message("Hello {name}", {"name": "Jane"})
        assert isinstance(result, str)

    async def test_optimize_send_time(self, agent: OutreachAgent) -> None:
        result = await agent.optimize_send_time("p1", Channel.EMAIL)
        assert isinstance(result, str)


class TestQualificationAgent:
    """Tests for QualificationAgent."""

    @pytest.fixture
    def agent(self) -> QualificationAgent:
        return QualificationAgent(framework=QualificationFramework.BANT, min_score=0.5)

    async def test_qualify(self, agent: QualificationAgent) -> None:
        result = await agent.qualify("p1", {"conversation": "test"})
        assert isinstance(result, QualificationResult)
        assert result.prospect_id == "p1"

    async def test_bant_overall(self) -> None:
        bant = BANTScore(budget=0.8, authority=0.6, need=0.9, timeline=0.7)
        assert bant.overall == pytest.approx(0.75)

    async def test_is_qualified(self, agent: QualificationAgent) -> None:
        qualified = QualificationResult(
            prospect_id="p1",
            framework=QualificationFramework.BANT,
            qualified=True,
            score=0.8,
        )
        not_qualified = QualificationResult(
            prospect_id="p2",
            framework=QualificationFramework.BANT,
            qualified=False,
            score=0.3,
        )
        assert agent.is_qualified(qualified) is True
        assert agent.is_qualified(not_qualified) is False


class TestDemoSchedulingAgent:
    """Tests for DemoSchedulingAgent."""

    @pytest.fixture
    def agent(self) -> DemoSchedulingAgent:
        return DemoSchedulingAgent(default_duration_minutes=30, buffer_minutes=15)

    async def test_find_available_slots(self, agent: DemoSchedulingAgent) -> None:
        slots = await agent.find_available_slots(
            "p1",
            datetime(2026, 10, 1),
            datetime(2026, 10, 7),
        )
        assert isinstance(slots, list)

    async def test_book_demo(self, agent: DemoSchedulingAgent) -> None:
        slot = TimeSlot(start=datetime(2026, 10, 1, 10, 0), end=datetime(2026, 10, 1, 10, 30))
        booking = await agent.book_demo("p1", slot)
        assert isinstance(booking, DemoBooking)
        assert booking.prospect_id == "p1"

    async def test_cancel(self, agent: DemoSchedulingAgent) -> None:
        result = await agent.cancel("demo_1", reason="Prospect requested reschedule")
        assert result is True


class TestFollowUpAgent:
    """Tests for FollowUpAgent."""

    @pytest.fixture
    def agent(self) -> FollowUpAgent:
        return FollowUpAgent(cadence_days=3, max_touches=5)

    async def test_schedule_followup(self, agent: FollowUpAgent) -> None:
        action = await agent.schedule_followup("p1", "email", "email", content="Follow up")
        assert isinstance(action, FollowUpAction)
        assert action.prospect_id == "p1"
        assert action.status == "pending"

    async def test_should_follow_up(self, agent: FollowUpAgent) -> None:
        recent = datetime.utcnow()
        old = datetime(2020, 1, 1)
        assert await agent.should_follow_up("p1", old) is True
        assert await agent.should_follow_up("p1", recent) is False

    async def test_get_pending_followups(self, agent: FollowUpAgent) -> None:
        result = await agent.get_pending_followups()
        assert isinstance(result, list)


class TestSalesForecastingAgent:
    """Tests for SalesForecastingAgent."""

    @pytest.fixture
    def agent(self) -> SalesForecastingAgent:
        return SalesForecastingAgent(forecast_horizon_days=90, confidence_interval=0.95)

    async def test_generate_forecast(self, agent: SalesForecastingAgent) -> None:
        result = await agent.generate_forecast(
            datetime(2026, 10, 1),
            datetime(2026, 12, 31),
        )
        assert isinstance(result, ForecastResult)
        assert result.confidence_interval == 0.95

    async def test_identify_at_risk_deals(self, agent: SalesForecastingAgent) -> None:
        result = await agent.identify_at_risk_deals(threshold_days=14)
        assert isinstance(result, list)

    async def test_get_pipeline_summary(self, agent: SalesForecastingAgent) -> None:
        result = await agent.get_pipeline_summary()
        assert isinstance(result, dict)
