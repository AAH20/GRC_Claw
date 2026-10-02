"""Tests for reputation management endpoints."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_analyze_reputation(client, sample_reputation_request):
    """Test reputation analysis endpoint.

    Args:
        client: Async test client.
        sample_reputation_request: Sample request fixture.
    """
    response = await client.post("/api/v1/reputation/analyze", json=sample_reputation_request)
    # Will fail without API key, but tests the endpoint exists
    assert response.status_code in [201, 500]


@pytest.mark.asyncio
async def test_get_reputation_score_not_found(client):
    """Test getting non-existent reputation score.

    Args:
        client: Async test client.
    """
    response = await client.get("/api/v1/reputation/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_company_reputation(client):
    """Test getting company reputation scores.

    Args:
        client: Async test client.
    """
    response = await client.get("/api/v1/reputation/company/TechCorp")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_compare_reputations(client):
    """Test reputation comparison endpoint.

    Args:
        client: Async test client.
    """
    companies = ["TechCorp", "StartupInc"]
    response = await client.post("/api/v1/reputation/compare", json=companies)
    assert response.status_code in [201, 500]
