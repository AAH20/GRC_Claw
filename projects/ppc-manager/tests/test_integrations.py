"""Tests for PPC Manager ad platform integrations."""

from __future__ import annotations

import pytest

from ppc_manager.integrations.google_ads import GoogleAdsClient, GoogleAdsConfig
from ppc_manager.integrations.linkedin_ads import LinkedInAdsClient, LinkedInAdsConfig
from ppc_manager.integrations.meta_ads import MetaAdsClient, MetaAdsConfig
from ppc_manager.integrations.tiktok_ads import TikTokAdsClient, TikTokAdsConfig


class TestGoogleAdsIntegration:
    """Tests for the Google Ads integration."""

    @pytest.fixture
    def config(self) -> GoogleAdsConfig:
        """Create a test Google Ads configuration."""
        return GoogleAdsConfig(
            developer_token="test_token",
            client_id="test_client_id",
            client_secret="test_client_secret",
            refresh_token="test_refresh_token",
            login_customer_id="123-456-7890",
        )

    @pytest.fixture
    def client(self, config: GoogleAdsConfig) -> GoogleAdsClient:
        """Create a Google Ads client."""
        return GoogleAdsClient(config)

    def test_config_creation(self, config: GoogleAdsConfig) -> None:
        """Test that config is created correctly."""
        assert config.developer_token == "test_token"
        assert config.login_customer_id == "123-456-7890"

    def test_client_initialization(self, client: GoogleAdsClient) -> None:
        """Test that client initializes correctly."""
        assert client.config.developer_token == "test_token"

    @pytest.mark.asyncio
    async def test_list_campaigns_empty_customer_raises(self, client: GoogleAdsClient) -> None:
        """Test that empty customer ID raises ValueError."""
        with pytest.raises(ValueError, match="Customer ID is required"):
            await client.list_campaigns("")


class TestMetaAdsIntegration:
    """Tests for the Meta Ads integration."""

    @pytest.fixture
    def config(self) -> MetaAdsConfig:
        """Create a test Meta Ads configuration."""
        return MetaAdsConfig(
            access_token="test_token",
            app_id="test_app_id",
            app_secret="test_app_secret",
            ad_account_id="act_123456",
        )

    @pytest.fixture
    def client(self, config: MetaAdsConfig) -> MetaAdsClient:
        """Create a Meta Ads client."""
        return MetaAdsClient(config)

    def test_config_creation(self, config: MetaAdsConfig) -> None:
        """Test that config is created correctly."""
        assert config.access_token == "test_token"
        assert config.ad_account_id == "act_123456"

    def test_client_initialization(self, client: MetaAdsClient) -> None:
        """Test that client initializes correctly."""
        assert client.config.ad_account_id == "act_123456"

    @pytest.mark.asyncio
    async def test_update_campaign_budget_empty_id_raises(self, client: MetaAdsClient) -> None:
        """Test that empty campaign ID raises ValueError."""
        with pytest.raises(ValueError, match="Campaign ID is required"):
            await client.update_campaign_budget("", 1000)


class TestLinkedInAdsIntegration:
    """Tests for the LinkedIn Ads integration."""

    @pytest.fixture
    def config(self) -> LinkedInAdsConfig:
        """Create a test LinkedIn Ads configuration."""
        return LinkedInAdsConfig(
            access_token="test_token",
            ad_account_id="urn:li:sponsoredAccount:12345",
        )

    @pytest.fixture
    def client(self, config: LinkedInAdsConfig) -> LinkedInAdsClient:
        """Create a LinkedIn Ads client."""
        return LinkedInAdsClient(config)

    def test_config_creation(self, config: LinkedInAdsConfig) -> None:
        """Test that config is created correctly."""
        assert config.access_token == "test_token"
        assert config.ad_account_id == "urn:li:sponsoredAccount:12345"

    def test_client_initialization(self, client: LinkedInAdsClient) -> None:
        """Test that client initializes correctly."""
        assert client.config.ad_account_id == "urn:li:sponsoredAccount:12345"

    @pytest.mark.asyncio
    async def test_get_analytics_empty_id_raises(self, client: LinkedInAdsClient) -> None:
        """Test that empty campaign ID raises ValueError."""
        with pytest.raises(ValueError, match="Campaign ID is required"):
            await client.get_campaign_analytics("")


class TestTikTokAdsIntegration:
    """Tests for the TikTok Ads integration."""

    @pytest.fixture
    def config(self) -> TikTokAdsConfig:
        """Create a test TikTok Ads configuration."""
        return TikTokAdsConfig(
            access_token="test_token",
            advertiser_id="123456789",
        )

    @pytest.fixture
    def client(self, config: TikTokAdsConfig) -> TikTokAdsClient:
        """Create a TikTok Ads client."""
        return TikTokAdsClient(config)

    def test_config_creation(self, config: TikTokAdsConfig) -> None:
        """Test that config is created correctly."""
        assert config.access_token == "test_token"
        assert config.advertiser_id == "123456789"

    def test_client_initialization(self, client: TikTokAdsClient) -> None:
        """Test that client initializes correctly."""
        assert client.config.advertiser_id == "123456789"

    @pytest.mark.asyncio
    async def test_get_report_empty_id_raises(self, client: TikTokAdsClient) -> None:
        """Test that empty campaign ID raises ValueError."""
        with pytest.raises(ValueError, match="Campaign ID is required"):
            await client.get_campaign_report("")
