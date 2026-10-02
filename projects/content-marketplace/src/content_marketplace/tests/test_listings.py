"""Tests for listing management."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_create_listing(client: TestClient) -> None:
    """Test creating a new listing."""
    response = client.post(
        "/api/v1/listings",
        json={
            "title": "Test Content",
            "description": "A test content listing",
            "seller_id": "seller_123",
            "category": "digital_art",
            "tags": ["art", "digital"],
            "base_price": 29.99,
            "currency": "USD",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Content"
    assert data["seller_id"] == "seller_123"
    assert data["status"] == "draft"


def test_get_listing(client: TestClient) -> None:
    """Test getting a listing by ID."""
    # Create first
    create_resp = client.post(
        "/api/v1/listings",
        json={
            "title": "Test",
            "description": "Test desc",
            "seller_id": "seller_1",
            "category": "test",
            "base_price": 10.0,
        },
    )
    listing_id = create_resp.json()["id"]

    # Get
    response = client.get(f"/api/v1/listings/{listing_id}")
    assert response.status_code == 200
    assert response.json()["id"] == listing_id


def test_update_listing(client: TestClient) -> None:
    """Test updating a listing."""
    create_resp = client.post(
        "/api/v1/listings",
        json={
            "title": "Original",
            "description": "Original desc",
            "seller_id": "seller_1",
            "category": "test",
            "base_price": 10.0,
        },
    )
    listing_id = create_resp.json()["id"]

    response = client.put(
        f"/api/v1/listings/{listing_id}",
        json={"title": "Updated", "base_price": 15.0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated"
    assert data["base_price"] == 15.0


def test_delete_listing(client: TestClient) -> None:
    """Test deleting a listing."""
    create_resp = client.post(
        "/api/v1/listings",
        json={
            "title": "To Delete",
            "description": "Will be deleted",
            "seller_id": "seller_1",
            "category": "test",
            "base_price": 5.0,
        },
    )
    listing_id = create_resp.json()["id"]

    response = client.delete(f"/api/v1/listings/{listing_id}")
    assert response.status_code == 204

    # Verify deleted
    get_resp = client.get(f"/api/v1/listings/{listing_id}")
    assert get_resp.status_code == 404


def test_list_listings(client: TestClient) -> None:
    """Test listing multiple listings."""
    # Create a few
    for i in range(3):
        client.post(
            "/api/v1/listings",
            json={
                "title": f"Listing {i}",
                "description": f"Description {i}",
                "seller_id": "seller_1",
                "category": "test",
                "base_price": 10.0 + i,
            },
        )

    response = client.get("/api/v1/listings?seller_id=seller_1")
    assert response.status_code == 200
    assert len(response.json()) >= 3
