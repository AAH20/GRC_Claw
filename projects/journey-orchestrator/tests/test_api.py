"""Tests for API endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from journey_orchestrator.main import app


@pytest.fixture
async def client() -> AsyncClient:
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestJourneysEndpoint:
    """Tests for the journeys API endpoints."""

    @pytest.mark.asyncio
    async def test_create_journey(self, client: AsyncClient) -> None:
        payload = {
            "business_goal": "Increase retention",
            "target_audience": "New users",
            "channels": ["email"],
        }
        response = await client.post("/api/v1/journeys", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["business_goal"] == "Increase retention"
        assert data["status"] == "draft"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_journey_validation_error(self, client: AsyncClient) -> None:
        payload = {"business_goal": "", "target_audience": "Users"}
        response = await client.post("/api/v1/journeys", json=payload)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_list_journeys(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/journeys")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_journey_not_found(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/journeys/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_activate_journey(self, client: AsyncClient) -> None:
        # Create a journey first
        create_resp = await client.post(
            "/api/v1/journeys",
            json={"business_goal": "Test", "target_audience": "Test users"},
        )
        journey_id = create_resp.json()["id"]

        response = await client.post(f"/api/v1/journeys/{journey_id}/activate")
        assert response.status_code == 200
        assert response.json()["status"] == "active"


class TestEventsEndpoint:
    """Tests for the events API endpoints."""

    @pytest.mark.asyncio
    async def test_ingest_event(self, client: AsyncClient) -> None:
        payload = {
            "customer_id": "cust_123",
            "event_type": "page_view",
            "properties": {"page": "/home"},
        }
        response = await client.post("/api/v1/events", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "accepted"
        assert "event_id" in data

    @pytest.mark.asyncio
    async def test_ingest_event_validation_error(self, client: AsyncClient) -> None:
        payload = {"customer_id": "", "event_type": "test"}
        response = await client.post("/api/v1/events", json=payload)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_customer_events(self, client: AsyncClient) -> None:
        # Ingest an event first
        await client.post(
            "/api/v1/events",
            json={"customer_id": "cust_456", "event_type": "click"},
        )
        response = await client.get("/api/v1/events/cust_456")
        assert response.status_code == 200
        events = response.json()
        assert len(events) >= 1


class TestSegmentsEndpoint:
    """Tests for the segments API endpoints."""

    @pytest.mark.asyncio
    async def test_create_segment(self, client: AsyncClient) -> None:
        payload = {
            "name": "High Value Customers",
            "description": "Customers with LTV > $1000",
            "criteria": {"min_ltv": 1000},
        }
        response = await client.post("/api/v1/segments", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "High Value Customers"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_list_segments(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/segments")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_get_segment_not_found(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/segments/nonexistent")
        assert response.status_code == 404
