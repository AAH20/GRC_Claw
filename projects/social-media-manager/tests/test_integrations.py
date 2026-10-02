"""Tests for platform integration clients."""

from __future__ import annotations

import httpx
import pytest
import respx

from social_media_manager.integrations import (
    FacebookClient,
    InstagramClient,
    LinkedInClient,
    PlatformError,
    TikTokClient,
    TwitterClient,
    get_client,
)


class TestClientFactory:
    """Client registry behaviour."""

    def test_returns_correct_client(self) -> None:
        assert isinstance(get_client("twitter", "token"), TwitterClient)
        assert isinstance(get_client("instagram", "token"), InstagramClient)
        assert isinstance(get_client("facebook", "token"), FacebookClient)
        assert isinstance(get_client("linkedin", "token"), LinkedInClient)
        assert isinstance(get_client("tiktok", "token"), TikTokClient)

    def test_unknown_platform_raises(self) -> None:
        with pytest.raises(ValueError, match="Unsupported platform"):
            get_client("myspace")

    def test_is_configured_flag(self) -> None:
        assert get_client("twitter", "token").is_configured is True
        assert get_client("twitter", None).is_configured is False


class TestTwitterClient:
    """Twitter/X client behaviour."""

    @respx.mock
    async def test_post_tweet(self) -> None:
        respx.post("https://api.twitter.com/2/tweets").mock(
            return_value=httpx.Response(201, json={"data": {"id": "123"}})
        )
        result = await TwitterClient("token").post_tweet("hello world")
        assert result["data"]["id"] == "123"

    async def test_rejects_long_tweet(self) -> None:
        with pytest.raises(ValueError, match="280"):
            await TwitterClient("token").post_tweet("x" * 281)

    async def test_rejects_empty_tweet(self) -> None:
        with pytest.raises(ValueError):
            await TwitterClient("token").post_tweet("   ")

    @respx.mock
    async def test_client_error_raises_platform_error(self) -> None:
        respx.get("https://api.twitter.com/2/users/by/username/ghost").mock(
            return_value=httpx.Response(404, text="not found")
        )
        with pytest.raises(PlatformError) as exc:
            await TwitterClient("token").get_user("ghost")
        assert exc.value.status == 404


class TestInstagramClient:
    """Instagram client behaviour."""

    @respx.mock
    async def test_create_media_container(self) -> None:
        respx.post("https://graph.instagram.com/v18.0/123/media").mock(
            return_value=httpx.Response(200, json={"id": "container-1"})
        )
        result = await InstagramClient("token").create_media_container(
            "123", "https://img.example.com/a.jpg", "caption"
        )
        assert result["id"] == "container-1"

    async def test_requires_user_and_image(self) -> None:
        with pytest.raises(ValueError):
            await InstagramClient("token").create_media_container("", "url")


class TestFacebookClient:
    """Facebook client behaviour."""

    @respx.mock
    async def test_create_post(self) -> None:
        respx.post("https://graph.facebook.com/v18.0/page1/feed").mock(
            return_value=httpx.Response(200, json={"id": "post-1"})
        )
        result = await FacebookClient("token").create_post("page1", "hello")
        assert result["id"] == "post-1"

    async def test_requires_message(self) -> None:
        with pytest.raises(ValueError):
            await FacebookClient("token").create_post("page1", "  ")

    async def test_invalid_period_rejected(self) -> None:
        with pytest.raises(ValueError, match="period"):
            await FacebookClient("token").get_page_insights("page1", period="hour")


class TestLinkedInClient:
    """LinkedIn client behaviour."""

    @respx.mock
    async def test_create_post(self) -> None:
        respx.post("https://api.linkedin.com/v2/ugcPosts").mock(
            return_value=httpx.Response(201, json={"id": "urn:li:share:1"})
        )
        result = await LinkedInClient("token").create_post(
            "urn:li:person:abc", "hello linkedin"
        )
        assert result["id"] == "urn:li:share:1"

    async def test_invalid_visibility(self) -> None:
        with pytest.raises(ValueError, match="visibility"):
            await LinkedInClient("token").create_post("urn:li:person:abc", "hi", "SECRET")


class TestTikTokClient:
    """TikTok client behaviour."""

    @respx.mock
    async def test_get_user_info(self) -> None:
        respx.get("https://open-api.tiktok.com/user/info/").mock(
            return_value=httpx.Response(200, json={"data": {"display_name": "creator"}})
        )
        result = await TikTokClient("token").get_user_info("open-id-1")
        assert result["data"]["display_name"] == "creator"

    async def test_video_metrics_requires_ids(self) -> None:
        with pytest.raises(ValueError):
            await TikTokClient("token").get_video_metrics([])

    @respx.mock
    async def test_retries_on_server_error(self) -> None:
        route = respx.post("https://open-api.tiktok.com/video/query/")
        route.side_effect = [
            httpx.Response(503, text="unavailable"),
            httpx.Response(200, json={"data": {"videos": []}}),
        ]
        result = await TikTokClient("token", max_retries=2).get_video_metrics(["v1"])
        assert result["data"]["videos"] == []

    @respx.mock
    async def test_exhausted_retries_raise(self) -> None:
        respx.post("https://open-api.tiktok.com/video/query/").mock(
            return_value=httpx.Response(500, text="error")
        )
        with pytest.raises(PlatformError):
            await TikTokClient("token", max_retries=2).get_video_metrics(["v1"])
