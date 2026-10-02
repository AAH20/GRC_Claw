"""Tests for SMB Marketing agents."""

from __future__ import annotations

import pytest

from smb_marketing.agents.analytics import AnalyticsAgent
from smb_marketing.agents.campaigns import CampaignsAgent
from smb_marketing.agents.content import ContentAgent
from smb_marketing.agents.email import EmailAgent
from smb_marketing.agents.social import SocialAgent


class TestContentAgent:
    """Tests for ContentAgent."""

    @pytest.fixture
    def agent(self) -> ContentAgent:
        return ContentAgent()

    @pytest.mark.asyncio
    async def test_generate(self, agent: ContentAgent) -> None:
        from smb_marketing.agents.content import ContentRequest

        request = ContentRequest(
            content_type="blog_post",
            topic="AI in Marketing",
            tone="professional",
        )
        result = await agent.generate(request)
        assert result is not None
        assert result.content is not None


class TestEmailAgent:
    """Tests for EmailAgent."""

    @pytest.fixture
    def agent(self) -> EmailAgent:
        return EmailAgent()

    @pytest.mark.asyncio
    async def test_create_campaign(self, agent: EmailAgent) -> None:
        from smb_marketing.agents.email import EmailCampaignRequest

        request = EmailCampaignRequest(
            name="Test Campaign",
            subject="Test Subject",
            body="Test body",
        )
        result = await agent.create_campaign(request)
        assert result is not None
        assert result.name == "Test Campaign"

    @pytest.mark.asyncio
    async def test_send_campaign(self, agent: EmailAgent) -> None:
        from smb_marketing.agents.email import EmailCampaignRequest

        request = EmailCampaignRequest(
            name="Test Campaign",
            subject="Test Subject",
            body="Test body",
        )
        created = await agent.create_campaign(request)
        sent = await agent.send_campaign(created.id)
        assert sent is not None

    @pytest.mark.asyncio
    async def test_get_campaign(self, agent: EmailAgent) -> None:
        from smb_marketing.agents.email import EmailCampaignRequest

        request = EmailCampaignRequest(
            name="Test Campaign",
            subject="Test Subject",
            body="Test body",
        )
        created = await agent.create_campaign(request)
        fetched = await agent.get_campaign(created.id)
        assert fetched is not None
        assert fetched.id == created.id

    @pytest.mark.asyncio
    async def test_list_campaigns(self, agent: EmailAgent) -> None:
        from smb_marketing.agents.email import EmailCampaignRequest

        await agent.create_campaign(EmailCampaignRequest(name="C1", subject="S1", body="B1"))
        await agent.create_campaign(EmailCampaignRequest(name="C2", subject="S2", body="B2"))
        campaigns = await agent.list_campaigns()
        assert len(campaigns) == 2

    def test_optimize_subject_line(self, agent: EmailAgent) -> None:
        optimized = agent.optimize_subject_line("Test Subject")
        assert isinstance(optimized, str)


class TestSocialAgent:
    """Tests for SocialAgent."""

    @pytest.fixture
    def agent(self) -> SocialAgent:
        return SocialAgent()

    @pytest.mark.asyncio
    async def test_schedule_post(self, agent: SocialAgent) -> None:
        from smb_marketing.agents.social import SocialPostRequest

        request = SocialPostRequest(
            content="Test post",
            platform="twitter",
            scheduled_time="2026-01-01T12:00:00Z",
        )
        result = await agent.schedule_post(request)
        assert result is not None
        assert result.content == "Test post"


class TestCampaignsAgent:
    """Tests for CampaignsAgent."""

    @pytest.fixture
    def agent(self) -> CampaignsAgent:
        return CampaignsAgent()

    @pytest.mark.asyncio
    async def test_create_campaign(self, agent: CampaignsAgent) -> None:
        from smb_marketing.agents.campaigns import CampaignRequest

        request = CampaignRequest(
            name="Test Campaign",
            objective="awareness",
            budget=1000.0,
        )
        result = await agent.create_campaign(request)
        assert result is not None
        assert result.name == "Test Campaign"

    @pytest.mark.asyncio
    async def test_get_campaign(self, agent: CampaignsAgent) -> None:
        from smb_marketing.agents.campaigns import CampaignRequest

        request = CampaignRequest(
            name="Test Campaign",
            objective="awareness",
            budget=1000.0,
        )
        created = await agent.create_campaign(request)
        fetched = await agent.get_campaign(created.id)
        assert fetched is not None
        assert fetched.id == created.id

    @pytest.mark.asyncio
    async def test_list_campaigns(self, agent: CampaignsAgent) -> None:
        from smb_marketing.agents.campaigns import CampaignRequest

        await agent.create_campaign(CampaignRequest(name="C1", objective="awareness", budget=100.0))
        await agent.create_campaign(CampaignRequest(name="C2", objective="conversion", budget=200.0))
        campaigns = await agent.list_campaigns()
        assert len(campaigns) == 2

    @pytest.mark.asyncio
    async def test_update_campaign(self, agent: CampaignsAgent) -> None:
        from smb_marketing.agents.campaigns import CampaignRequest

        request = CampaignRequest(
            name="Test Campaign",
            objective="awareness",
            budget=1000.0,
        )
        created = await agent.create_campaign(request)
        updated = await agent.update_campaign(created.id, {"name": "Updated Campaign"})
        assert updated.name == "Updated Campaign"

    @pytest.mark.asyncio
    async def test_delete_campaign(self, agent: CampaignsAgent) -> None:
        from smb_marketing.agents.campaigns import CampaignRequest

        request = CampaignRequest(
            name="Test Campaign",
            objective="awareness",
            budget=1000.0,
        )
        created = await agent.create_campaign(request)
        await agent.delete_campaign(created.id)
        fetched = await agent.get_campaign(created.id)
        assert fetched is None

    def test_allocate_budget(self, agent: CampaignsAgent) -> None:
        allocation = agent.allocate_budget(1000.0, {"email": 0.4, "social": 0.3, "ads": 0.3})
        assert allocation["email"] == 400.0
        assert allocation["social"] == 300.0
        assert allocation["ads"] == 300.0


class TestAnalyticsAgent:
    """Tests for AnalyticsAgent."""

    @pytest.fixture
    def agent(self) -> AnalyticsAgent:
        return AnalyticsAgent()

    @pytest.mark.asyncio
    async def test_generate_report(self, agent: AnalyticsAgent) -> None:
        result = await agent.generate_report()
        assert result is not None
