"""Tests for the community curation service."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from community_curation.main import create_app


@pytest.fixture
def client() -> TestClient:
    """Create a test client.

    Returns:
        FastAPI test client.
    """
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_curation_request() -> dict:
    """Sample curation request data.

    Returns:
        Dictionary with sample request data.
    """
    return {
        "query": "artificial intelligence",
        "sources": ["reddit", "hacker_news"],
        "limit": 10,
        "time_range": "week",
        "min_quality_score": 0.5,
        "include_trends": True,
        "include_clusters": True,
        "language": "en",
    }
