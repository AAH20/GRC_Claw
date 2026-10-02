"""Tests for moderation queue API endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client: TestClient) -> None:
        """Test health check returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestItemsEndpoints:
    """Tests for item endpoints."""

    def test_create_item(self, client: TestClient) -> None:
        """Test creating a moderation item."""
        response = client.post(
            "/api/v1/items",
            json={
                "content": "Test content for moderation",
                "content_type": "text",
                "author_id": "user123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "Test content for moderation"
        assert data["author_id"] == "user123"
        assert data["status"] == "pending"

    def test_list_items(self, client: TestClient) -> None:
        """Test listing items."""
        response = client.get("/api/v1/items")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_get_item_not_found(self, client: TestClient) -> None:
        """Test getting non-existent item returns 404."""
        response = client.get("/api/v1/items/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    def test_update_item(self, client: TestClient) -> None:
        """Test updating an item."""
        # Create item first
        create_resp = client.post(
            "/api/v1/items",
            json={
                "content": "Test content",
                "author_id": "user123",
            },
        )
        item_id = create_resp.json()["id"]

        # Update it
        response = client.patch(
            f"/api/v1/items/{item_id}",
            json={"status": "in_review"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "in_review"

    def test_delete_item(self, client: TestClient) -> None:
        """Test deleting an item."""
        create_resp = client.post(
            "/api/v1/items",
            json={
                "content": "Test content",
                "author_id": "user123",
            },
        )
        item_id = create_resp.json()["id"]

        response = client.delete(f"/api/v1/items/{item_id}")
        assert response.status_code == 204


class TestQueuesEndpoints:
    """Tests for queue endpoints."""

    def test_create_queue(self, client: TestClient) -> None:
        """Test creating a queue."""
        response = client.post(
            "/api/v1/queues",
            json={
                "name": "Test Queue",
                "description": "A test queue",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Queue"

    def test_list_queues(self, client: TestClient) -> None:
        """Test listing queues."""
        response = client.get("/api/v1/queues")
        assert response.status_code == 200
        data = response.json()
        assert "queues" in data

    def test_get_queue_not_found(self, client: TestClient) -> None:
        """Test getting non-existent queue returns 404."""
        response = client.get("/api/v1/queues/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404


class TestAgentEndpoints:
    """Tests for agent endpoints."""

    def test_score_endpoint(self, client: TestClient) -> None:
        """Test priority scoring endpoint."""
        response = client.post(
            "/api/v1/agents/score",
            json={
                "item_id": "00000000-0000-0000-0000-000000000000",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "agent_name" in data

    def test_auto_moderate_endpoint(self, client: TestClient) -> None:
        """Test auto-moderation endpoint."""
        response = client.post(
            "/api/v1/agents/auto-moderate",
            json={
                "item_id": "00000000-0000-0000-0000-000000000000",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

    def test_route_endpoint(self, client: TestClient) -> None:
        """Test human review routing endpoint."""
        response = client.post(
            "/api/v1/agents/route",
            json={
                "item_id": "00000000-0000-0000-0000-000000000000",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

    def test_optimize_endpoint(self, client: TestClient) -> None:
        """Test queue optimization endpoint."""
        response = client.post(
            "/api/v1/agents/optimize",
            json={},
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

    def test_escalate_endpoint(self, client: TestClient) -> None:
        """Test escalation endpoint."""
        response = client.post(
            "/api/v1/agents/escalate",
            json={
                "item_id": "00000000-0000-0000-0000-000000000000",
                "reason": "Test escalation",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data


class TestReviewEndpoints:
    """Tests for review endpoints."""

    def test_submit_review(self, client: TestClient) -> None:
        """Test submitting a review."""
        response = client.post(
            "/api/v1/reviews",
            json={
                "item_id": "00000000-0000-0000-0000-000000000000",
                "reviewer_id": "reviewer1",
                "decision": "approve",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True


class TestEscalationEndpoints:
    """Tests for escalation endpoints."""

    def test_create_escalation(self, client: TestClient) -> None:
        """Test creating an escalation."""
        response = client.post(
            "/api/v1/escalations",
            json={
                "item_id": "00000000-0000-0000-0000-000000000000",
                "reason": "Test escalation",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["reason"] == "Test escalation"

    def test_list_escalations(self, client: TestClient) -> None:
        """Test listing escalations."""
        response = client.get("/api/v1/escalations")
        assert response.status_code == 200
        data = response.json()
        assert "escalations" in data
