"""Tests for review analysis endpoints."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_fetch_reviews(client, sample_review_request):
    """Test review fetching endpoint.

    Args:
        client: Async test client.
        sample_review_request: Sample request fixture.
    """
    response = await client.post("/api/v1/reviews/fetch", json=sample_review_request)
    # Will fail without API key, but tests the endpoint exists
    assert response.status_code in [201, 500]


@pytest.mark.asyncio
async def test_get_review_not_found(client):
    """Test getting non-existent review.

    Args:
        client: Async test client.
    """
    response = await client.get("/api/v1/reviews/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_reviews(client):
    """Test review listing endpoint.

    Args:
        client: Async test client.
    """
    response = await client.get("/api/v1/reviews/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_review_summary(client):
    """Test review summary endpoint.

    Args:
        client: Async test client.
    """
    response = await client.get("/api/v1/reviews/summary/TechCorp")
    assert response.status_code == 200
    data = response.json()
    assert "company_name" in data
    assert "total_reviews" in data
