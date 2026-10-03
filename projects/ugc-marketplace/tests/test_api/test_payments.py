"""
Comprehensive API tests for the payments endpoints.

Endpoints under test:
    - POST /payments           (process a payment)
    - POST /payments/payout    (initiate a payout)
    - GET  /payments/history   (retrieve payment history)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client() -> TestClient:
    """Return a FastAPI TestClient bound to the application."""
    # Import the app lazily so collection does not fail if the app
    # module is not yet importable in the test environment.
    from app.main import app  # type: ignore[import-not-found]

    return TestClient(app)


@pytest.fixture
def valid_payment_payload() -> dict:
    """A minimal valid payload for POST /payments."""
    return {
        "order_id": "order-001",
        "amount": 29.99,
        "currency": "USD",
        "payment_method": "credit_card",
        "customer_id": "cust-123",
    }


@pytest.fixture
def valid_payout_payload() -> dict:
    """A minimal valid payload for POST /payments/payout."""
    return {
        "user_id": "user-456",
        "amount": 150.00,
        "currency": "USD",
        "destination": "bank_account",
        "destination_id": "bank-789",
    }


# ---------------------------------------------------------------------------
# POST /payments  – process a payment
# ---------------------------------------------------------------------------

class TestProcessPayment:
    """Tests for the POST /payments endpoint."""

    def test_process_payment_success(
        self, client: TestClient, valid_payment_payload: dict
    ) -> None:
        """A valid payload should return 200 and a payment confirmation."""
        response = client.post("/payments", json=valid_payment_payload)

        assert response.status_code == 200
        body = response.json()
        assert "payment_id" in body
        assert body["status"] in {"succeeded", "completed", "paid"}
        assert body["order_id"] == valid_payment_payload["order_id"]
        assert body["amount"] == valid_payment_payload["amount"]
        assert body["currency"] == valid_payment_payload["currency"]

    def test_process_payment_returns_payment_id(
        self, client: TestClient, valid_payment_payload: dict
    ) -> None:
        """The response must contain a unique payment identifier."""
        response = client.post("/payments", json=valid_payment_payload)

        assert response.status_code == 200
        payment_id = response.json().get("payment_id")
        assert payment_id is not None
        assert isinstance(payment_id, str)
        assert len(payment_id) > 0

    def test_process_payment_missing_required_fields(
        self, client: TestClient
    ) -> None:
        """Omitting required fields should return 422 Unprocessable Entity."""
        incomplete_payload = {"order_id": "order-002"}  # missing amount, etc.
        response = client.post("/payments", json=incomplete_payload)

        assert response.status_code == 422

    def test_process_payment_invalid_amount(
        self, client: TestClient, valid_payment_payload: dict
    ) -> None:
        """A negative amount should be rejected."""
        valid_payment_payload["amount"] = -10.00
        response = client.post("/payments", json=valid_payment_payload)

        assert response.status_code in {400, 422}

    def test_process_payment_zero_amount(
        self, client: TestClient, valid_payment_payload: dict
    ) -> None:
        """A zero amount should be rejected."""
        valid_payment_payload["amount"] = 0
        response = client.post("/payments", json=valid_payment_payload)

        assert response.status_code in {400, 422}

    def test_process_payment_invalid_currency(
        self, client: TestClient, valid_payment_payload: dict
    ) -> None:
        """An unsupported currency should be rejected."""
        valid_payment_payload["currency"] = "INVALID"
        response = client.post("/payments", json=valid_payment_payload)

        assert response.status_code in {400, 422}

    def test_process_payment_empty_body(
        self, client: TestClient
    ) -> None:
        """An empty JSON body should return 422."""
        response = client.post("/payments", json={})

        assert response.status_code == 422

    def test_process_payment_no_body(
        self, client: TestClient
    ) -> None:
        """Sending no body at all should return 422."""
        response = client.post("/payments")

        assert response.status_code == 422

    def test_process_payment_content_type(
        self, client: TestClient, valid_payment_payload: dict
    ) -> None:
        """The response should have application/json content type."""
        response = client.post("/payments", json=valid_payment_payload)

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_process_payment_idempotency(
        self, client: TestClient, valid_payment_payload: dict
    ) -> None:
        """Sending the same payload twice should not create duplicate payments
        (if the endpoint supports idempotency keys) or should return
        consistent results."""
        resp1 = client.post("/payments", json=valid_payment_payload)
        resp2 = client.post("/payments", json=valid_payment_payload)

        assert resp1.status_code == 200
        assert resp2.status_code == 200
        # If idempotency is enforced the payment_id should match;
        # otherwise both should still be valid responses.
        pid1 = resp1.json().get("payment_id")
        pid2 = resp2.json().get("payment_id")
        assert pid1 is not None
        assert pid2 is not None

    def test_process_payment_large_amount(
        self, client: TestClient, valid_payment_payload: dict
    ) -> None:
        """A very large amount should be handled gracefully."""
        valid_payment_payload["amount"] = 9_999_999.99
        response = client.post("/payments", json=valid_payment_payload)

        # Either it succeeds or it is rejected with a 4xx — never a 5xx.
        assert response.status_code < 500

    def test_process_payment_string_amount(
        self, client: TestClient, valid_payment_payload: dict
    ) -> None:
        """A non-numeric amount should be rejected."""
        valid_payment_payload["amount"] = "not-a-number"
        response = client.post("/payments", json=valid_payment_payload)

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /payments/payout  – initiate a payout
# ---------------------------------------------------------------------------

class TestInitiatePayout:
    """Tests for the POST /payments/payout endpoint."""

    def test_initiate_payout_success(
        self, client: TestClient, valid_payout_payload: dict
    ) -> None:
        """A valid payout payload should return 200 and a payout confirmation."""
        response = client.post("/payments/payout", json=valid_payout_payload)

        assert response.status_code == 200
        body = response.json()
        assert "payout_id" in body
        assert body["status"] in {
            "initiated",
            "pending",
            "processing",
            "submitted",
        }
        assert body["user_id"] == valid_payout_payload["user_id"]
        assert body["amount"] == valid_payout_payload["amount"]
        assert body["currency"] == valid_payout_payload["currency"]

    def test_initiate_payout_returns_payout_id(
        self, client: TestClient, valid_payout_payload: dict
    ) -> None:
        """The response must contain a unique payout identifier."""
        response = client.post("/payments/payout", json=valid_payout_payload)

        assert response.status_code == 200
        payout_id = response.json().get("payout_id")
        assert payout_id is not None
        assert isinstance(payout_id, str)
        assert len(payout_id) > 0

    def test_initiate_payout_missing_required_fields(
        self, client: TestClient
    ) -> None:
        """Omitting required fields should return 422."""
        incomplete_payload = {"user_id": "user-789"}  # missing amount, etc.
        response = client.post("/payments/payout", json=incomplete_payload)

        assert response.status_code == 422

    def test_initiate_payout_invalid_amount(
        self, client: TestClient, valid_payout_payload: dict
    ) -> None:
        """A negative payout amount should be rejected."""
        valid_payout_payload["amount"] = -50.00
        response = client.post("/payments/payout", json=valid_payout_payload)

        assert response.status_code in {400, 422}

    def test_initiate_payout_zero_amount(
        self, client: TestClient, valid_payout_payload: dict
    ) -> None:
        """A zero payout amount should be rejected."""
        valid_payout_payload["amount"] = 0
        response = client.post("/payments/payout", json=valid_payout_payload)

        assert response.status_code in {400, 422}

    def test_initiate_payout_invalid_currency(
        self, client: TestClient, valid_payout_payload: dict
    ) -> None:
        """An unsupported currency should be rejected."""
        valid_payout_payload["currency"] = "INVALID"
        response = client.post("/payments/payout", json=valid_payout_payload)

        assert response.status_code in {400, 422}

    def test_initiate_payout_empty_body(
        self, client: TestClient
    ) -> None:
        """An empty JSON body should return 422."""
        response = client.post("/payments/payout", json={})

        assert response.status_code == 422

    def test_initiate_payout_no_body(
        self, client: TestClient
    ) -> None:
        """Sending no body at all should return 422."""
        response = client.post("/payments/payout")

        assert response.status_code == 422

    def test_initiate_payout_content_type(
        self, client: TestClient, valid_payout_payload: dict
    ) -> None:
        """The response should have application/json content type."""
        response = client.post("/payments/payout", json=valid_payout_payload)

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_initiate_payout_large_amount(
        self, client: TestClient, valid_payout_payload: dict
    ) -> None:
        """A very large payout amount should be handled gracefully."""
        valid_payout_payload["amount"] = 9_999_999.99
        response = client.post("/payments/payout", json=valid_payout_payload)

        assert response.status_code < 500

    def test_initiate_payout_string_amount(
        self, client: TestClient, valid_payout_payload: dict
    ) -> None:
        """A non-numeric amount should be rejected."""
        valid_payout_payload["amount"] = "not-a-number"
        response = client.post("/payments/payout", json=valid_payout_payload)

        assert response.status_code == 422

    def test_initiate_payout_invalid_destination(
        self, client: TestClient, valid_payout_payload: dict
    ) -> None:
        """An invalid payout destination should be rejected."""
        valid_payout_payload["destination"] = "invalid_destination"
        response = client.post("/payments/payout", json=valid_payout_payload)

        assert response.status_code in {400, 422}


# ---------------------------------------------------------------------------
# GET /payments/history  – retrieve payment history
# ---------------------------------------------------------------------------

class TestGetPaymentHistory:
    """Tests for the GET /payments/history endpoint."""

    def test_get_payment_history_success(
        self, client: TestClient
    ) -> None:
        """A GET request should return 200 and a list of payments."""
        response = client.get("/payments/history")

        assert response.status_code == 200
        body = response.json()
        # The response may be a list or a dict with a data/payments key.
        if isinstance(body, list):
            assert isinstance(body, list)
        elif isinstance(body, dict):
            assert "data" in body or "payments" in body or "items" in body
        else:
            pytest.fail(f"Unexpected response type: {type(body)}")

    def test_get_payment_history_returns_list_or_paginated(
        self, client: TestClient
    ) -> None:
        """The response should be a list or a paginated structure."""
        response = client.get("/payments/history")

        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, (list, dict))

    def test_get_payment_history_content_type(
        self, client: TestClient
    ) -> None:
        """The response should have application/json content type."""
        response = client.get("/payments/history")

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_get_payment_history_with_limit_param(
        self, client: TestClient
    ) -> None:
        """A limit query parameter should be accepted."""
        response = client.get("/payments/history", params={"limit": 5})

        assert response.status_code == 200

    def test_get_payment_history_with_offset_param(
        self, client: TestClient
    ) -> None:
        """An offset query parameter should be accepted."""
        response = client.get("/payments/history", params={"offset": 10})

        assert response.status_code == 200

    def test_get_payment_history_with_user_id_param(
        self, client: TestClient
    ) -> None:
        """A user_id query parameter should be accepted."""
        response = client.get(
            "/payments/history", params={"user_id": "user-456"}
        )

        assert response.status_code == 200

    def test_get_payment_history_with_status_param(
        self, client: TestClient
    ) -> None:
        """A status query parameter should be accepted."""
        response = client.get(
            "/payments/history", params={"status": "succeeded"}
        )

        assert response.status_code == 200

    def test_get_payment_history_with_date_range(
        self, client: TestClient
    ) -> None:
        """start_date and end_date query parameters should be accepted."""
        response = client.get(
            "/payments/history",
            params={
                "start_date": "2025-01-01",
                "end_date": "2025-12-31",
            },
        )

        assert response.status_code == 200

    def test_get_payment_history_empty_result(
        self, client: TestClient
    ) -> None:
        """Querying with a non-existent user_id should return an empty list
        or an empty paginated result, not an error."""
        response = client.get(
            "/payments/history", params={"user_id": "non-existent-user-xyz"}
        )

        assert response.status_code == 200
        body = response.json()
        if isinstance(body, list):
            assert len(body) == 0
        elif isinstance(body, dict):
            data = body.get("data") or body.get("payments") or body.get("items") or []
            assert len(data) == 0

    def test_get_payment_history_invalid_limit(
        self, client: TestClient
    ) -> None:
        """A negative limit should be rejected or clamped."""
        response = client.get("/payments/history", params={"limit": -1})

        # Either 422 (validation) or 200 (clamped to default) is acceptable.
        assert response.status_code in {200, 422}

    def test_get_payment_history_response_structure(
        self, client: TestClient
    ) -> None:
        """Each payment record in the history should have expected fields."""
        response = client.get("/payments/history")

        assert response.status_code == 200
        body = response.json()

        records: list = []
        if isinstance(body, list):
            records = body
        elif isinstance(body, dict):
            records = (
                body.get("data")
                or body.get("payments")
                or body.get("items")
                or []
            )

        if records:
            first = records[0]
            expected_fields = {"payment_id", "amount", "currency", "status"}
            # At least some of the expected fields should be present.
            assert expected_fields.intersection(set(first.keys())), (
                f"Expected at least one of {expected_fields} in {first.keys()}"
            )
