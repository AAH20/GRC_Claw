"""Test configuration and fixtures."""

from __future__ import annotations

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the API.

    Returns:
        FastAPI TestClient instance.
    """
    return TestClient(app)


@pytest.fixture
def sample_campaign_data() -> dict:
    """Provide sample campaign data for testing.

    Returns:
        Dictionary with valid campaign creation data.
    """
    return {
        "name": "Test Campaign",
        "description": "A test campaign for unit testing",
        "goals": ["awareness", "conversion"],
        "total_budget": 10000.0,
        "daily_budget": 333.33,
        "channels": ["search", "social"],
        "duration_days": 30,
        "target_audience": {
            "demographics": {"age_ranges": ["25-34"], "locations": ["US"]},
        },
        "brand_voice": "professional",
        "key_message": "Test message for campaign",
        "industry": "technology",
    }


@pytest_asyncio.fixture
async def async_client():
    """Create an async test client.

    Yields:
        Async test client for async endpoint testing.
    """
    from httpx import AsyncClient, ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
