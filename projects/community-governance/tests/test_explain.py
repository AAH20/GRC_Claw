"""Tests for explain endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_explain_action(client: AsyncClient) -> None:
    """Test explaining a governance action."""
    request_data = {
        "explanation_type": "action",
        "target_data": {
            "action_type": "create",
            "status": "approved",
            "reason": "Content meets community guidelines",
            "target_type": "post",
            "target_id": "post_123",
            "actor_id": "user_456",
        },
        "audience": "member",
        "detail_level": "standard",
    }
    response = await client.post("/api/v1/explain", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "details" in data
    assert data["explanation_type"] == "action"


@pytest.mark.asyncio
async def test_explain_rule(client: AsyncClient) -> None:
    """Test explaining a governance rule."""
    request_data = {
        "explanation_type": "rule",
        "target_data": {
            "name": "No Spam",
            "description": "Users must not post spam content",
            "category": "content_moderation",
            "severity": "medium",
        },
        "audience": "member",
        "detail_level": "brief",
    }
    response = await client.post("/api/v1/explain", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert data["explanation_type"] == "rule"


@pytest.mark.asyncio
async def test_explain_dispute(client: AsyncClient) -> None:
    """Test explaining a dispute resolution."""
    request_data = {
        "explanation_type": "dispute",
        "target_data": {
            "title": "Content Removal Dispute",
            "status": "resolved",
            "category": "content_moderation",
            "priority": "medium",
            "resolution": {
                "outcome": "Content reinstated with warning",
                "rationale": "Content was removed in error",
            },
        },
        "audience": "moderator",
        "detail_level": "detailed",
    }
    response = await client.post("/api/v1/explain", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert data["explanation_type"] == "dispute"


@pytest.mark.asyncio
async def test_explain_policy(client: AsyncClient) -> None:
    """Test explaining a governance policy."""
    request_data = {
        "explanation_type": "policy",
        "target_data": {
            "name": "Community Content Policy",
            "description": "Guidelines for acceptable content",
            "status": "active",
            "scope": "global",
            "guidelines": ["Be respectful", "No hate speech"],
        },
        "audience": "admin",
        "detail_level": "detailed",
    }
    response = await client.post("/api/v1/explain", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert data["explanation_type"] == "policy"
