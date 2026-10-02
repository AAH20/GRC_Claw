"""Tests for platform integrations."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from creator_analytics.integrations import (
    YouTubeIntegration,
    InstagramIntegration,
    TikTokIntegration,
    TwitterIntegration,
)


@pytest.mark.asyncio
async def test_youtube_integration() -> None:
    """Test YouTube integration."""
    integration = YouTubeIntegration(api_key="test-key")
    assert integration.base_url == "https://www.googleapis.com/youtube/v3"
    await integration.close()


@pytest.mark.asyncio
async def test_instagram_integration() -> None:
    """Test Instagram integration."""
    integration = InstagramIntegration(access_token="test-token")
    assert integration.base_url == "https://graph.instagram.com"
    await integration.close()


@pytest.mark.asyncio
async def test_tiktok_integration() -> None:
    """Test TikTok integration."""
    integration = TikTokIntegration(access_token="test-token")
    assert integration.base_url == "https://open-api.tiktok.com"
    await integration.close()


@pytest.mark.asyncio
async def test_twitter_integration() -> None:
    """Test Twitter integration."""
    integration = TwitterIntegration(bearer_token="test-token")
    assert integration.base_url == "https://api.twitter.com/2"
    await integration.close()


@pytest.mark.asyncio
async def test_youtube_fetch_analytics() -> None:
    """Test YouTube fetch analytics."""
    integration = YouTubeIntegration(api_key="test-key")

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "items": [{
            "snippet": {"title": "Test Channel"},
            "statistics": {
                "subscriberCount": "10000",
                "videoCount": "100",
                "viewCount": "500000",
            },
        }]
    }
    mock_response.raise_for_status = MagicMock()

    with patch.object(integration, "_get_client") as mock_client:
        mock_client.return_value = AsyncMock()
        mock_client.return_value.get = AsyncMock(return_value=mock_response)

        result = await integration.fetch_analytics("channel-123")
        assert result["platform"] == "youtube"
        assert result["subscriber_count"] == 10000

    await integration.close()
