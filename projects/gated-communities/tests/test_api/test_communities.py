"""Comprehensive API tests for the Communities endpoints.

Tests cover:
- POST /communities  (test_create_community)
- GET  /communities  (test_list_communities)
- GET  /communities/{id}  (test_get_community)
"""

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Return a TestClient bound to the FastAPI app."""
    # Import the app from the main application module.
    # Adjust the import path to match your project layout.
    from app.main import app  # type: ignore
    return TestClient(app)


@pytest.fixture
def sample_community_payload():
    """Return a valid payload for creating a community."""
    return {
        "name": "Test Community",
        "description": "A community created during automated testing.",
        "is_private": False,
    }


@pytest.fixture
def created_community(client, sample_community_payload):
    """Create a community via the API and return the response JSON."""
    response = client.post("/communities", json=sample_community_payload)
    assert response.status_code == 201, response.text
    return response.json()


# ---------------------------------------------------------------------------
# 1. test_create_community  —  POST /communities
# ---------------------------------------------------------------------------

class TestCreateCommunity:
    """Tests for the POST /communities endpoint."""

    def test_create_community_success(self, client, sample_community_payload):
        """A valid payload should create a community and return 201."""
        response = client.post("/communities", json=sample_community_payload)

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == sample_community_payload["name"]
        assert data["description"] == sample_community_payload["description"]
        assert data["is_private"] == sample_community_payload["is_private"]

    def test_create_community_returns_unique_id(
        self, client, sample_community_payload
    ):
        """Two communities created with the same payload get different IDs."""
        resp1 = client.post("/communities", json=sample_community_payload)
        resp2 = client.post("/communities", json=sample_community_payload)

        assert resp1.status_code == 201
        assert resp2.status_code == 201
        assert resp1.json()["id"] != resp2.json()["id"]

    def test_create_community_missing_name(self, client):
        """Omitting the required 'name' field should return 422."""
        payload = {"description": "No name provided", "is_private": False}
        response = client.post("/communities", json=payload)

        assert response.status_code == 422

    def test_create_community_empty_name(self, client):
        """An empty 'name' string should be rejected (422 or 400)."""
        payload = {"name": "", "description": "Empty name", "is_private": False}
        response = client.post("/communities", json=payload)

        assert response.status_code in (400, 422)

    def test_create_community_extra_fields_ignored(
        self, client, sample_community_payload
    ):
        """Unknown fields should not cause a 500 — they are either ignored or rejected gracefully."""
        payload = {**sample_community_payload, "unknown_field": "value"}
        response = client.post("/communities", json=payload)

        # FastAPI/Pydantic ignores extra fields by default (201),
        # but some configurations reject them (422). Either is acceptable.
        assert response.status_code in (201, 422)

    def test_create_community_content_type(self, client, sample_community_payload):
        """The response should have application/json content type."""
        response = client.post("/communities", json=sample_community_payload)

        assert response.status_code == 201
        assert "application/json" in response.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# 2. test_list_communities  —  GET /communities
# ---------------------------------------------------------------------------

class TestListCommunities:
    """Tests for the GET /communities endpoint."""

    def test_list_communities_empty(self, client):
        """When no communities exist the endpoint should return an empty list with 200."""
        response = client.get("/communities")

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_communities_returns_created(
        self, client, sample_community_payload
    ):
        """After creating a community it should appear in the list."""
        client.post("/communities", json=sample_community_payload)

        response = client.get("/communities")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        names = [c["name"] for c in data]
        assert sample_community_payload["name"] in names

    def test_list_communities_structure(self, client, created_community):
        """Each item in the list should contain the expected keys."""
        response = client.get("/communities")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

        first = data[0]
        expected_keys = {"id", "name", "description", "is_private"}
        assert expected_keys.issubset(set(first.keys()))

    def test_list_communities_pagination(self, client):
        """If pagination params are accepted they should not cause errors."""
        response = client.get("/communities?skip=0&limit=10")

        # Should either succeed (200) or return 422 if pagination is not supported.
        assert response.status_code in (200, 422)

    def test_list_communities_content_type(self, client):
        """The response should have application/json content type."""
        response = client.get("/communities")

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# 3. test_get_community  —  GET /communities/{id}
# ---------------------------------------------------------------------------

class TestGetCommunity:
    """Tests for the GET /communities/{id} endpoint."""

    def test_get_community_success(self, client, created_community):
        """Fetching an existing community by ID should return 200 and the correct data."""
        community_id = created_community["id"]
        response = client.get(f"/communities/{community_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == community_id
        assert data["name"] == created_community["name"]
        assert data["description"] == created_community["description"]

    def test_get_community_not_found(self, client):
        """Requesting a non-existent community ID should return 404."""
        response = client.get("/communities/999999")

        assert response.status_code == 404

    def test_get_community_invalid_id(self, client):
        """A non-integer ID should return 422 (validation error)."""
        response = client.get("/communities/not-a-number")

        assert response.status_code == 422

    def test_get_community_content_type(self, client, created_community):
        """The response should have application/json content type."""
        community_id = created_community["id"]
        response = client.get(f"/communities/{community_id}")

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_get_community_structure(self, client, created_community):
        """The returned community object should contain the expected keys."""
        community_id = created_community["id"]
        response = client.get(f"/communities/{community_id}")

        assert response.status_code == 200
        data = response.json()
        expected_keys = {"id", "name", "description", "is_private"}
        assert expected_keys.issubset(set(data.keys()))
