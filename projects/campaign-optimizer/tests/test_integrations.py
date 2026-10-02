"""Tests for the Campaign Optimizer platform integrations."""

from __future__ import annotations

import httpx
import pytest
import respx

from campaign_optimizer.integrations.google import GoogleAdsClient
from campaign_optimizer.integrations.linkedin import LinkedInAdsClient
from campaign_optimizer.integrations.meta import MetaAdsClient


# ─── Meta Ads Client Tests ──────────────────────────────────────────


class TestMetaAdsClient:
    """Tests for the Meta Ads API client."""

    @pytest.fixture
    def client(self) -> MetaAdsClient:
        """Create a Meta Ads client instance."""
        return MetaAdsClient(
            access_token="test_token_123",
            ad_account_id="act_123456789",
        )

    def test_client_initialization(self, client: MetaAdsClient) -> None:
        """Test client initialization with valid credentials."""
        assert client.access_token == "test_token_123"
        assert client.ad_account_id == "act_123456789"

    def test_client_empty_token_raises(self) -> None:
        """Test that empty access token raises ValueError."""
        with pytest.raises(ValueError, match="Access token is required"):
            MetaAdsClient(access_token="", ad_account_id="act_123")

    def test_client_empty_account_raises(self) -> None:
        """Test that empty account ID raises ValueError."""
        with pytest.raises(ValueError, match="Ad account ID is required"):
            MetaAdsClient(access_token="token", ad_account_id="")

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_campaigns(self, client: MetaAdsClient) -> None:
        """Test getting campaigns from Meta API."""
        respx.get(
            "https://graph.facebook.com/v19.0/act_123456789/campaigns"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [
                        {"id": "camp_1", "name": "Campaign 1", "status": "ACTIVE"},
                        {"id": "camp_2", "name": "Campaign 2", "status": "PAUSED"},
                    ]
                },
            )
        )
        campaigns = await client.get_campaigns()
        assert len(campaigns) == 2
        assert campaigns[0]["name"] == "Campaign 1"
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_campaign_insights(self, client: MetaAdsClient) -> None:
        """Test getting campaign insights."""
        respx.get(
            "https://graph.facebook.com/v19.0/camp_1/insights"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "impressions": "10000",
                            "clicks": "150",
                            "spend": "500.00",
                            "conversions": "10",
                        }
                    ]
                },
            )
        )
        insights = await client.get_campaign_insights("camp_1")
        assert insights["impressions"] == "10000"
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_campaign(self, client: MetaAdsClient) -> None:
        """Test creating a campaign."""
        respx.post(
            "https://graph.facebook.com/v19.0/act_123456789/campaigns"
        ).mock(
            return_value=httpx.Response(
                200,
                json={"id": "new_camp_123"},
            )
        )
        result = await client.create_campaign(
            name="Test Campaign",
            objective="OUTCOME_SALES",
            daily_budget=100.0,
        )
        assert result["id"] == "new_camp_123"
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_update_campaign_budget(self, client: MetaAdsClient) -> None:
        """Test updating campaign budget."""
        respx.post(
            "https://graph.facebook.com/v19.0/camp_1"
        ).mock(
            return_value=httpx.Response(
                200,
                json={"success": True},
            )
        )
        result = await client.update_campaign_budget("camp_1", 200.0)
        assert result["success"] is True
        await client.close()


# ─── Google Ads Client Tests ────────────────────────────────────────


