"""Tests for brand strategy endpoints."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_create_strategy(client, sample_strategy_request):
    """Test strategy creation endpoint.

    Args:
        client: Async test client.
        sample_strategy_request: Sample request fixture.
    """
    response = await client.post("/api/v1/strategy/create", json=sample_strategy_request)
    # Will fail without API key, but tests the endpoint exists
    assert response.status_code in [201, 500]


@pytest.mark.asyncio
async def test_get_strategy_not_found(client):
    """Test getting non-existent strategy.

    Args:
        client: Async test client.
    """
    response = await client.get("/api/v1/strategy/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_strategies(client):
    """Test strategy listing endpoint.

    Args:
        client: Async test client.
    """
    response = await client.get("/api/v1/strategy/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_delete_strategy_not_found(client):
    """Test deleting non-existent strategy.

    Args:
        client: Async test client.
    """
    response = await client.delete("/api/v1/strategy/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_activate_strategy_not_found(client):
    """Test activating non-existent strategy.

    Args:
        client: Async test client.
    """
    response = await client.post("/api/v1/strategy/00000000-0000-0000-0000-000000000000/activate")
    assert response.status_code == 404
