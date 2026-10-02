"""Tests for platform integrations."""

from __future__ import annotations

import pytest

from video_marketing.integrations.instagram import (
    InstagramError,
    InstagramIntegration,
    InstagramMediaType,
    InstagramVisibility,
)
from video_marketing.integrations.tiktok import (
    TikTokError,
    TikTokIntegration,
    TikTokVisibility,
)
from video_marketing.integrations.youtube import (
    YouTubeError,
    YouTubeIntegration,
    YouTubeVisibility,
)


# ---------------------------------------------------------------------------
# YouTube Integration Tests
# ---------------------------------------------------------------------------


class TestYouTubeIntegration:
    """Tests for YouTubeIntegration."""

    def test_init_with_api_key(self) -> None:
        yt = YouTubeIntegration(api_key="test-key")
        assert yt.is_configured() is True

    def test_init_with_access_token(self) -> None:
        yt = YouTubeIntegration(access_token="test-token")
        assert yt.is_configured() is True

    def test_init_empty(self) -> None:
        yt = YouTubeIntegration()
        assert yt.is_configured() is False

    @pytest.mark.asyncio
    async def test_upload_no_token_raises(self) -> None:
        yt = YouTubeIntegration()
        with pytest.raises(YouTubeError, match="Access token required"):
            await yt.upload_video(
                file_path="/tmp/test.mp4",
                title="Test Video",
            )

    @pytest.mark.asyncio
    async def test_update_metadata_no_token_raises(self) -> None:
        yt = YouTubeIntegration()
        with pytest.raises(YouTubeError, match="Access token required"):
            await yt.update_video_metadata("video-123", title="New Title")

    @pytest.mark.asyncio
    async def test_get_analytics_no_api_key_raises(self) -> None:
        yt = YouTubeIntegration()
        with pytest.raises(YouTubeError, match="API key required"):
            await yt.get_video_analytics("video-123")

    @pytest.mark.asyncio
    async def test_delete_no_token_raises(self) -> None:
        yt = YouTubeIntegration()
        with pytest.raises(YouTubeError, match="Access token required"):
            await yt.delete_video("video-123")

    @pytest.mark.asyncio
    async def test_add_to_playlist_no_token_raises(self) -> None:
        yt = YouTubeIntegration()
        with pytest.raises(YouTubeError, match="Access token required"):
            await yt.add_to_playlist("video-123", "playlist-456")

    @pytest.mark.asyncio
    async def test_search_no_api_key_raises(self) -> None:
        yt = YouTubeIntegration()
        with pytest.raises(YouTubeError, match="API key required"):
            await yt.search_videos("test query")

    @pytest.mark.asyncio
    async def test_upload_with_token(self) -> None:
        yt = YouTubeIntegration(access_token="test-token")
        result = await yt.upload_video(
            file_path="/tmp/test.mp4",
            title="Test Video",
            description="Test Description",
            tags=["test", "automation"],
        )
        assert result.success is True
        assert result.video_id
        assert result.video_url

    @pytest.mark.asyncio
    async def test_update_metadata_with_token(self) -> None:
        yt = YouTubeIntegration(access_token="test-token")
        video = await yt.update_video_metadata(
            "video-123",
            title="Updated Title",
            description="Updated Description",
        )
        assert video.id == "video-123"
        assert video.title == "Updated Title"

    @pytest.mark.asyncio
    async def test_get_analytics_with_api_key(self) -> None:
        yt = YouTubeIntegration(api_key="test-key")
        video = await yt.get_video_analytics("video-123")
        assert video.id == "video-123"

    @pytest.mark.asyncio
    async def test_delete_with_token(self) -> None:
        yt = YouTubeIntegration(access_token="test-token")
        result = await yt.delete_video("video-123")
        assert result is True

    @pytest.mark.asyncio
    async def test_add_to_playlist_with_token(self) -> None:
        yt = YouTubeIntegration(access_token="test-token")
        result = await yt.add_to_playlist("video-123", "playlist-456")
        assert result is True

    @pytest.mark.asyncio
    async def test_search_with_api_key(self) -> None:
        yt = YouTubeIntegration(api_key="test-key")
        results = await yt.search_videos("test query", max_results=5)
        assert isinstance(results, list)


# ---------------------------------------------------------------------------
# TikTok Integration Tests
# ---------------------------------------------------------------------------


