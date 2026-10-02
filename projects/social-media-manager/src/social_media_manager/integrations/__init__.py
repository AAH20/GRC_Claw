"""Platform integration clients."""

from __future__ import annotations

from social_media_manager.integrations.base import BasePlatformClient, PlatformError
from social_media_manager.integrations.facebook import FacebookClient
from social_media_manager.integrations.instagram import InstagramClient
from social_media_manager.integrations.linkedin import LinkedInClient
from social_media_manager.integrations.tiktok import TikTokClient
from social_media_manager.integrations.twitter import TwitterClient

__all__ = [
    "BasePlatformClient",
    "PlatformError",
    "FacebookClient",
    "InstagramClient",
    "LinkedInClient",
    "TikTokClient",
    "TwitterClient",
    "get_client",
]

_CLIENTS: dict[str, type[BasePlatformClient]] = {
    "twitter": TwitterClient,
    "instagram": InstagramClient,
    "facebook": FacebookClient,
    "linkedin": LinkedInClient,
    "tiktok": TikTokClient,
}


def get_client(
    platform: str, access_token: str | None = None, **kwargs: object
) -> BasePlatformClient:
    """Instantiate the client for a named platform.

    Args:
        platform: Platform identifier (e.g. ``"twitter"``).
        access_token: Optional credential for the client.
        **kwargs: Extra arguments forwarded to the client constructor.

    Returns:
        A configured :class:`BasePlatformClient` subclass instance.

    Raises:
        ValueError: If the platform is not supported.
    """
    key = platform.lower()
    if key not in _CLIENTS:
        raise ValueError(
            f"Unsupported platform '{platform}'. Valid: {', '.join(sorted(_CLIENTS))}"
        )
    return _CLIENTS[key](access_token, **kwargs)  # type: ignore[arg-type]
