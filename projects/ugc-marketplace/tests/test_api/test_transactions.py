"""
Comprehensive API tests for the Transactions endpoints.

Endpoints under test:
  - POST   /transactions              → create a new transaction
  - GET    /transactions              → list transactions
  - POST   /transactions/{id}/refund  → process a refund for a transaction
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def client() -> TestClient:
    """Return a TestClient bound to the FastAPI app."""
    # Import the app lazily so collection does not fail if the app
    # module is not yet importable in the test environment.
    from app.main import app  # type: ignore[import-not-found]

    return TestClient(app)


@pytest.fixture()
def sample_transaction_payload() -> dict:
    """Return a minimal valid payload for creating a transaction."""
    return {
        "user_id": "user-001",
        "amount": 29.99,
        "currency": "USD",
        "description": "Test purchase",
    }


@pytest.fixture()
def created_transaction(client: TestClient, sample_transaction_payload: dict) -> dict:
    """Create a transaction via the API and return the response body."""
    response = client.post("/transactions", json=sample_transaction_payload)
    assert response.status_code == 201, response.text
    return response.json()


# ---------------------------------------------------------------------------
# 1. POST /transactions  – test_create_transaction
# ---------------------------------------------------------------------------


class TestCreateTransaction:
    """Tests for POST /transactions."""

    def test_create_transaction_success(
        self, client: TestClient, sample_transaction_payload: dict
    ) -> None:
        """A valid payload returns 201 and the created transaction."""
        response = client.post("/transactions", json=sample_transaction_payload)

        assert response.status_code == 201
        body = response.json()
        assert "id" in body
        assert body["user_id"] == sample_transaction_payload["user_id"]
        assert body["amount"] == sample_transaction_payload["amount"]
        assert body["currency"] == sample_transaction_payload["currency"]
        assert body["description"] == sample_transaction_payload["description"]
        assert body["status"] in {"pending", "completed", "created"}

    def test_create_transaction_auto_generates_id(
        self, client: TestClient, sample_transaction_payload: dict
    ) -> None:
        """The server assigns a unique id when none is provided."""
        resp1 = client.post("/transactions", json=sample_transaction_payload)
        resp2 = client.post("/transactions", json=sample_transaction_payload)

        assert resp1.status_code == 201
        assert resp2.status_code == 201
        assert resp1.json()["id"] != resp2.json()["id"]

    def test_create_transaction_missing_required_fields(
        self, client: TestClient
    ) -> None:
        """Omitting required fields returns 422."""
        response = client.post("/transactions", json={})
        assert response.status_code == 422

    def test_create_transaction_invalid_amount_type(
        self, client: TestClient, sample_transaction_payload: dict
    ) -> None:
        """A non-numeric amount returns 422."""
        sample_transaction_payload["amount"] = "not-a-number"
        response = client.post("/transactions", json=sample_transaction_payload)
        assert response.status_code == 422

    def test_create_transaction_negative_amount(
        self, client: TestClient, sample_transaction_payload: dict
    ) -> None:
        """A negative amount is rejected (422 or 400)."""
        sample_transaction_payload["amount"] = -10.00
        response = client.post("/transactions", json=sample_transaction_payload)
        assert response.status_code in {400, 422}

    def test_create_transaction_zero_amount(
        self, client: TestClient, sample_transaction_payload: dict
    ) -> None:
        """A zero amount is rejected (422 or 400)."""
        sample_transaction_payload["amount"] = 0
        response = client.post("/transactions", json=sample_transaction_payload)
        assert response.status_code in {400, 422}

    def test_create_transaction_invalid_currency(
        self, client: TestClient, sample_transaction_payload: dict
    ) -> None:
        """An invalid currency code returns 422."""
        sample_transaction_payload["currency"] = "INVALID"
        response = client.post("/transactions", json=sample_transaction_payload)
        assert response.status_code == 422

    def test_create_transaction_extra_fields_ignored(
        self, client: TestClient, sample_transaction_payload: dict
    ) -> None:
        """Extra fields in the payload are silently ignored."""
        sample_transaction_payload["unknown_field"] = "some-value"
        response = client.post("/transactions", json=sample_transaction_payload)
        assert response.status_code == 201
        assert "unknown_field" not in response.json()

    def test_create_transaction_content_type(
        self, client: TestClient, sample_transaction_payload: dict
    ) -> None:
        """The endpoint accepts application/json."""
        response = client.post(
            "/transactions",
            json=sample_transaction_payload,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 201


# ---------------------------------------------------------------------------
# 2. GET /transactions  – test_list_transactions
# ---------------------------------------------------------------------------


class TestListTransactions:
    """Tests for GET /transactions."""

    def test_list_transactions_empty(self, client: TestClient) -> None:
        """When no transactions exist the list is empty."""
        response = client.get("/transactions")
        assert response.status_code == 200
        body = response.json()
        # The response may be a list or a dict with a data/results key
        if isinstance(body, list):
            assert body == []
        else:
            data = body.get("data") or body.get("results") or body.get("items") or []
            assert data == []

    def test_list_transactions_returns_created(
        self, client: TestClient, created_transaction: dict
    ) -> None:
        """A previously created transaction appears in the list."""
        response = client.get("/transactions")
        assert response.status_code == 200
        body = response.json()

        if isinstance(body, list):
            transactions = body
        else:
            transactions = (
                body.get("data") or body.get("results") or body.get("items") or []
            )

        ids = [t["id"] for t in transactions]
        assert created_transaction["id"] in ids

    def test_list_transactions_pagination(
        self, client: TestClient, sample_transaction_payload: dict
    ) -> None:
        """Pagination parameters are accepted and limit results."""
        # Create several transactions
        for _ in range(5):
            client.post("/transactions", json=sample_transaction_payload)

        response = client.get("/transactions?limit=2")
        assert response.status_code == 200
        body = response.json()

        if isinstance(body, list):
            transactions = body
        else:
            transactions = (
                body.get("data") or body.get("results") or body.get("items") or []
            )

        assert len(transactions) <= 2

    def test_list_transactions_filter_by_user(
        self, client: TestClient, sample_transaction_payload: dict
    ) -> None:
        """Filtering by user_id returns only that user's transactions."""
        sample_transaction_payload["user_id"] = "user-filter-test"
        client.post("/transactions", json=sample_transaction_payload)

        response = client.get("/transactions?user_id=user-filter-test")
        assert response.status_code == 200
        body = response.json()

        if isinstance(body, list):
            transactions = body
        else:
            transactions = (
                body.get("data") or body.get("results") or body.get("items") or []
            )

        for txn in transactions:
            assert txn["user_id"] == "user-filter-test"

    def test_list_transactions_response_structure(
        self, client: TestClient, created_transaction: dict
    ) -> None:
        """Each transaction in the list has the expected fields."""
        response = client.get("/transactions")
        assert response.status_code == 200
        body = response.json()

        if isinstance(body, list):
            transactions = body
        else:
            transactions = (
                body.get("data") or body.get("results") or body.get("items") or []
            )

        assert len(transactions) > 0
        txn = transactions[0]
        expected_keys = {"id", "user_id", "amount", "currency", "status"}
        assert expected_keys.issubset(txn.keys())


