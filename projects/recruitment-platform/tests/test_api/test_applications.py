"""
Comprehensive API tests for the Applications endpoints.

Tests cover:
- POST /applications — create application
- GET /applications — list applications
- PATCH /applications/{id}/status — update application status
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app, get_db
from app.models import Base


# ── Test Database Setup ───────────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite:///./test_applications.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override the dependency to use the test database."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create fresh tables before each test and drop them after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Provide a TestClient instance."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_application_payload():
    """Return a valid payload for creating an application."""
    return {
        "job_id": 1,
        "candidate_id": 1,
        "cover_letter": "I am excited to apply for this position.",
        "resume_url": "https://example.com/resume.pdf",
    }


@pytest.fixture
def created_application(client, sample_application_payload):
    """Create an application and return the response JSON."""
    response = client.post("/applications", json=sample_application_payload)
    assert response.status_code == 201
    return response.json()


# ── 1. POST /applications — test_create_application ───────────────────────────


class TestCreateApplication:
    """Tests for POST /applications endpoint."""

    def test_create_application_success(self, client, sample_application_payload):
        """Successfully create a new application."""
        response = client.post("/applications", json=sample_application_payload)

        assert response.status_code == 201
        data = response.json()
        assert data["job_id"] == sample_application_payload["job_id"]
        assert data["candidate_id"] == sample_application_payload["candidate_id"]
        assert data["cover_letter"] == sample_application_payload["cover_letter"]
        assert data["resume_url"] == sample_application_payload["resume_url"]
        assert data["status"] == "pending"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_application_without_optional_fields(self, client):
        """Create application with only required fields."""
        payload = {"job_id": 1, "candidate_id": 1}
        response = client.post("/applications", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["job_id"] == 1
        assert data["candidate_id"] == 1
        assert data["status"] == "pending"

    def test_create_application_missing_job_id(self, client):
        """Fail when job_id is missing."""
        payload = {"candidate_id": 1}
        response = client.post("/applications", json=payload)

        assert response.status_code == 422

    def test_create_application_missing_candidate_id(self, client):
        """Fail when candidate_id is missing."""
        payload = {"job_id": 1}
        response = client.post("/applications", json=payload)

        assert response.status_code == 422

    def test_create_application_empty_body(self, client):
        """Fail when request body is empty."""
        response = client.post("/applications", json={})

        assert response.status_code == 422

    def test_create_application_invalid_job_id_type(self, client):
        """Fail when job_id is not an integer."""
        payload = {"job_id": "not-an-int", "candidate_id": 1}
        response = client.post("/applications", json=payload)

        assert response.status_code == 422

    def test_create_application_invalid_candidate_id_type(self, client):
        """Fail when candidate_id is not an integer."""
        payload = {"job_id": 1, "candidate_id": "not-an-int"}
        response = client.post("/applications", json=payload)

        assert response.status_code == 422

    def test_create_application_negative_ids(self, client):
        """Fail when IDs are negative."""
        payload = {"job_id": -1, "candidate_id": -1}
        response = client.post("/applications", json=payload)

        assert response.status_code == 422

    def test_create_application_duplicate(self, client, sample_application_payload):
        """Handle duplicate application (same job + candidate)."""
        # First creation should succeed
        response1 = client.post("/applications", json=sample_application_payload)
        assert response1.status_code == 201

        # Second creation with same data
        response2 = client.post("/applications", json=sample_application_payload)
        # Either 409 Conflict or 201 depending on idempotency design
        assert response2.status_code in (201, 409)

    def test_create_application_with_all_fields(self, client):
        """Create application with every possible field populated."""
        payload = {
            "job_id": 42,
            "candidate_id": 99,
            "cover_letter": "A" * 5000,
            "resume_url": "https://example.com/path/to/resume.pdf",
        }
        response = client.post("/applications", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["job_id"] == 42
        assert data["candidate_id"] == 99
        assert data["cover_letter"] == "A" * 5000
        assert data["resume_url"] == "https://example.com/path/to/resume.pdf"

    def test_create_application_response_content_type(self, client, sample_application_payload):
        """Response should have JSON content type."""
        response = client.post("/applications", json=sample_application_payload)

        assert response.headers["content-type"].startswith("application/json")


# ── 2. GET /applications — test_list_applications ────────────────────────────


class TestListApplications:
    """Tests for GET /applications endpoint."""

    def test_list_applications_empty(self, client):
        """Return empty list when no applications exist."""
        response = client.get("/applications")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_applications_single(self, client, created_application):
        """Return list with one application."""
        response = client.get("/applications")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == created_application["id"]

    def test_list_applications_multiple(self, client, sample_application_payload):
        """Return all created applications."""
        # Create 3 applications
        for i in range(3):
            payload = {**sample_application_payload, "job_id": i + 1}
            client.post("/applications", json=payload)

        response = client.get("/applications")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_list_applications_pagination(self, client, sample_application_payload):
        """Test pagination with skip and limit."""
        # Create 5 applications
        for i in range(5):
            payload = {**sample_application_payload, "job_id": i + 1}
            client.post("/applications", json=payload)

        # Get first 2
        response = client.get("/applications?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Get next 2
        response = client.get("/applications?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Get remaining
        response = client.get("/applications?skip=4&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_list_applications_filter_by_job_id(self, client, sample_application_payload):
        """Filter applications by job_id."""
        # Create applications for different jobs
        for job_id in [1, 2, 3]:
            payload = {**sample_application_payload, "job_id": job_id}
            client.post("/applications", json=payload)

        response = client.get("/applications?job_id=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["job_id"] == 2

    def test_list_applications_filter_by_candidate_id(self, client, sample_application_payload):
        """Filter applications by candidate_id."""
        for candidate_id in [10, 20, 30]:
            payload = {**sample_application_payload, "candidate_id": candidate_id}
            client.post("/applications", json=payload)

        response = client.get("/applications?candidate_id=20")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["candidate_id"] == 20

    def test_list_applications_filter_by_status(self, client, sample_application_payload):
        """Filter applications by status."""
        # Create applications and update their statuses
        for i in range(3):
            payload = {**sample_application_payload, "job_id": i + 1}
            resp = client.post("/applications", json=payload)
            app_id = resp.json()["id"]

            if i == 0:
                client.patch(f"/applications/{app_id}/status", json={"status": "accepted"})
            elif i == 1:
                client.patch(f"/applications/{app_id}/status", json={"status": "rejected"})

        # Filter by accepted
        response = client.get("/applications?status=accepted")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "accepted"

        # Filter by rejected
        response = client.get("/applications?status=rejected")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "rejected"

        # Filter by pending (default)
        response = client.get("/applications?status=pending")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "pending"

    def test_list_applications_response_structure(self, client, created_application):
        """Verify the structure of returned application objects."""
        response = client.get("/applications")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

        app = data[0]
        required_fields = {"id", "job_id", "candidate_id", "status", "created_at", "updated_at"}
        assert required_fields.issubset(set(app.keys()))

    def test_list_applications_ordering(self, client, sample_application_payload):
        """Applications should be returned in a consistent order."""
        for i in range(3):
            payload = {**sample_application_payload, "job_id": i + 1}
            client.post("/applications", json=payload)

        response = client.get("/applications")
        data = response.json()

        # Should be ordered by id (ascending) or created_at
        ids = [app["id"] for app in data]
        assert ids == sorted(ids)


# ── 3. PATCH /applications/{id}/status — test_update_application_status ──────


class TestUpdateApplicationStatus:
    """Tests for PATCH /applications/{id}/status endpoint."""

    def test_update_application_status_success(self, client, created_application):
        """Successfully update an application's status."""
        app_id = created_application["id"]
        new_status = "accepted"

        response = client.patch(
            f"/applications/{app_id}/status",
            json={"status": new_status},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == app_id
        assert data["status"] == new_status
        assert data["updated_at"] is not None

    def test_update_application_status_to_rejected(self, client, created_application):
        """Update status to rejected."""
        app_id = created_application["id"]

        response = client.patch(
            f"/applications/{app_id}/status",
            json={"status": "rejected"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "rejected"

    def test_update_application_status_to_under_review(self, client, created_application):
        """Update status to under_review."""
        app_id = created_application["id"]

        response = client.patch(
            f"/applications/{app_id}/status",
            json={"status": "under_review"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "under_review"

    def test_update_application_status_invalid_status(self, client, created_application):
        """Fail with an invalid status value."""
        app_id = created_application["id"]

        response = client.patch(
            f"/applications/{app_id}/status",
            json={"status": "invalid_status"},
        )

        assert response.status_code == 422

    def test_update_application_status_empty_status(self, client, created_application):
        """Fail with an empty status string."""
        app_id = created_application["id"]

        response = client.patch(
            f"/applications/{app_id}/status",
            json={"status": ""},
        )

        assert response.status_code == 422

    def test_update_application_status_missing_field(self, client, created_application):
        """Fail when status field is missing from request body."""
        app_id = created_application["id"]

        response = client.patch(
            f"/applications/{app_id}/status",
            json={},
        )

        assert response.status_code == 422

    def test_update_application_status_nonexistent_application(self, client):
        """Fail when application ID does not exist."""
        response = client.patch(
            "/applications/99999/status",
            json={"status": "accepted"},
        )

        assert response.status_code == 404

    def test_update_application_status_invalid_id_type(self, client):
        """Fail when application ID is not an integer."""
        response = client.patch(
            "/applications/not-an-id/status",
            json={"status": "accepted"},
        )

        assert response.status_code == 422

    def test_update_application_status_negative_id(self, client):
        """Fail when application ID is negative."""
        response = client.patch(
            "/applications/-1/status",
            json={"status": "accepted"},
        )

        assert response.status_code == 422

    def test_update_application_status_multiple_transitions(self, client, created_application):
        """Test multiple status transitions in sequence."""
        app_id = created_application["id"]

        statuses = ["under_review", "accepted"]
        for status in statuses:
            response = client.patch(
                f"/applications/{app_id}/status",
                json={"status": status},
            )
            assert response.status_code == 200
            assert response.json()["status"] == status

    def test_update_application_status_preserves_other_fields(self, client, created_application):
        """Status update should not modify other fields."""
        app_id = created_application["id"]
        original = created_application

        response = client.patch(
            f"/applications/{app_id}/status",
            json={"status": "accepted"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == original["job_id"]
        assert data["candidate_id"] == original["candidate_id"]
        assert data["cover_letter"] == original["cover_letter"]
        assert data["resume_url"] == original["resume_url"]

    def test_update_application_status_response_content_type(self, client, created_application):
        """Response should have JSON content type."""
        app_id = created_application["id"]

        response = client.patch(
            f"/applications/{app_id}/status",
            json={"status": "accepted"},
        )

        assert response.headers["content-type"].startswith("application/json")

    def test_update_application_status_idempotent(self, client, created_application):
        """Setting the same status twice should succeed both times."""
        app_id = created_application["id"]

        response1 = client.patch(
            f"/applications/{app_id}/status",
            json={"status": "accepted"},
        )
        assert response1.status_code == 200

        response2 = client.patch(
            f"/applications/{app_id}/status",
            json={"status": "accepted"},
        )
        assert response2.status_code == 200
        assert response2.json()["status"] == "accepted"
