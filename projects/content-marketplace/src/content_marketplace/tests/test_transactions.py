"""Tests for transaction processing."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_transaction(client: TestClient) -> None:
    """Test creating a transaction."""
    listing_resp = client.post(
        "/api/v1/listings",
        json={
            "title": "Buyable Content",
            "description": "Content for purchase",
            "seller_id": "seller_1",
            "category": "test",
            "base_price": 25.0,
        },
    )
    listing_id = listing_resp.json()["id"]

    response = client.post(
        "/api/v1/transactions",
        json={
            "listing_id": listing_id,
            "buyer_id": "buyer_1",
            "seller_id": "seller_1",
            "amount": 25.0,
            "payment_method": "card_123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["amount"] == 25.0
    assert data["platform_fee"] == 2.5


def test_process_transaction(client: TestClient) -> None:
    """Test processing a transaction."""
    listing_resp = client.post(
        "/api/v1/listings",
        json={
            "title": "Process Me",
            "description": "Content to process",
            "seller_id": "seller_1",
            "category": "test",
            "base_price": 30.0,
        },
    )
    listing_id = listing_resp.json()["id"]

    tx_resp = client.post(
        "/api/v1/transactions",
        json={
            "listing_id": listing_id,
            "buyer_id": "buyer_1",
            "seller_id": "seller_1",
            "amount": 30.0,
            "payment_method": "card_123",
        },
    )
    tx_id = tx_resp.json()["id"]

    response = client.post(f"/api/v1/transactions/{tx_id}/process")
    assert response.status_code == 200
    assert response.json()["status"] == "processing"


def test_complete_transaction(client: TestClient) -> None:
    """Test completing a transaction."""
    listing_resp = client.post(
        "/api/v1/listings",
        json={
            "title": "Complete Me",
            "description": "Content to complete",
            "seller_id": "seller_1",
            "category": "test",
            "base_price": 40.0,
        },
    )
    listing_id = listing_resp.json()["id"]

    tx_resp = client.post(
        "/api/v1/transactions",
        json={
            "listing_id": listing_id,
            "buyer_id": "buyer_1",
            "seller_id": "seller_1",
            "amount": 40.0,
            "payment_method": "card_123",
        },
    )
    tx_id = tx_resp.json()["id"]

    # Process first
    client.post(f"/api/v1/transactions/{tx_id}/process")

    # Complete
    response = client.post(f"/api/v1/transactions/{tx_id}/complete")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