class TestTikTokIntegration:
    """Tests for TikTokIntegration."""

    def test_init_with_token(self) -> None:
        tt = TikTokIntegration(access_token="test-token")
        assert tt.is_configured() is True

    def test_init_empty(self) -> None:
        tt = TikTokIntegration()
        assert tt.is_configured() is False

    @pytest.mark.asyncio
    async def test_upload_no_token_raises(self) -> None:
        tt = TikTokIntegration()
        with pytest.raises(TikTokError, match="Access token required"):
            await tt.upload_video(
                file_path="/tmp/test.mp4",
                title="Test Video",
            )

    @pytest.mark.asyncio
    async def test_get_analytics_no_token_raises(self) -> None:
        tt = TikTokIntegration()
        with pytest.raises(TikTokError, match="Access token required"):
            await tt.get_video_analytics("video-123")

    @pytest.mark.asyncio
    async def test_delete_no_token_raises(self) -> None:
        tt = TikTokIntegration()
        with pytest.raises(TikTokError, match="Access token required"):
            await tt.delete_video("video-123")

    @pytest.mark.asyncio
    async def test_get_user_videos_no_token_raises(self) -> None:
        tt = TikTokIntegration()
        with pytest.raises(TikTokError, match="Access token required"):
            await tt.get_user_videos()

    @pytest.mark.asyncio
    async def test_upload_with_token(self) -> None:
        tt = TikTokIntegration(access_token="test-token")
        result = await tt.upload_video(
            file_path="/tmp/test.mp4",
            title="Test TikTok",
            description="Test Description",
            hashtags=["test", "automation"],
        )
        assert result.success is True
        assert result.video_id
        assert result.share_url

    @pytest.mark.asyncio
    async def test_get_analytics_with_token(self) -> None:
        tt = TikTokIntegration(access_token="test-token")
        video = await tt.get_video_analytics("video-123")
        assert video.id == "video-123"

    @pytest.mark.asyncio
    async def test_delete_with_token(self) -> None:
        tt = TikTokIntegration(access_token="test-token")
        result = await tt.delete_video("video-123")
        assert result is True

    @pytest.mark.asyncio
    async def test_get_user_videos_with_token(self) -> None:
        tt = TikTokIntegration(access_token="test-token")
        videos = await tt.get_user_videos(max_results=10)
        assert isinstance(videos, list)


# ---------------------------------------------------------------------------
# Instagram Integration Tests
# ---------------------------------------------------------------------------


class TestInstagramIntegration:
    """Tests for InstagramIntegration."""

    def test_init_with_token_and_user_id(self) -> None:
        ig = InstagramIntegration(access_token="test-token", user_id="user-123")
        assert ig.is_configured() is True

    def test_init_with_token_only(self) -> None:
        ig = InstagramIntegration(access_token="test-token")
        assert ig.is_configured() is False

    def test_init_empty(self) -> None:
        ig = InstagramIntegration()
        assert ig.is_configured() is False

    @pytest.mark.asyncio
    async def test_upload_reel_no_token_raises(self) -> None:
        ig = InstagramIntegration()
        with pytest.raises(InstagramError, match="Access token required"):
            await ig.upload_reel(
                file_path="/tmp/test.mp4",
                caption="Test Reel",
            )

    @pytest.mark.asyncio
    async def test_upload_story_no_token_raises(self) -> None:
        ig = InstagramIntegration()
        with pytest.raises(InstagramError, match="Access token required"):
            await ig.upload_story(file_path="/tmp/test.mp4")

    @pytest.mark.asyncio
    async def test_get_analytics_no_token_raises(self) -> None:
        ig = InstagramIntegration()
        with pytest.raises(InstagramError, match="Access token required"):
            await ig.get_media_analytics("media-123")

    @pytest.mark.asyncio
    async def test_delete_no_token_raises(self) -> None:
        ig = InstagramIntegration()
        with pytest.raises(InstagramError, match="Access token required"):
            await ig.delete_media("media-123")

    @pytest.mark.asyncio
    async def test_get_user_media_no_token_raises(self) -> None:
        ig = InstagramIntegration()
        with pytest.raises(InstagramError, match="Access token required"):
            await ig.get_user_media()

    @pytest.mark.asyncio
    async def test_refresh_token_no_token_raises(self) -> None:
        ig = InstagramIntegration()
        with pytest.raises(InstagramError, match="No access token"):
            await ig.refresh_access_token()

    @pytest.mark.asyncio
    async def test_upload_reel_with_token(self) -> None:
        ig = InstagramIntegration(access_token="test-token", user_id="user-123")
        result = await ig.upload_reel(
            file_path="/tmp/test.mp4",
            caption="Test Reel #test #automation",
            hashtags=["test", "automation"],
        )
        assert result.success is True
        assert result.media_id
        assert result.permalink

    @pytest.mark.asyncio
    async def test_upload_story_with_token(self) -> None:
        ig = InstagramIntegration(access_token="test-token", user_id="user-123")
        result = await ig.upload_story(
            file_path="/tmp/test.mp4",
            caption="Test Story",
        )
        assert result.success is True
        assert result.media_id

    @pytest.mark.asyncio
    async def test_get_analytics_with_token(self) -> None:
        ig = InstagramIntegration(access_token="test-token", user_id="user-123")
        media = await ig.get_media_analytics("media-123")
        assert media.id == "media-123"

    @pytest.mark.asyncio
    async def test_delete_with_token(self) -> None:
        ig = InstagramIntegration(access_token="test-token", user_id="user-123")
        result = await ig.delete_media("media-123")
        assert result is True

    @pytest.mark.asyncio
    async def test_get_user_media_with_token(self) -> None:
        ig = InstagramIntegration(access_token="test-token", user_id="user-123")
        media = await ig.get_user_media(max_results=10)
        assert isinstance(media, list)

    @pytest.mark.asyncio
    async def test_refresh_token_with_token(self) -> None:
        ig = InstagramIntegration(access_token="test-token", user_id="user-123")
        token = await ig.refresh_access_token()
        assert token == "test-token"
