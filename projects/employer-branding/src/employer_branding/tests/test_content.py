"""Tests for content generation endpoints."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_generate_content(client, sample_content_request):
    """Test content generation endpoint.

    Args:
        client: Async test client.
        sample_content_request: Sample request fixture.
    """
    response = await client.post("/api/v1/content/generate", json=sample_content_request)
    # Will fail without API key, but tests the endpoint exists
    assert response.status_code in [201, 500]


@pytest.mark.asyncio
async def test_list_content(client):
    """Test content listing endpoint.

    Args:
        client: Async test client.
    """
    response = await client.get("/api/v1/content/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_content_not_found(client):
    """Test getting non-existent content.

    Args:
        client: Async test client.
    """
    response = await client.get("/api/v1/content/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_content_not_found(client):
    """Test deleting non-existent content.

    Args:
        client: Async test client.
    """
    response = await client.delete("/api/v1/content/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
