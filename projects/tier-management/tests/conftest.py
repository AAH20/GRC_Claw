"""Test configuration and fixtures."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from tier_management.main import app


@pytest.fixture
async def client() -> AsyncClient:
    """Create an async test client for the FastAPI app.

    Returns:
        AsyncClient configured for testing.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_tier_data() -> dict:
    """Sample tier data for testing.

    Returns:
        Dictionary with sample tier fields.
    """
    return {
        "name": "Gold Tier",
        "level": "gold",
        "status": "active",
        "description": "Gold membership tier",
        "requirements": {"min_activity_score": 70},
        "benefits": ["priority_support", "exclusive_access"],
        "max_members": 1000,
        "monthly_fee": 29.99,
    }


@pytest.fixture
def sample_evaluation_data() -> dict:
    """Sample evaluation data for testing.

    Returns:
        Dictionary with sample evaluation fields.
    """
    from uuid import uuid4

    return {
        "member_id": str(uuid4()),
        "current_tier_id": str(uuid4()),
        "target_tier_id": str(uuid4()),
        "member_metrics": {
            "activity_score": 80.0,
            "contribution_score": 75.0,
            "engagement_score": 85.0,
            "tenure_score": 60.0,
        },
    }


@pytest.fixture
def sample_access_check_data() -> dict:
    """Sample access check data for testing.

    Returns:
        Dictionary with sample access check fields.
    """
    from uuid import uuid4

    return {
        "member_id": str(uuid4()),
        "resource": "premium_forum",
        "action": "read",
        "context": {"time_of_day": "business_hours"},
    }
