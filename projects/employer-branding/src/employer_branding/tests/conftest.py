"""Pytest configuration and fixtures."""

from __future__ import annotations

import os

os.environ.setdefault("OPENAI_API_KEY", "test-key-for-integration-tests")

import pytest
from httpx import ASGITransport, AsyncClient

from employer_branding.main import create_app


@pytest.fixture
async def client():
    """Create an async test client.

    Yields:
        AsyncClient configured for testing.
    """
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_content_request():
    """Sample content generation request.

    Returns:
        Dictionary with sample request data.
    """
    return {
        "content_type": "job_posting",
        "topic": "Senior Software Engineer",
        "tone": "enthusiastic",
        "language": "en",
        "max_length": 2000,
        "keywords": ["python", "fastapi", "remote"],
        "target_audience": "Senior developers",
    }


@pytest.fixture
def sample_sentiment_request():
    """Sample sentiment analysis request.

    Returns:
        Dictionary with sample request data.
    """
    return {
        "text": "I love working at this company! The culture is amazing and the people are great.",
        "analyze_aspects": True,
        "detect_emotions": True,
    }


@pytest.fixture
def sample_reputation_request():
    """Sample reputation analysis request.

    Returns:
        Dictionary with sample request data.
    """
    return {
        "company_name": "TechCorp",
        "sources": ["glassdoor"],
        "period_days": 90,
        "include_recommendations": True,
    }


@pytest.fixture
def sample_review_request():
    """Sample review fetch request.

    Returns:
        Dictionary with sample request data.
    """
    return {
        "company_name": "TechCorp",
        "source": "glassdoor",
        "limit": 50,
    }


@pytest.fixture
def sample_strategy_request():
    """Sample brand strategy request.

    Returns:
        Dictionary with sample request data.
    """
    return {
        "company_name": "TechCorp",
        "industry": "Technology",
        "company_size": "500-1000",
        "mission": "To build products that make a difference",
        "vision": "To be the most innovative company in our industry",
        "values": ["Innovation", "Integrity", "Collaboration"],
        "target_audience": ["Software Engineers", "Product Managers"],
    }
