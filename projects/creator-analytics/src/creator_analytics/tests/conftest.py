"""Test configuration and fixtures."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from creator_analytics.main import create_app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create a test client for the FastAPI app.

    Yields:
        AsyncClient configured for testing.
    """
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_audience_data() -> dict:
    """Sample audience data for testing.

    Returns:
        Dictionary with sample audience data.
    """
    return {
        "creator_id": "test-creator-123",
        "total_followers": 50000,
        "active_followers": 35000,
        "age_distribution": {"18_24": 0.35, "25_34": 0.40, "35_44": 0.25},
        "gender_distribution": {"male": 0.55, "female": 0.45},
        "top_countries": {"US": 0.40, "UK": 0.20, "CA": 0.15},
        "growth_rate": 0.05,
        "churn_rate": 0.02,
        "peak_activity_hours": [9, 12, 18, 21],
    }


@pytest.fixture
def sample_content_data() -> dict:
    """Sample content data for testing.

    Returns:
        Dictionary with sample content data.
    """
    return {
        "content_id": "content-456",
        "creator_id": "test-creator-123",
        "content_type": "video",
        "title": "Test Content Title",
        "description": "Test content description",
        "metrics": {
            "views": 10000,
            "likes": 500,
            "comments": 100,
            "shares": 50,
            "saves": 30,
            "engagement_rate": 0.068,
        },
    }


@pytest.fixture
def sample_revenue_data() -> dict:
    """Sample revenue data for testing.

    Returns:
        Dictionary with sample revenue data.
    """
    return {
        "creator_id": "test-creator-123",
        "stream_data": [
            {"stream": "advertising", "amount": 5000, "growth_rate": 0.03},
            {"stream": "sponsorships", "amount": 3000, "growth_rate": 0.05},
            {"stream": "merchandise", "amount": 2000, "growth_rate": 0.02},
        ],
        "total_followers": 50000,
        "engagement_rate": 0.068,
    }


@pytest.fixture
def sample_growth_data() -> dict:
    """Sample growth data for testing.

    Returns:
        Dictionary with sample growth data.
    """
    return {
        "creator_id": "test-creator-123",
        "current_followers": 50000,
        "current_monthly_revenue": 10000.0,
        "monthly_growth_rate": 0.05,
        "revenue_growth_rate": 0.04,
        "prediction_period_months": 12,
        "content_frequency": 4,
        "engagement_rate": 0.068,
        "collaboration_count": 2,
        "platform_diversity": 3,
    }


@pytest.fixture
def sample_engagement_data() -> dict:
    """Sample engagement data for testing.

    Returns:
        Dictionary with sample engagement data.
    """
    return {
        "creator_id": "test-creator-123",
        "total_interactions": 50000,
        "interactions_by_type": {
            "like": 30000,
            "comment": 10000,
            "share": 5000,
            "save": 3000,
            "view": 2000,
        },
        "total_followers": 50000,
        "content_count": 50,
        "repeat_engagers": 15000,
        "total_engagers": 25000,
        "average_engagement_frequency": 3.5,
        "hourly_engagement": {9: 5000, 12: 8000, 18: 10000, 21: 7000},
        "sentiments": {"positive": 35000, "negative": 5000, "neutral": 10000},
        "response_rate": 0.8,
        "growth_rate": 0.05,
    }
