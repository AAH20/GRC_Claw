"""Tests for Partner Management agents."""

from __future__ import annotations

import pytest

from partner_management.agents.communication import CommunicationAgent
from partner_management.agents.deal_management import DealManagementAgent
from partner_management.agents.onboarding import OnboardingAgent


class TestOnboardingAgent:
    """Tests for OnboardingAgent."""

    @pytest.fixture
    def agent(self) -> OnboardingAgent:
        return OnboardingAgent()

    @pytest.mark.asyncio
    async def test_register_partner(self, agent: OnboardingAgent) -> None:
        from partner_management.agents.onboarding import PartnerProfile

        profile = PartnerProfile(
            name="Test Partner",
            email="test@example.com",
            tier="gold",
        )
        result = await agent.register_partner(profile)
        assert result is not None
        assert result.name == "Test Partner"

    @pytest.mark.asyncio
    async def test_qualify_partner(self, agent: OnboardingAgent) -> None:
        from partner_management.agents.onboarding import PartnerProfile

        profile = PartnerProfile(
            name="Test Partner",
            email="test@example.com",
            tier="gold",
        )
        registered = await agent.register_partner(profile)
        qualified = await agent.qualify_partner(registered.id)
        assert qualified is not None

    @pytest.mark.asyncio
    async def test_approve_partner(self, agent: OnboardingAgent) -> None:
        from partner_management.agents.onboarding import PartnerProfile

        profile = PartnerProfile(
            name="Test Partner",
            email="test@example.com",
            tier="gold",
        )
        registered = await agent.register_partner(profile)
        approved = await agent.approve_partner(registered.id)
        assert approved is not None

    @pytest.mark.asyncio
    async def test_activate_partner(self, agent: OnboardingAgent) -> None:
        from partner_management.agents.onboarding import PartnerProfile

        profile = PartnerProfile(
            name="Test Partner",
            email="test@example.com",
            tier="gold",
        )
        registered = await agent.register_partner(profile)
        activated = await agent.activate_partner(registered.id)
        assert activated is not None

    @pytest.mark.asyncio
    async def test_get_partner(self, agent: OnboardingAgent) -> None:
        from partner_management.agents.onboarding import PartnerProfile

        profile = PartnerProfile(
            name="Test Partner",
            email="test@example.com",
            tier="gold",
        )
        registered = await agent.register_partner(profile)
        fetched = await agent.get_partner(registered.id)
        assert fetched is not None
        assert fetched.id == registered.id

    @pytest.mark.asyncio
    async def test_list_partners(self, agent: OnboardingAgent) -> None:
        from partner_management.agents.onboarding import PartnerProfile

        await agent.register_partner(PartnerProfile(name="P1", email="p1@test.com"))
        await agent.register_partner(PartnerProfile(name="P2", email="p2@test.com"))
        partners = await agent.list_partners()
        assert len(partners) == 2

    @pytest.mark.asyncio
    async def test_update_tier(self, agent: OnboardingAgent) -> None:
        from partner_management.agents.onboarding import PartnerProfile, PartnerTier

        profile = PartnerProfile(
            name="Test Partner",
            email="test@example.com",
            tier="gold",
        )
        registered = await agent.register_partner(profile)
        updated = await agent.update_tier(registered.id, PartnerTier.PLATINUM)
        assert updated.tier == PartnerTier.PLATINUM


