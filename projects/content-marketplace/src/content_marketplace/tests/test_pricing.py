"""Tests for pricing optimization."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_pricing(client: TestClient) -> None:
    """Test creating a pricing entry."""
    # Create listing first
    listing_resp = client.post(
        "/api/v1/listings",
        json={
            "title": "Priced Content",
            "description": "Content with pricing",
            "seller_id": "seller_1",
            "category": "test",
            "base_price": 50.0,
        },
    )
    listing_id = listing_resp.json()["id"]

    response = client.post(
        "/api/v1/pricing",
        json={
            "listing_id": listing_id,
            "strategy": "dynamic",
            "base_price": 50.0,
            "demand_multiplier": 1.2,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["listing_id"] == listing_id
    assert data["strategy"] == "dynamic"
    assert data["final_price"] == 60.0


def test_optimize_pricing(client: TestClient) -> None:
    """Test optimizing a pricing entry."""
    listing_resp = client.post(
        "/api/v1/listings",
        json={
            "title": "Optimize Me",
            "description": "Content to optimize",
            "seller_id": "seller_1",
            "category": "test",
            "base_price": 100.0,
        },
    )
    listing_id = listing_resp.json()["id"]

    pricing_resp = client.post(
        "/api/v1/pricing",
        json={
            "listing_id": listing_id,
            "strategy": "dynamic",
            "base_price": 100.0,
            "demand_multiplier": 1.0,
        },
    )
    pricing_id = pricing_resp.json()["id"]

    response = client.post(f"/api/v1/pricing/{pricing_id}/optimize")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == pricing_id
