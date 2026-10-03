"""Comprehensive API tests for the /jobs endpoints."""

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Return a TestClient bound to the FastAPI app."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def sample_job_payload():
    """Return a valid payload for creating a job."""
    return {
        "title": "Senior Backend Engineer",
        "description": "Build and maintain scalable APIs.",
        "location": "Remote",
        "salary_min": 120000,
        "salary_max": 180000,
        "employment_type": "full-time",
        "department": "Engineering",
        "is_active": True,
    }


@pytest.fixture
def created_job(client, sample_job_payload):
    """Create a job via the API and return the response JSON."""
    response = client.post("/jobs", json=sample_job_payload)
    assert response.status_code == 201
    return response.json()


# ---------------------------------------------------------------------------
# 1. test_create_job — POST /jobs
# ---------------------------------------------------------------------------

class TestCreateJob:
    """Tests for POST /jobs."""

    def test_create_job_success(self, client, sample_job_payload):
        """POST /jobs with valid payload returns 201 and the created job."""
        response = client.post("/jobs", json=sample_job_payload)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_job_payload["title"]
        assert data["description"] == sample_job_payload["description"]
        assert data["location"] == sample_job_payload["location"]
        assert data["salary_min"] == sample_job_payload["salary_min"]
        assert data["salary_max"] == sample_job_payload["salary_max"]
        assert data["employment_type"] == sample_job_payload["employment_type"]
        assert data["department"] == sample_job_payload["department"]
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_job_minimal_payload(self, client):
        """POST /jobs with only required fields succeeds."""
        payload = {"title": "DevOps Engineer"}
        response = client.post("/jobs", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "DevOps Engineer"
        assert "id" in data

    def test_create_job_missing_title(self, client):
        """POST /jobs without a title returns 422."""
        payload = {"description": "No title provided"}
        response = client.post("/jobs", json=payload)

        assert response.status_code == 422

    def test_create_job_empty_title(self, client):
        """POST /jobs with an empty title returns 422."""
        payload = {"title": ""}
        response = client.post("/jobs", json=payload)

        assert response.status_code == 422

    def test_create_job_invalid_salary_range(self, client):
        """POST /jobs where salary_min > salary_max returns 422."""
        payload = {
            "title": "QA Engineer",
            "salary_min": 100000,
            "salary_max": 50000,
        }
        response = client.post("/jobs", json=payload)

        assert response.status_code == 422

    def test_create_job_invalid_employment_type(self, client):
        """POST /jobs with an invalid employment_type returns 422."""
        payload = {
            "title": "Designer",
            "employment_type": "internship-fulltime-hybrid",
        }
        response = client.post("/jobs", json=payload)

        assert response.status_code == 422

    def test_create_job_negative_salary(self, client):
        """POST /jobs with a negative salary returns 422."""
        payload = {
            "title": "Support Engineer",
            "salary_min": -1000,
        }
        response = client.post("/jobs", json=payload)

        assert response.status_code == 422

    def test_create_job_extra_fields_ignored(self, client):
        """POST /jobs ignores unknown fields gracefully."""
        payload = {
            "title": "Product Manager",
            "unknown_field": "should be ignored",
        }
        response = client.post("/jobs", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert "unknown_field" not in data

    def test_create_job_content_type(self, client, sample_job_payload):
        """POST /jobs returns JSON content type."""
        response = client.post("/jobs", json=sample_job_payload)

        assert response.headers["content-type"].startswith("application/json")

    def test_create_job_id_is_unique(self, client, sample_job_payload):
        """Two POST /jobs calls produce different IDs."""
        resp1 = client.post("/jobs", json=sample_job_payload)
        resp2 = client.post("/jobs", json=sample_job_payload)

        assert resp1.status_code == 201
        assert resp2.status_code == 201
        assert resp1.json()["id"] != resp2.json()["id"]


# ---------------------------------------------------------------------------
# 2. test_list_jobs — GET /jobs
# ---------------------------------------------------------------------------

class TestListJobs:
    """Tests for GET /jobs."""

    def test_list_jobs_empty(self, client):
        """GET /jobs returns an empty list when no jobs exist."""
        response = client.get("/jobs")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_jobs_returns_created(self, client, created_job):
        """GET /jobs includes a previously created job."""
        response = client.get("/jobs")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        ids = [job["id"] for job in data]
        assert created_job["id"] in ids

    def test_list_jobs_multiple(self, client, sample_job_payload):
        """GET /jobs returns all created jobs."""
        # Create three jobs
        for i in range(3):
            payload = {**sample_job_payload, "title": f"Job {i}"}
            client.post("/jobs", json=payload)

        response = client.get("/jobs")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    def test_list_jobs_pagination_limit(self, client, sample_job_payload):
        """GET /jobs?limit=N respects the limit parameter."""
        for i in range(5):
            payload = {**sample_job_payload, "title": f"Paginated Job {i}"}
            client.post("/jobs", json=payload)

        response = client.get("/jobs", params={"limit": 2})

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_jobs_pagination_offset(self, client, sample_job_payload):
        """GET /jobs?offset=N skips the first N jobs."""
        # Create jobs with known titles
        for i in range(5):
            payload = {**sample_job_payload, "title": f"Offset Job {i}"}
            client.post("/jobs", json=payload)

        response = client.get("/jobs", params={"offset": 3})

        assert response.status_code == 200
        data = response.json()
        # Should have fewer results than the total
        all_response = client.get("/jobs")
        all_data = all_response.json()
        assert len(data) < len(all_data)

    def test_list_jobs_filter_by_department(self, client, sample_job_payload):
        """GET /jobs?department=Engineering filters by department."""
        client.post("/jobs", json={**sample_job_payload, "department": "Engineering"})
        client.post("/jobs", json={**sample_job_payload, "department": "Marketing"})

        response = client.get("/jobs", params={"department": "Engineering"})

        assert response.status_code == 200
        data = response.json()
        for job in data:
            assert job["department"] == "Engineering"

    def test_list_jobs_filter_by_location(self, client, sample_job_payload):
        """GET /jobs?location=Remote filters by location."""
        client.post("/jobs", json={**sample_job_payload, "location": "Remote"})
        client.post("/jobs", json={**sample_job_payload, "location": "New York"})

        response = client.get("/jobs", params={"location": "Remote"})

        assert response.status_code == 200
        data = response.json()
        for job in data:
            assert job["location"] == "Remote"

    def test_list_jobs_filter_by_is_active(self, client, sample_job_payload):
        """GET /jobs?is_active=false returns only inactive jobs."""
        client.post("/jobs", json={**sample_job_payload, "is_active": True})
        client.post("/jobs", json={**sample_job_payload, "is_active": False})

        response = client.get("/jobs", params={"is_active": "false"})

        assert response.status_code == 200
        data = response.json()
        for job in data:
            assert job["is_active"] is False

    def test_list_jobs_response_structure(self, client, created_job):
        """GET /jobs returns objects with expected keys."""
        response = client.get("/jobs")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        job = data[0]
        expected_keys = {"id", "title", "description", "location", "created_at", "updated_at"}
        assert expected_keys.issubset(set(job.keys()))

    def test_list_jobs_content_type(self, client):
        """GET /jobs returns JSON content type."""
        response = client.get("/jobs")

        assert response.headers["content-type"].startswith("application/json")


# ---------------------------------------------------------------------------
# 3. test_get_job — GET /jobs/{id}
# ---------------------------------------------------------------------------

class TestGetJob:
    """Tests for GET /jobs/{id}."""

    def test_get_job_success(self, client, created_job):
        """GET /jobs/{id} returns the correct job."""
        job_id = created_job["id"]
        response = client.get(f"/jobs/{job_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job_id
        assert data["title"] == created_job["title"]
        assert data["description"] == created_job["description"]
        assert data["location"] == created_job["location"]

    def test_get_job_not_found(self, client):
        """GET /jobs/{id} with non-existent ID returns 404."""
        response = client.get("/jobs/999999")

        assert response.status_code == 404

    def test_get_job_invalid_id_format(self, client):
        """GET /jobs/{id} with non-integer ID returns 422."""
        response = client.get("/jobs/not-a-number")

        assert response.status_code == 422

    def test_get_job_negative_id(self, client):
        """GET /jobs/{id} with negative ID returns 404."""
        response = client.get("/jobs/-1")

        assert response.status_code == 404

    def test_get_job_content_type(self, client, created_job):
        """GET /jobs/{id} returns JSON content type."""
        response = client.get(f"/jobs/{created_job['id']}")

        assert response.headers["content-type"].startswith("application/json")

    def test_get_job_all_fields_present(self, client, created_job):
        """GET /jobs/{id} response contains all expected fields."""
        response = client.get(f"/jobs/{created_job['id']}")

        assert response.status_code == 200
        data = response.json()
        expected_keys = {
            "id", "title", "description", "location",
            "salary_min", "salary_max", "employment_type",
            "department", "is_active", "created_at", "updated_at",
        }
        assert expected_keys.issubset(set(data.keys()))

    def test_get_job_after_update_reflects_changes(self, client, created_job):
        """GET /jobs/{id} reflects updates made after creation."""
        job_id = created_job["id"]

        # Update the job
        update_payload = {"title": "Updated Title"}
        client.patch(f"/jobs/{job_id}", json=update_payload)

        # Fetch and verify
        response = client.get(f"/jobs/{job_id}")
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"
