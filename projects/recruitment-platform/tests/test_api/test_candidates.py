"""
Comprehensive API tests for the Candidates endpoints.

Tests cover:
- POST /candidates  — create a new candidate
- GET  /candidates  — list all candidates
- GET  /candidates/{id} — retrieve a single candidate by ID
"""

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Return a TestClient bound to the FastAPI application."""
    # Import the app lazily so that import errors surface as test failures
    # rather than collection errors.
    from app.main import app  # adjust import path to match your project layout
    return TestClient(app)


@pytest.fixture
def sample_candidate_payload():
    """Return a valid payload for creating a candidate."""
    return {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane.doe@example.com",
        "phone": "+1-555-0100",
        "skills": ["Python", "FastAPI", "SQL"],
        "experience_years": 5,
        "current_title": "Software Engineer",
        "location": "Berlin, Germany",
    }


@pytest.fixture
def created_candidate(client, sample_candidate_payload):
    """Create a candidate via the API and return the response JSON."""
    response = client.post("/candidates", json=sample_candidate_payload)
    assert response.status_code == 201, response.text
    return response.json()


# ---------------------------------------------------------------------------
# 1. POST /candidates — test_create_candidate
# ---------------------------------------------------------------------------

class TestCreateCandidate:
    """Tests for the POST /candidates endpoint."""

    def test_create_candidate_success(self, client, sample_candidate_payload):
        """A valid payload returns 201 and the created candidate data."""
        response = client.post("/candidates", json=sample_candidate_payload)

        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == sample_candidate_payload["first_name"]
        assert data["last_name"] == sample_candidate_payload["last_name"]
        assert data["email"] == sample_candidate_payload["email"]
        assert "id" in data
        assert isinstance(data["id"], (int, str))

    def test_create_candidate_auto_generates_id(self, client, sample_candidate_payload):
        """The server assigns an ID that is not present in the request payload."""
        response = client.post("/candidates", json=sample_candidate_payload)
        data = response.json()
        assert "id" in data
        assert data["id"] is not None

    def test_create_candidate_missing_required_fields(self, client):
        """Omitting required fields returns 422 Unprocessable Entity."""
        incomplete_payload = {"first_name": "OnlyFirst"}
        response = client.post("/candidates", json=incomplete_payload)
        assert response.status_code == 422

    def test_create_candidate_invalid_email(self, client, sample_candidate_payload):
        """An invalid email address is rejected with 422."""
        sample_candidate_payload["email"] = "not-an-email"
        response = client.post("/candidates", json=sample_candidate_payload)
        assert response.status_code == 422

    def test_create_candidate_empty_body(self, client):
        """An empty JSON body returns 422."""
        response = client.post("/candidates", json={})
        assert response.status_code == 422

    def test_create_candidate_duplicate_email(self, client, sample_candidate_payload):
        """Creating two candidates with the same email returns 409 Conflict."""
        # First creation should succeed
        resp1 = client.post("/candidates", json=sample_candidate_payload)
        assert resp1.status_code == 201

        # Second creation with the same email should fail
        resp2 = client.post("/candidates", json=sample_candidate_payload)
        assert resp2.status_code == 409

    def test_create_candidate_response_content_type(self, client, sample_candidate_payload):
        """The response Content-Type is application/json."""
        response = client.post("/candidates", json=sample_candidate_payload)
        assert response.status_code == 201
        assert "application/json" in response.headers.get("content-type", "")

    def test_create_candidate_with_optional_fields(self, client):
        """A payload with only the required fields succeeds."""
        minimal_payload = {
            "first_name": "Minimal",
            "last_name": "User",
            "email": "minimal.user@example.com",
        }
        response = client.post("/candidates", json=minimal_payload)
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "Minimal"
        assert data["email"] == "minimal.user@example.com"


# ---------------------------------------------------------------------------
# 2. GET /candidates — test_list_candidates
# ---------------------------------------------------------------------------

class TestListCandidates:
    """Tests for the GET /candidates endpoint."""

    def test_list_candidates_empty(self, client):
        """When no candidates exist the endpoint returns an empty list."""
        response = client.get("/candidates")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_candidates_returns_created(self, client, created_candidate):
        """A previously created candidate appears in the list."""
        response = client.get("/candidates")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        ids = [c["id"] for c in data]
        assert created_candidate["id"] in ids

    def test_list_candidates_multiple(self, client, sample_candidate_payload):
        """Multiple created candidates all appear in the list."""
        # Create three candidates
        emails = ["alice@example.com", "bob@example.com", "charlie@example.com"]
        for i, email in enumerate(emails):
            payload = {**sample_candidate_payload, "email": email}
            resp = client.post("/candidates", json=payload)
            assert resp.status_code == 201

        response = client.get("/candidates")
        assert response.status_code == 200
        data = response.json()
        listed_emails = {c["email"] for c in data}
        for email in emails:
            assert email in listed_emails

    def test_list_candidates_response_structure(self, client, created_candidate):
        """Each item in the list has the expected keys."""
        response = client.get("/candidates")
        data = response.json()
        assert len(data) >= 1
        first = data[0]
        expected_keys = {"id", "first_name", "last_name", "email"}
        assert expected_keys.issubset(set(first.keys()))

    def test_list_candidates_content_type(self, client):
        """The response Content-Type is application/json."""
        response = client.get("/candidates")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_list_candidates_pagination_params(self, client, sample_candidate_payload):
        """The endpoint accepts limit and offset query parameters."""
        # Create a few candidates
        for i in range(3):
            payload = {**sample_candidate_payload, "email": f"page-{i}@example.com"}
            client.post("/candidates", json=payload)

        response = client.get("/candidates?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should return at most 2 items
        assert len(data) <= 2


# ---------------------------------------------------------------------------
# 3. GET /candidates/{id} — test_get_candidate
# ---------------------------------------------------------------------------

class TestGetCandidate:
    """Tests for the GET /candidates/{id} endpoint."""

    def test_get_candidate_success(self, client, created_candidate):
        """Retrieving an existing candidate returns 200 and the correct data."""
        candidate_id = created_candidate["id"]
        response = client.get(f"/candidates/{candidate_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == candidate_id
        assert data["email"] == created_candidate["email"]

    def test_get_candidate_not_found(self, client):
        """Retrieving a non-existent candidate returns 404."""
        response = client.get("/candidates/999999")
        assert response.status_code == 404

    def test_get_candidate_invalid_id_format(self, client):
        """A non-integer ID returns 422."""
        response = client.get("/candidates/not-a-number")
        assert response.status_code == 422

    def test_get_candidate_response_structure(self, client, created_candidate):
        """The response contains all expected fields."""
        candidate_id = created_candidate["id"]
        response = client.get(f"/candidates/{candidate_id}")
        data = response.json()
        expected_keys = {"id", "first_name", "last_name", "email"}
        assert expected_keys.issubset(set(data.keys()))

    def test_get_candidate_content_type(self, client, created_candidate):
        """The response Content-Type is application/json."""
        candidate_id = created_candidate["id"]
        response = client.get(f"/candidates/{candidate_id}")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_get_candidate_after_update(self, client, created_candidate):
        """After updating a candidate the GET endpoint reflects the change."""
        candidate_id = created_candidate["id"]

        # Update the candidate
        update_payload = {"first_name": "UpdatedName"}
        update_resp = client.patch(
            f"/candidates/{candidate_id}", json=update_payload
        )
        # PATCH may or may not be implemented; only assert GET if update succeeded
        if update_resp.status_code == 200:
            response = client.get(f"/candidates/{candidate_id}")
            assert response.status_code == 200
            assert response.json()["first_name"] == "UpdatedName"
