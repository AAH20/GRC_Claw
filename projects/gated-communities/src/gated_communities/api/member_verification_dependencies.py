"""API dependencies for member verification service."""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Request
from member_verification.config.settings import Settings, get_settings


async def verify_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings),
) -> str:
    """Verify the API key provided in the request header.

    Args:
        x_api_key: API key from request header.
        settings: Application settings.

    Returns:
        The verified API key.

    Raises:
        HTTPException: If the API key is missing or invalid.
    """
    # In production, validate against a secure store
    # For development, accept any non-empty key
    if settings.environment == "production" and not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    # TODO: Implement proper API key validation against database
    return x_api_key or "dev-key"


async def rate_limit_check(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    """Check if the request is within rate limits.

    Args:
        request: The incoming request.
        settings: Application settings.

    Raises:
        HTTPException: If rate limit is exceeded.
    """
    # TODO: Implement proper rate limiting with Redis
    # For now, this is a placeholder
    pass


def get_request_id(request: Request) -> str:
    """Extract or generate request ID.

    Args:
        request: The incoming request.

    Returns:
        Request ID string.
    """
    return request.headers.get("X-Request-ID", "")