# ---------------------------------------------------------------------------
# 3. POST /transactions/{id}/refund  – test_process_refund
# ---------------------------------------------------------------------------


class TestProcessRefund:
    """Tests for POST /transactions/{id}/refund."""

    def test_process_refund_success(
        self, client: TestClient, created_transaction: dict
    ) -> None:
        """Refunding a valid transaction returns 200 and updated status."""
        txn_id = created_transaction["id"]
        response = client.post(f"/transactions/{txn_id}/refund")

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == txn_id
        assert body["status"] in {"refunded", "refund_pending", "cancelled"}

    def test_process_refund_idempotent(
        self, client: TestClient, created_transaction: dict
    ) -> None:
        """Refunding the same transaction twice does not error."""
        txn_id = created_transaction["id"]

        resp1 = client.post(f"/transactions/{txn_id}/refund")
        assert resp1.status_code == 200

        resp2 = client.post(f"/transactions/{txn_id}/refund")
        # Either idempotent success or a conflict — both are acceptable
        assert resp2.status_code in {200, 409}

    def test_process_refund_nonexistent_transaction(
        self, client: TestClient
    ) -> None:
        """Refunding a non-existent transaction returns 404."""
        response = client.post("/transactions/nonexistent-id/refund")
        assert response.status_code == 404

    def test_process_refund_invalid_id_format(
        self, client: TestClient
    ) -> None:
        """An invalid id format returns 422 or 404."""
        response = client.post("/transactions/!/refund")
        assert response.status_code in {404, 422}

    def test_process_refund_already_refunded(
        self, client: TestClient, created_transaction: dict
    ) -> None:
        """Refunding an already-refunded transaction returns 409 or 200."""
        txn_id = created_transaction["id"]

        # First refund
        client.post(f"/transactions/{txn_id}/refund")

        # Second refund
        response = client.post(f"/transactions/{txn_id}/refund")
        assert response.status_code in {200, 409}

    def test_process_refund_with_reason(
        self, client: TestClient, created_transaction: dict
    ) -> None:
        """A refund with a reason body is accepted."""
        txn_id = created_transaction["id"]
        response = client.post(
            f"/transactions/{txn_id}/refund",
            json={"reason": "Customer request"},
        )
        assert response.status_code == 200

    def test_process_refund_updates_transaction_state(
        self, client: TestClient, created_transaction: dict
    ) -> None:
        """After a refund the transaction status is updated."""
        txn_id = created_transaction["id"]

        client.post(f"/transactions/{txn_id}/refund")

        # Fetch the transaction list and verify status changed
        list_resp = client.get("/transactions")
        assert list_resp.status_code == 200
        body = list_resp.json()

        if isinstance(body, list):
            transactions = body
        else:
            transactions = (
                body.get("data") or body.get("results") or body.get("items") or []
            )

        refunded_txn = next(
            (t for t in transactions if t["id"] == txn_id), None
        )
        assert refunded_txn is not None
        assert refunded_txn["status"] in {"refunded", "refund_pending", "cancelled"}
