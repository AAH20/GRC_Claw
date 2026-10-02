"""Test configuration and fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from fraud_detection.main import create_app


@pytest.fixture
def client() -> TestClient:
    """Create a test client.

    Returns:
        TestClient instance.
    """
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_transaction() -> dict:
    """Create a sample transaction for testing.

    Returns:
        Sample transaction dictionary.
    """
    return {
        "transaction_id": "txn-001",
        "account_id": "acc-001",
        "amount": 150.0,
        "currency": "USD",
        "transaction_type": "debit",
        "merchant_id": "merch-001",
        "merchant_category": "retail",
        "location": "New York, NY",
        "device_id": "dev-001",
        "ip_address": "192.168.1.1",
    }
