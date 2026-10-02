"""Pytest configuration and fixtures."""

from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from moderation_analytics.main import create_app


@pytest.fixture
async def client():
    """Create test client."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
