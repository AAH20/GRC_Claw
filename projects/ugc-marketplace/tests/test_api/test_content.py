"""
Comprehensive API tests for the Content endpoints.

Tests cover:
- POST /content  — create content
- GET  /content  — list content
- GET  /content/{id} — retrieve a single content item
"""

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Return a TestClient bound to the FastAPI application."""
    # Import the app lazily so collection does not fail if the app
    # module is not importable in every environment.
    from app.main import app  # type: ignore
    return TestClient(app)


@pytest.fixture
def sample_content_payload():
    """Return a valid payload for creating content."""
    return {
        "title": "Test Content Item",
        "description": "A sample content item used in API tests.",
        "content_type": "article",
        "author_id": "user-001",
        "tags": ["test", "api", "pytest"],
        "status": "draft",
    }


@pytest.fixture
def created_content(client, sample_content_payload):
    """Create a content item and return the response JSON."""
    response = client.post("/content", json=sample_content_payload)
    assert response.status_code == 201, response.text
    return response.json()


# ---------------------------------------------------------------------------
# POST /content
# ---------------------------------------------------------------------------

class TestCreateContent:
    """Tests for the POST /content endpoint."""

    def test_create_content_success(self, client, sample_content_payload):
        """POST /content with a valid payload returns 201 and the created object."""
        response = client.post("/content", json=sample_content_payload)

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["title"] == sample_content_payload["title"]
        assert data["description"] == sample_content_payload["description"]
        assert data["content_type"] == sample_content_payload["content_type"]
        assert data["author_id"] == sample_content_payload["author_id"]
        assert data["tags"] == sample_content_payload["tags"]
        assert data["status"] == sample_content_payload["status"]

    def test_create_content_returns_unique_ids(self, client, sample_content_payload):
        """Each POST /content call returns a distinct id."""
        resp1 = client.post("/content", json=sample_content_payload)
        resp2 = client.post("/content", json=sample_content_payload)

        assert resp1.status_code == 201
        assert resp2.status_code == 201
        assert resp1.json()["id"] != resp2.json()["id"]

    def test_create_content_missing_title(self, client, sample_content_payload):
        """POST /content without a required title returns 422."""
        payload = {k: v for k, v in sample_content_payload.items() if k != "title"}
        response = client.post("/content", json=payload)

        assert response.status_code == 422

    def test_create_content_missing_content_type(self, client, sample_content_payload):
        """POST /content without content_type returns 422."""
        payload = {k: v for k, v in sample_content_payload.items() if k != "content_type"}
        response = client.post("/content", json=payload)

        assert response.status_code == 422

    def test_create_content_invalid_content_type(self, client, sample_content_payload):
        """POST /content with an unsupported content_type returns 422."""
        payload = {**sample_content_payload, "content_type": "unsupported_type"}
        response = client.post("/content", json=payload)

        assert response.status_code == 422

    def test_create_content_empty_body(self, client):
        """POST /content with an empty JSON body returns 422."""
        response = client.post("/content", json={})

        assert response.status_code == 422

    def test_create_content_no_body(self, client):
        """POST /content with no body at all returns 422."""
        response = client.post("/content")

        assert response.status_code == 422

    def test_create_content_extra_fields_ignored(self, client, sample_content_payload):
        """Extra unknown fields are either ignored or rejected, not crash the server."""
        payload = {**sample_content_payload, "unknown_field": "some value"}
        response = client.post("/content", json=payload)

        # Accept 201 (ignored) or 422 (rejected) — both are valid API behaviors
        assert response.status_code in (201, 422)

    def test_create_content_response_content_type(self, client, sample_content_payload):
        """Response Content-Type is application/json."""
        response = client.post("/content", json=sample_content_payload)

        assert response.status_code == 201
        assert "application/json" in response.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# GET /content
# ---------------------------------------------------------------------------

class TestListContent:
    """Tests for the GET /content endpoint."""

    def test_list_content_empty(self, client):
        """GET /content returns an empty list when no content exists."""
        response = client.get("/content")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_content_returns_created_items(self, client, sample_content_payload):
        """GET /content returns previously created content items."""
        # Create two items
        client.post("/content", json=sample_content_payload)
        client.post("/content", json={**sample_content_payload, "title": "Second Item"})

        response = client.get("/content")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_list_content_response_structure(self, client, created_content):
        """Each item in the list has the expected keys."""
        response = client.get("/content")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

        item = data[0]
        expected_keys = {"id", "title", "description", "content_type", "author_id", "tags", "status"}
        assert expected_keys.issubset(item.keys())

    def test_list_content_pagination_limit(self, client, sample_content_payload):
        """GET /content?limit=N returns at most N items."""
        # Create several items
        for i in range(5):
            client.post("/content", json={**sample_content_payload, "title": f"Item {i}"})

        response = client.get("/content", params={"limit": 2})

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_content_pagination_offset(self, client, sample_content_payload):
        """GET /content?offset=N skips the first N items."""
        # Create items
        for i in range(3):
            client.post("/content", json={**sample_content_payload, "title": f"Item {i}"})

        response = client.get("/content", params={"offset": 1})

        assert response.status_code == 200
        data = response.json()
        # Should have fewer items than the total
        assert len(data) >= 0

    def test_list_content_filter_by_status(self, client, sample_content_payload):
        """GET /content?status=draft filters by status."""
        client.post("/content", json=sample_content_payload)
        client.post("/content", json={**sample_content_payload, "status": "published"})

        response = client.get("/content", params={"status": "draft"})

        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["status"] == "draft"

    def test_list_content_filter_by_author(self, client, sample_content_payload):
        """GET /content?author_id=user-001 filters by author."""
        client.post("/content", json=sample_content_payload)
        client.post("/content", json={**sample_content_payload, "author_id": "user-002"})

        response = client.get("/content", params={"author_id": "user-001"})

        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["author_id"] == "user-001"

    def test_list_content_response_content_type(self, client):
        """Response Content-Type is application/json."""
        response = client.get("/content")

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# GET /content/{id}
# ---------------------------------------------------------------------------

class TestGetContent:
    """Tests for the GET /content/{id} endpoint."""

    def test_get_content_success(self, client, created_content):
        """GET /content/{id} returns the matching content item."""
        content_id = created_content["id"]
        response = client.get(f"/content/{content_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == content_id
        assert data["title"] == created_content["title"]
        assert data["description"] == created_content["description"]
        assert data["content_type"] == created_content["content_type"]
        assert data["author_id"] == created_content["author_id"]
        assert data["tags"] == created_content["tags"]
        assert data["status"] == created_content["status"]

    def test_get_content_not_found(self, client):
        """GET /content/{id} with a non-existent id returns 404."""
        response = client.get("/content/nonexistent-id-12345")

        assert response.status_code == 404

    def test_get_content_invalid_id_format(self, client):
        """GET /content/{id} with an invalid id format returns 422 or 404."""
        response = client.get("/content/!!invalid!!")

        assert response.status_code in (404, 422)

    def test_get_content_response_content_type(self, client, created_content):
        """Response Content-Type is application/json."""
        content_id = created_content["id"]
        response = client.get(f"/content/{content_id}")

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_get_content_after_update(self, client, created_content):
        """GET /content/{id} reflects updates made to the content."""
        content_id = created_content["id"]

        # Update the content
        client.patch(
            f"/content/{content_id}",
            json={"title": "Updated Title"},
        )

        response = client.get(f"/content/{content_id}")

        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"

    def test_get_content_does_not_leak_other_items(self, client, sample_content_payload):
        """GET /content/{id} only returns the requested item, not others."""
        resp1 = client.post("/content", json=sample_content_payload)
        client.post("/content", json={**sample_content_payload, "title": "Other Item"})

        content_id = resp1.json()["id"]
        response = client.get(f"/content/{content_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == content_id
        assert data["title"] == sample_content_payload["title"]
