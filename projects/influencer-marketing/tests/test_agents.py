"""Tests for influencer marketing agent implementations."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from influencer_marketing.agents.base import AgentConfig, AgentResult
from influencer_marketing.agents.discovery import (
    DiscoveryAgent,
    DiscoveryCriteria,
    DiscoveredInfluencer,
)
from influencer_marketing.agents.negotiation import (
    ContractTerms,
    NegotiationAgent,
    NegotiationStatus,
)
from influencer_marketing.agents.outreach import (
    OutreachAgent,
    OutreachMessage,
    OutreachResult,
    OutreachStatus,
)
from influencer_marketing.agents.vetting import (
    VettingAgent,
    VettingCriteria,
    VettingReport,
)


def _make_influencer() -> DiscoveredInfluencer:
    return DiscoveredInfluencer(
        platform="instagram",
        platform_id="ig_123",
        username="test_influencer",
        display_name="Test Influencer",
        bio="Test bio content",
        follower_count=50000,
        following_count=500,
        post_count=200,
        engagement_rate=0.03,
        profile_url="https://instagram.com/test_influencer",
        profile_image_url="https://example.com/pic.jpg",
        categories=["fitness", "lifestyle"],
    )


class TestDiscoveryAgent:
    """Tests for DiscoveryAgent."""

    @pytest.fixture
    def agent(self) -> DiscoveryAgent:
        return DiscoveryAgent()

    async def test_validate_input_valid(self, agent: DiscoveryAgent) -> None:
        criteria = DiscoveryCriteria(platforms=["instagram"])
        assert await agent.validate_input(criteria) is True

    async def test_validate_input_no_platforms(self, agent: DiscoveryAgent) -> None:
        criteria = DiscoveryCriteria(platforms=[])
        assert await agent.validate_input(criteria) is False

    async def test_validate_input_invalid_followers(self, agent: DiscoveryAgent) -> None:
        criteria = DiscoveryCriteria(platforms=["instagram"], min_followers=1000, max_followers=100)
        assert await agent.validate_input(criteria) is False

    async def test_execute(self, agent: DiscoveryAgent) -> None:
        criteria = DiscoveryCriteria(platforms=["instagram"], max_results=10)
        result = await agent.execute(criteria)
        assert isinstance(result, AgentResult)


class TestVettingAgent:
    """Tests for VettingAgent."""

    @pytest.fixture
    def agent(self) -> VettingAgent:
        return VettingAgent()

    async def test_validate_input_valid(self, agent: VettingAgent) -> None:
        influencer = _make_influencer()
        criteria = VettingCriteria()
        assert await agent.validate_input((influencer, criteria)) is True

    async def test_validate_input_none(self, agent: VettingAgent) -> None:
        criteria = VettingCriteria()
        assert await agent.validate_input((None, criteria)) is False

    async def test_execute(self, agent: VettingAgent) -> None:
        influencer = _make_influencer()
        criteria = VettingCriteria()
        result = await agent.execute((influencer, criteria))
        assert isinstance(result, AgentResult)


class TestOutreachAgent:
    """Tests for OutreachAgent."""

    @pytest.fixture
    def agent(self) -> OutreachAgent:
        return OutreachAgent()

    async def test_validate_input_valid(self, agent: OutreachAgent) -> None:
        influencer = _make_influencer()
        vetting_report = VettingReport(
            influencer=influencer,
            overall_score=0.8,
            authenticity_score=0.9,
            content_quality_score=0.7,
            audience_quality_score=0.8,
            engagement_quality_score=0.7,
            brand_safety_score=0.9,
            is_approved=True,
        )
        message = OutreachMessage(subject="Test", body="Hello, this is a test message body.")
        assert await agent.validate_input((vetting_report, message)) is True

    async def test_validate_input_not_approved(self, agent: OutreachAgent) -> None:
        influencer = _make_influencer()
        vetting_report = VettingReport(
            influencer=influencer,
            overall_score=0.3,
            authenticity_score=0.3,
            content_quality_score=0.3,
            audience_quality_score=0.3,
            engagement_quality_score=0.3,
            brand_safety_score=0.3,
            is_approved=False,
        )
        message = OutreachMessage(subject="Test", body="Hello, this is a test message body.")
        assert await agent.validate_input((vetting_report, message)) is False

    async def test_validate_input_short_body(self, agent: OutreachAgent) -> None:
        influencer = _make_influencer()
        vetting_report = VettingReport(
            influencer=influencer,
            overall_score=0.8,
            authenticity_score=0.9,
            content_quality_score=0.7,
            audience_quality_score=0.8,
            engagement_quality_score=0.7,
            brand_safety_score=0.9,
            is_approved=True,
        )
        message = OutreachMessage(subject="Test", body="Hi")
        assert await agent.validate_input((vetting_report, message)) is False


class TestNegotiationAgent:
    """Tests for NegotiationAgent."""

    @pytest.fixture
    def agent(self) -> NegotiationAgent:
        return NegotiationAgent()

    async def test_validate_input_valid(self, agent: NegotiationAgent) -> None:
        outreach = OutreachResult(
            influencer_id="inf_1",
            status=OutreachStatus.INTERESTED,
            message=OutreachMessage(subject="Test", body="Test body"),
        )
        terms = ContractTerms(compensation=1000.0)
        assert await agent.validate_input((outreach, terms)) is True

    async def test_validate_input_not_interested(self, agent: NegotiationAgent) -> None:
        outreach = OutreachResult(
            influencer_id="inf_1",
            status=OutreachStatus.DECLINED,
            message=OutreachMessage(subject="Test", body="Test body"),
        )
        terms = ContractTerms(compensation=1000.0)
        assert await agent.validate_input((outreach, terms)) is False

    async def test_validate_input_negative_compensation(self, agent: NegotiationAgent) -> None:
        outreach = OutreachResult(
            influencer_id="inf_1",
            status=OutreachStatus.INTERESTED,
            message=OutreachMessage(subject="Test", body="Test body"),
        )
        terms = ContractTerms(compensation=-100.0)
        assert await agent.validate_input((outreach, terms)) is False
