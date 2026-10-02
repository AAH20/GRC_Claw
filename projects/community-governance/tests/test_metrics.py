"""Tests for metrics endpoint."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_metrics_endpoint(client: AsyncClient) -> None:
    """Test the Prometheus metrics endpoint."""
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert isinstance(response.text, str)
