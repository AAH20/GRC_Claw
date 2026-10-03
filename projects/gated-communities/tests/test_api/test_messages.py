"""Comprehensive API tests for the Messages endpoints.

Tests cover:
    - POST   /messages            (send a message)
    - GET    /messages            (list messages)
    - PATCH  /messages/{id}/read  (mark a message as read)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client() -> TestClient:
    """Return a TestClient bound to the FastAPI app.

    Replace the import below with the actual application factory used in the
    gated-communities project (e.g. ``from app.main import app``).
    """
    # from app.main import app
    # return TestClient(app)
    raise NotImplementedError(
        "Wire this fixture to the real FastAPI app instance."
    )


@pytest.fixture()
def sample_message_payload() -> dict:
    """Return a valid payload for POST /messages."""
    return {
        "content": "Hello, this is a test message!",
        "sender_id": "user-001",
        "recipient_id": "user-002",
        "community_id": "community-001",
    }


@pytest.fixture()
def created_message(client: TestClient, sample_message_payload: dict) -> dict:
    """Create a message via the API and return the response body."""
    response = client.post("/messages", json=sample_message_payload)
    assert response.status_code == 201, response.text
    return response.json()


# ---------------------------------------------------------------------------
# 1. test_send_message  —  POST /messages
# ---------------------------------------------------------------------------

class TestSendMessage:
    """Tests for the POST /messages endpoint."""

    def test_send_message_success(
        self, client: TestClient, sample_message_payload: dict
    ):
        """A valid payload returns 201 and the created message."""
        response = client.post("/messages", json=sample_message_payload)

        assert response.status_code == 201
        body = response.json()
        assert "id" in body
        assert body["content"] == sample_message_payload["content"]
        assert body["sender_id"] == sample_message_payload["sender_id"]
        assert body["recipient_id"] == sample_message_payload["recipient_id"]
        assert body["community_id"] == sample_message_payload["community_id"]
        assert body.get("read") is False or body.get("is_read") is False

    def test_send_message_missing_content(self, client: TestClient):
        """Missing required 'content' field returns 422."""
        payload = {
            "sender_id": "user-001",
            "recipient_id": "user-002",
            "community_id": "community-001",
        }
        response = client.post("/messages", json=payload)

        assert response.status_code == 422

    def test_send_message_empty_content(self, client: TestClient):
        """Empty string content is rejected (422 or 400)."""
        payload = {
            "content": "",
            "sender_id": "user-001",
            "recipient_id": "user-002",
            "community_id": "community-001",
        }
        response = client.post("/messages", json=payload)

        assert response.status_code in (400, 422)

    def test_send_message_missing_sender(self, client: TestClient):
        """Missing sender_id returns 422."""
        payload = {
            "content": "Test",
            "recipient_id": "user-002",
            "community_id": "community-001",
        }
        response = client.post("/messages", json=payload)

        assert response.status_code == 422

    def test_send_message_missing_recipient(self, client: TestClient):
        """Missing recipient_id returns 422."""
        payload = {
            "content": "Test",
            "sender_id": "user-001",
            "community_id": "community-001",
        }
        response = client.post("/messages", json=payload)

        assert response.status_code == 422

    def test_send_message_missing_community(self, client: TestClient):
        """Missing community_id returns 422."""
        payload = {
            "content": "Test",
            "sender_id": "user-001",
            "recipient_id": "user-002",
        }
        response = client.post("/messages", json=payload)

        assert response.status_code == 422

    def test_send_message_invalid_content_type(self, client: TestClient):
        """Non-string content returns 422."""
        payload = {
            "content": 12345,
            "sender_id": "user-001",
            "recipient_id": "user-002",
            "community_id": "community-001",
        }
        response = client.post("/messages", json=payload)

        assert response.status_code == 422

    def test_send_message_extra_fields_ignored(
        self, client: TestClient, sample_message_payload: dict
    ):
        """Extra unknown fields are either ignored or rejected gracefully."""
        payload = {**sample_message_payload, "unknown_field": "value"}
        response = client.post("/messages", json=payload)

        # Most FastAPI configs either ignore extras (201) or reject them (422)
        assert response.status_code in (201, 422)

    def test_send_message_content_too_long(self, client: TestClient):
        """Excessively long content is rejected."""
        payload = {
            "content": "A" * 10_001,
            "sender_id": "user-001",
            "recipient_id": "user-002",
            "community_id": "community-001",
        }
        response = client.post("/messages", json=payload)

        assert response.status_code in (400, 413, 422)

    def test_send_message_returns_unique_ids(
        self, client: TestClient, sample_message_payload: dict
    ):
        """Each POST returns a distinct message ID."""
        ids: set[str] = set()
        for _ in range(5):
            resp = client.post("/messages", json=sample_message_payload)
            assert resp.status_code == 201
            ids.add(resp.json()["id"])
        assert len(ids) == 5


# ---------------------------------------------------------------------------
# 2. test_get_messages  —  GET /messages
# ---------------------------------------------------------------------------

class TestGetMessages:
    """Tests for the GET /messages endpoint."""

    def test_get_messages_empty(self, client: TestClient):
        """When no messages exist, the endpoint returns an empty list."""
        response = client.get("/messages")

        assert response.status_code == 200
        assert response.json() == []

    def test_get_messages_returns_created(
        self, client: TestClient, created_message: dict
    ):
        """After creating a message, GET /messages includes it."""
        response = client.get("/messages")

        assert response.status_code == 200
        messages = response.json()
        assert isinstance(messages, list)
        assert len(messages) >= 1
        ids = [m["id"] for m in messages]
        assert created_message["id"] in ids

    def test_get_messages_filter_by_community(
        self, client: TestClient, sample_message_payload: dict
    ):
        """Filtering by community_id returns only matching messages."""
        # Create two messages in different communities
        client.post("/messages", json=sample_message_payload)
        other_payload = {**sample_message_payload, "community_id": "community-999"}
        client.post("/messages", json=other_payload)

        response = client.get(
            "/messages", params={"community_id": "community-001"}
        )
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) >= 1
        for msg in messages:
            assert msg["community_id"] == "community-001"

    def test_get_messages_filter_by_sender(
        self, client: TestClient, sample_message_payload: dict
    ):
        """Filtering by sender_id returns only matching messages."""
        client.post("/messages", json=sample_message_payload)
        other_payload = {**sample_message_payload, "sender_id": "user-999"}
        client.post("/messages", json=other_payload)

        response = client.get(
            "/messages", params={"sender_id": "user-001"}
        )
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) >= 1
        for msg in messages:
            assert msg["sender_id"] == "user-001"

    def test_get_messages_filter_by_recipient(
        self, client: TestClient, sample_message_payload: dict
    ):
        """Filtering by recipient_id returns only matching messages."""
        client.post("/messages", json=sample_message_payload)
        other_payload = {**sample_message_payload, "recipient_id": "user-999"}
        client.post("/messages", json=other_payload)

        response = client.get(
            "/messages", params={"recipient_id": "user-002"}
        )
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) >= 1
        for msg in messages:
            assert msg["recipient_id"] == "user-002"

    def test_get_messages_pagination_limit(
        self, client: TestClient, sample_message_payload: dict
    ):
        """The 'limit' query parameter caps the number of results."""
        for _ in range(10):
            client.post("/messages", json=sample_message_payload)

        response = client.get("/messages", params={"limit": 3})
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) <= 3

    def test_get_messages_pagination_offset(
        self, client: TestClient, sample_message_payload: dict
    ):
        """The 'offset' query parameter skips the first N results."""
        for _ in range(5):
            client.post("/messages", json=sample_message_payload)

        response = client.get("/messages", params={"offset": 2, "limit": 10})
        assert response.status_code == 200
        messages = response.json()
        # Should have at most 3 messages (5 - 2)
        assert len(messages) <= 3

    def test_get_messages_response_structure(
        self, client: TestClient, created_message: dict
    ):
        """Each message in the list has the expected keys."""
        response = client.get("/messages")
        assert response.status_code == 200
        messages = response.json()
        assert len(messages) >= 1

        first = messages[0]
        expected_keys = {"id", "content", "sender_id", "recipient_id", "community_id"}
        assert expected_keys.issubset(first.keys())

    def test_get_messages_ordered_by_created_at_desc(
        self, client: TestClient, sample_message_payload: dict
    ):
        """Messages are returned newest-first by default."""
        for i in range(3):
            payload = {**sample_message_payload, "content": f"Message {i}"}
            client.post("/messages", json=payload)

        response = client.get("/messages", params={"limit": 3})
        assert response.status_code == 200
        messages = response.json()
        if len(messages) >= 2:
            # Newest first — first item should be the last created
            assert messages[0]["content"] == "Message 2"


# ---------------------------------------------------------------------------
# 3. test_mark_as_read  —  PATCH /messages/{id}/read
# ---------------------------------------------------------------------------

class TestMarkAsRead:
    """Tests for the PATCH /messages/{message_id}/read endpoint."""

    def test_mark_as_read_success(
        self, client: TestClient, created_message: dict
    ):
        """Marking an existing message as read returns 200 and updated body."""
        message_id = created_message["id"]
        response = client.patch(f"/messages/{message_id}/read")

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == message_id
        assert body.get("read") is True or body.get("is_read") is True

    def test_mark_as_read_idempotent(
        self, client: TestClient, created_message: dict
    ):
        """Calling PATCH /read twice does not error."""
        message_id = created_message["id"]

        resp1 = client.patch(f"/messages/{message_id}/read")
        assert resp1.status_code == 200

        resp2 = client.patch(f"/messages/{message_id}/read")
        assert resp2.status_code == 200
        body = resp2.json()
        assert body.get("read") is True or body.get("is_read") is True

    def test_mark_as_read_nonexistent_message(self, client: TestClient):
        """Marking a non-existent message returns 404."""
        response = client.patch("/messages/nonexistent-id-12345/read")

        assert response.status_code == 404

    def test_mark_as_read_invalid_id_format(self, client: TestClient):
        """An invalid ID format returns 422 or 404."""
        response = client.patch("/messages/!!invalid!!/read")

        assert response.status_code in (404, 422)

    def test_mark_as_read_updates_get_messages(
        self, client: TestClient, created_message: dict
    ):
        """After marking as read, GET /messages reflects the change."""
        message_id = created_message["id"]

        # Before: should be unread
        resp_before = client.get("/messages", params={"limit": 100})
        before_msg = next(
            (m for m in resp_before.json() if m["id"] == message_id), None
        )
        assert before_msg is not None
        assert before_msg.get("read") is False or before_msg.get("is_read") is False

        # Mark as read
        client.patch(f"/messages/{message_id}/read")

        # After: should be read
        resp_after = client.get("/messages", params={"limit": 100})
        after_msg = next(
            (m for m in resp_after.json() if m["id"] == message_id), None
        )
        assert after_msg is not None
        assert after_msg.get("read") is True or after_msg.get("is_read") is True

    def test_mark_as_read_does_not_affect_other_messages(
        self, client: TestClient, sample_message_payload: dict
    ):
        """Marking one message as read leaves others unchanged."""
        # Create two messages
        resp1 = client.post("/messages", json=sample_message_payload)
        resp2 = client.post("/messages", json=sample_message_payload)
        msg1_id = resp1.json()["id"]
        msg2_id = resp2.json()["id"]

        # Mark only the first as read
        client.patch(f"/messages/{msg1_id}/read")

        # Verify second is still unread
        resp = client.get("/messages", params={"limit": 100})
        messages = resp.json()
        msg2 = next((m for m in messages if m["id"] == msg2_id), None)
        assert msg2 is not None
        assert msg2.get("read") is False or msg2.get("is_read") is False

    def test_mark_as_read_empty_id(self, client: TestClient):
        """An empty message ID returns 404 or 422."""
        response = client.patch("/messages//read")

        assert response.status_code in (404, 422)
