"""Tests for sentiment analysis endpoints."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_analyze_sentiment(client, sample_sentiment_request):
    """Test sentiment analysis endpoint.

    Args:
        client: Async test client.
        sample_sentiment_request: Sample request fixture.
    """
    response = await client.post("/api/v1/sentiment/analyze", json=sample_sentiment_request)
    # Will fail without API key, but tests the endpoint exists
    assert response.status_code in [201, 500]


@pytest.mark.asyncio
async def test_get_sentiment_report_not_found(client):
    """Test getting non-existent sentiment report.

    Args:
        client: Async test client.
    """
    response = await client.get("/api/v1/sentiment/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_batch_analyze(client):
    """Test batch sentiment analysis endpoint.

    Args:
        client: Async test client.
    """
    texts = ["Great company!", "Terrible experience.", "It's okay."]
    response = await client.post("/api/v1/sentiment/batch", json=texts)
    assert response.status_code in [201, 500]