class TestDealManagementAgent:
    """Tests for DealManagementAgent."""

    @pytest.fixture
    def agent(self) -> DealManagementAgent:
        return DealManagementAgent()

    @pytest.mark.asyncio
    async def test_register_deal(self, agent: DealManagementAgent) -> None:
        from partner_management.agents.deal_management import Deal

        deal = Deal(
            name="Test Deal",
            partner_id="partner-123",
            value=10000.0,
        )
        result = await agent.register_deal(deal)
        assert result is not None
        assert result.name == "Test Deal"

    @pytest.mark.asyncio
    async def test_advance_stage(self, agent: DealManagementAgent) -> None:
        from partner_management.agents.deal_management import Deal, DealStage

        deal = Deal(
            name="Test Deal",
            partner_id="partner-123",
            value=10000.0,
        )
        registered = await agent.register_deal(deal)
        advanced = await agent.advance_stage(registered.id, DealStage.PROPOSAL)
        assert advanced.stage == DealStage.PROPOSAL

    @pytest.mark.asyncio
    async def test_get_deal(self, agent: DealManagementAgent) -> None:
        from partner_management.agents.deal_management import Deal

        deal = Deal(
            name="Test Deal",
            partner_id="partner-123",
            value=10000.0,
        )
        registered = await agent.register_deal(deal)
        fetched = await agent.get_deal(registered.id)
        assert fetched is not None
        assert fetched.id == registered.id

    @pytest.mark.asyncio
    async def test_list_deals(self, agent: DealManagementAgent) -> None:
        from partner_management.agents.deal_management import Deal

        await agent.register_deal(Deal(name="D1", partner_id="p1", value=1000.0))
        await agent.register_deal(Deal(name="D2", partner_id="p2", value=2000.0))
        deals = await agent.list_deals()
        assert len(deals) == 2

    @pytest.mark.asyncio
    async def test_forecast_revenue(self, agent: DealManagementAgent) -> None:
        from partner_management.agents.deal_management import Deal

        await agent.register_deal(Deal(name="D1", partner_id="p1", value=1000.0))
        await agent.register_deal(Deal(name="D2", partner_id="p2", value=2000.0))
        forecast = await agent.forecast_revenue()
        assert forecast is not None


class TestCommunicationAgent:
    """Tests for CommunicationAgent."""

    @pytest.fixture
    def agent(self) -> CommunicationAgent:
        return CommunicationAgent()

    @pytest.mark.asyncio
    async def test_send_message(self, agent: CommunicationAgent) -> None:
        from partner_management.agents.communication import PartnerMessage

        message = PartnerMessage(
            partner_id="partner-123",
            subject="Test",
            body="Test message",
        )
        result = await agent.send_message(message)
        assert result is not None
        assert result.subject == "Test"

    @pytest.mark.asyncio
    async def test_register_template(self, agent: CommunicationAgent) -> None:
        await agent.register_template("welcome", "Welcome {{name}}!")

    @pytest.mark.asyncio
    async def test_send_templated(self, agent: CommunicationAgent) -> None:
        await agent.register_template("welcome", "Welcome {{name}}!")
        result = await agent.send_templated(
            "welcome",
            partner_id="partner-123",
            variables={"name": "Test"},
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_message(self, agent: CommunicationAgent) -> None:
        from partner_management.agents.communication import PartnerMessage

        message = PartnerMessage(
            partner_id="partner-123",
            subject="Test",
            body="Test message",
        )
        sent = await agent.send_message(message)
        fetched = await agent.get_message(sent.id)
        assert fetched is not None
        assert fetched.id == sent.id

    @pytest.mark.asyncio
    async def test_list_messages(self, agent: CommunicationAgent) -> None:
        from partner_management.agents.communication import PartnerMessage

        await agent.send_message(PartnerMessage(partner_id="p1", subject="S1", body="B1"))
        await agent.send_message(PartnerMessage(partner_id="p2", subject="S2", body="B2"))
        messages = await agent.list_messages()
        assert len(messages) == 2

    @pytest.mark.asyncio
    async def test_mark_delivered(self, agent: CommunicationAgent) -> None:
        from partner_management.agents.communication import PartnerMessage

        message = PartnerMessage(
            partner_id="partner-123",
            subject="Test",
            body="Test message",
        )
        sent = await agent.send_message(message)
        delivered = await agent.mark_delivered(sent.id)
        assert delivered.is_delivered is True
