"""API dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Header, HTTPException

from fraud_detection.config.settings import Settings, get_settings


async def verify_api_key(
    x_api_key: Annotated[str, Header(alias="X-API-Key")],
    settings: Annotated[Settings, None] = None,
) -> str:
    """Verify the API key from request headers.

    Args:
        x_api_key: API key from X-API-Key header.
        settings: Application settings.

    Returns:
        Verified API key.

    Raises:
        HTTPException: If API key is invalid.
    """
    if settings is None:
        settings = get_settings()

    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