class TestGoogleAdsClient:
    """Tests for the Google Ads API client."""

    @pytest.fixture
    def client(self) -> GoogleAdsClient:
        """Create a Google Ads client instance."""
        return GoogleAdsClient(
            developer_token="test_dev_token",
            customer_id="1234567890",
        )

    def test_client_initialization(self, client: GoogleAdsClient) -> None:
        """Test client initialization with valid credentials."""
        assert client.developer_token == "test_dev_token"
        assert client.customer_id == "1234567890"

    def test_client_empty_token_raises(self) -> None:
        """Test that empty developer token raises ValueError."""
        with pytest.raises(ValueError, match="Developer token is required"):
            GoogleAdsClient(developer_token="", customer_id="123")

    def test_client_empty_customer_raises(self) -> None:
        """Test that empty customer ID raises ValueError."""
        with pytest.raises(ValueError, match="Customer ID is required"):
            GoogleAdsClient(developer_token="token", customer_id="")

    def test_set_access_token(self, client: GoogleAdsClient) -> None:
        """Test setting access token."""
        client.set_access_token("oauth_token_123")
        assert client._access_token == "oauth_token_123"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_campaigns(self, client: GoogleAdsClient) -> None:
        """Test getting campaigns from Google Ads API."""
        respx.post(
            "https://googleads.googleapis.com/v17/customers/1234567890/googleAds:search"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "campaign": {
                                "id": "camp_1",
                                "name": "Google Campaign 1",
                                "status": "ENABLED",
                            }
                        }
                    ]
                },
            )
        )
        campaigns = await client.get_campaigns()
        assert len(campaigns) == 1
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_campaign_metrics(self, client: GoogleAdsClient) -> None:
        """Test getting campaign metrics."""
        respx.post(
            "https://googleads.googleapis.com/v17/customers/1234567890/googleAds:search"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "campaign": {"id": "camp_1", "name": "Test"},
                            "metrics": {
                                "impressions": 10000,
                                "clicks": 150,
                                "costMicros": 50000000,
                            },
                        }
                    ]
                },
            )
        )
        metrics = await client.get_campaign_metrics()
        assert len(metrics) == 1
        await client.close()


# ─── LinkedIn Ads Client Tests ──────────────────────────────────────


class TestLinkedInAdsClient:
    """Tests for the LinkedIn Ads API client."""

    @pytest.fixture
    def client(self) -> LinkedInAdsClient:
        """Create a LinkedIn Ads client instance."""
        return LinkedInAdsClient(
            access_token="test_li_token",
            ad_account_id="123456789",
        )

    def test_client_initialization(self, client: LinkedInAdsClient) -> None:
        """Test client initialization with valid credentials."""
        assert client.access_token == "test_li_token"
        assert client.ad_account_id == "123456789"

    def test_client_empty_token_raises(self) -> None:
        """Test that empty access token raises ValueError."""
        with pytest.raises(ValueError, match="Access token is required"):
            LinkedInAdsClient(access_token="", ad_account_id="123")

    def test_client_empty_account_raises(self) -> None:
        """Test that empty account ID raises ValueError."""
        with pytest.raises(ValueError, match="Ad account ID is required"):
            LinkedInAdsClient(access_token="token", ad_account_id="")

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_campaigns(self, client: LinkedInAdsClient) -> None:
        """Test getting campaigns from LinkedIn API."""
        respx.get("https://api.linkedin.com/v2/adCampaigns").mock(
            return_value=httpx.Response(
                200,
                json={
                    "elements": [
                        {
                            "id": "li_camp_1",
                            "name": "LinkedIn Campaign 1",
                            "status": "ACTIVE",
                        }
                    ]
                },
            )
        )
        campaigns = await client.get_campaigns()
        assert len(campaigns) == 1
        assert campaigns[0]["name"] == "LinkedIn Campaign 1"
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_campaign_analytics(self, client: LinkedInAdsClient) -> None:
        """Test getting campaign analytics."""
        respx.get("https://api.linkedin.com/v2/adAnalytics").mock(
            return_value=httpx.Response(
                200,
                json={
                    "elements": [
                        {
                            "impressions": 5000,
                            "clicks": 75,
                            "costInLocalCurrency": "250.00",
                        }
                    ]
                },
            )
        )
        analytics = await client.get_campaign_analytics("li_camp_1")
        assert len(analytics) == 1
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_campaign(self, client: LinkedInAdsClient) -> None:
        """Test creating a LinkedIn campaign."""
        respx.post("https://api.linkedin.com/v2/adCampaigns").mock(
            return_value=httpx.Response(
                201,
                json={"id": "new_li_camp_123"},
            )
        )
        result = await client.create_campaign(
            name="Test LI Campaign",
            campaign_group_id="urn:li:sponsoredCampaignGroup:123",
            daily_budget=50.0,
        )
        assert result["id"] == "new_li_camp_123"
        await client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_update_campaign_status(self, client: LinkedInAdsClient) -> None:
        """Test updating campaign status."""
        respx.post(
            "https://api.linkedin.com/v2/adCampaigns/urn:li:sponsoredCampaign:li_camp_1"
        ).mock(
            return_value=httpx.Response(
                200,
                json={"success": True},
            )
        )
        result = await client.update_campaign_status("li_camp_1", "PAUSED")
        assert result["success"] is True
        await client.close()
