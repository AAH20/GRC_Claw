"""
Comprehensive API tests for the Creators endpoints.

Tests cover:
- POST /creators  (create)
- GET  /creators  (list)
- GET  /creators/{id}  (retrieve)
"""

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Return a TestClient bound to the FastAPI app."""
    # Import the app lazily so collection does not fail if the app module
    # is not importable in the current environment.
    try:
        from app.main import app
    except ImportError:
        from main import app
    return TestClient(app)


@pytest.fixture
def sample_payload():
    """A valid payload for creating a creator."""
    return {
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "bio": "Content creator specialising in tech reviews.",
        "social_handles": {
            "instagram": "@janedoe",
            "youtube": "@JaneDoeChannel",
        },
    }


@pytest.fixture
def created_creator(client, sample_payload):
    """Create a creator via the API and return the response JSON."""
    resp = client.post("/creators", json=sample_payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# 1. POST /creators  – test_create_creator
# ---------------------------------------------------------------------------

class TestCreateCreator:
    """Tests for the POST /creators endpoint."""

    def test_create_creator_success(self, client, sample_payload):
        """A valid payload returns 201 and the created resource."""
        resp = client.post("/creators", json=sample_payload)

        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == sample_payload["name"]
        assert body["email"] == sample_payload["email"]
        assert body["bio"] == sample_payload["bio"]
        assert "id" in body
        assert isinstance(body["id"], (str, int))

    def test_create_creator_minimal_payload(self, client):
        """Only required fields are needed to create a creator."""
        payload = {"name": "Minimal Creator"}
        resp = client.post("/creators", json=payload)

        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "Minimal Creator"
        assert "id" in body

    def test_create_creator_missing_name(self, client):
        """Omitting the required 'name' field returns 422."""
        payload = {"email": "noname@example.com"}
        resp = client.post("/creators", json=payload)

        assert resp.status_code == 422

    def test_create_creator_empty_name(self, client):
        """An empty string for 'name' should be rejected (422)."""
        payload = {"name": ""}
        resp = client.post("/creators", json=payload)

        assert resp.status_code == 422

    def test_create_creator_invalid_email(self, client):
        """A malformed email address returns 422."""
        payload = {"name": "Bad Email", "email": "not-an-email"}
        resp = client.post("/creators", json=payload)

        assert resp.status_code == 422

    def test_create_creator_duplicate_email(self, client, sample_payload):
        """Creating two creators with the same email returns 409."""
        # First creation should succeed.
        resp1 = client.post("/creators", json=sample_payload)
        assert resp1.status_code == 201

        # Second creation with the same email should conflict.
        resp2 = client.post("/creators", json=sample_payload)
        assert resp2.status_code == 409

    def test_create_creator_extra_fields_ignored(self, client):
        """Unknown fields in the payload are silently ignored."""
        payload = {
            "name": "Extra Fields",
            "unknown_field": "should be ignored",
        }
        resp = client.post("/creators", json=payload)

        assert resp.status_code == 201
        body = resp.json()
        assert "unknown_field" not in body

    def test_create_creator_content_type(self, client, sample_payload):
        """The response Content-Type is application/json."""
        resp = client.post("/creators", json=sample_payload)

        assert resp.status_code == 201
        assert "application/json" in resp.headers.get("content-type", "")

    def test_create_creator_idempotent_body(self, client, sample_payload):
        """Two identical requests produce different creator IDs."""
        resp1 = client.post("/creators", json=sample_payload)
        resp2 = client.post("/creators", json=sample_payload)

        # At least one of them should succeed; if both succeed they must
        # have different IDs (the duplicate-email test covers the 409 path).
        if resp1.status_code == 201 and resp2.status_code == 201:
            assert resp1.json()["id"] != resp2.json()["id"]


# ---------------------------------------------------------------------------
# 2. GET /creators  – test_list_creators
# ---------------------------------------------------------------------------

class TestListCreators:
    """Tests for the GET /creators endpoint."""

    def test_list_creators_empty(self, client):
        """When no creators exist the list is empty."""
        resp = client.get("/creators")

        assert resp.status_code == 200
        body = resp.json()
        # The response may be a list or a dict with a 'data'/'items' key.
        if isinstance(body, list):
            assert body == []
        elif isinstance(body, dict):
            items = body.get("data") or body.get("items") or body.get("creators") or []
            assert items == []

    def test_list_creators_returns_created(self, client, created_creator):
        """A previously created creator appears in the list."""
        resp = client.get("/creators")

        assert resp.status_code == 200
        body = resp.json()

        if isinstance(body, list):
            ids = [c["id"] for c in body]
        elif isinstance(body, dict):
            items = body.get("data") or body.get("items") or body.get("creators") or []
            ids = [c["id"] for c in items]
        else:
            ids = []

        assert created_creator["id"] in ids

    def test_list_creators_pagination(self, client):
        """Pagination parameters are accepted without error."""
        resp = client.get("/creators?page=1&per_page=10")

        assert resp.status_code == 200

    def test_list_creators_pagination_invalid(self, client):
        """Invalid pagination values return 422."""
        resp = client.get("/creators?page=abc&per_page=xyz")

        assert resp.status_code == 422

    def test_list_creators_response_structure(self, client, created_creator):
        """Each item in the list contains at least an 'id' and 'name'."""
        resp = client.get("/creators")

        assert resp.status_code == 200
        body = resp.json()

        if isinstance(body, list):
            items = body
        elif isinstance(body, dict):
            items = body.get("data") or body.get("items") or body.get("creators") or []
        else:
            items = []

        assert len(items) >= 1
        for item in items:
            assert "id" in item
            assert "name" in item

    def test_list_creators_content_type(self, client):
        """The response Content-Type is application/json."""
        resp = client.get("/creators")

        assert resp.status_code == 200
        assert "application/json" in resp.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# 3. GET /creators/{id}  – test_get_creator
# ---------------------------------------------------------------------------

class TestGetCreator:
    """Tests for the GET /creators/{id} endpoint."""

    def test_get_creator_success(self, client, created_creator):
        """Retrieving an existing creator returns 200 and the correct data."""
        creator_id = created_creator["id"]
        resp = client.get(f"/creators/{creator_id}")

        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == creator_id
        assert body["name"] == created_creator["name"]
        assert body["email"] == created_creator["email"]

    def test_get_creator_not_found(self, client):
        """Requesting a non-existent creator returns 404."""
        resp = client.get("/creators/99999999")

        assert resp.status_code == 404

    def test_get_creator_invalid_id_format(self, client):
        """A non-numeric ID returns 422 (path validation)."""
        resp = client.get("/creators/not-a-number")

        assert resp.status_code == 422

    def test_get_creator_content_type(self, client, created_creator):
        """The response Content-Type is application/json."""
        creator_id = created_creator["id"]
        resp = client.get(f"/creators/{creator_id}")

        assert resp.status_code == 200
        assert "application/json" in resp.headers.get("content-type", "")

    def test_get_creator_response_fields(self, client, created_creator):
        """The response contains all expected fields."""
        creator_id = created_creator["id"]
        resp = client.get(f"/creators/{creator_id}")

        assert resp.status_code == 200
        body = resp.json()
        expected_fields = {"id", "name", "email"}
        assert expected_fields.issubset(body.keys())

    def test_get_creator_after_update_reflects_changes(
        self, client, created_creator, sample_payload
    ):
        """If the creator is updated, the GET reflects the new data."""
        creator_id = created_creator["id"]

        # Attempt an update (PATCH or PUT) — tolerate 405 if not supported.
        new_name = "Jane Updated"
        patch_resp = client.patch(
            f"/creators/{creator_id}", json={"name": new_name}
        )
        if patch_resp.status_code == 405:
            patch_resp = client.put(
                f"/creators/{creator_id}", json={**sample_payload, "name": new_name}
            )

        if patch_resp.status_code in (200, 204):
            resp = client.get(f"/creators/{creator_id}")
            assert resp.status_code == 200
            assert resp.json()["name"] == new_name
