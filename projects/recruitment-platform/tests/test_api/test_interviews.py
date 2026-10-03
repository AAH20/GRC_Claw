"""
Comprehensive API tests for the Interviews endpoints.

Endpoints under test:
    POST   /interviews              — schedule a new interview
    GET    /interviews              — list interviews
    PATCH  /interviews/{id}         — reschedule an existing interview
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Return a TestClient bound to the FastAPI app."""
    # Import lazily so collection does not fail if the app is not yet wired.
    from app.main import app  # type: ignore

    return TestClient(app)


@pytest.fixture
def sample_interview_payload():
    """Return a minimal valid payload for scheduling an interview."""
    start = datetime.now(timezone.utc) + timedelta(days=1)
    end = start + timedelta(hours=1)
    return {
        "candidate_id": 1,
        "job_id": 1,
        "interviewer_id": 1,
        "scheduled_at": start.isoformat(),
        "duration_minutes": 60,
        "mode": "video",
        "status": "scheduled",
    }


@pytest.fixture
def created_interview(client, sample_interview_payload):
    """Create an interview via the API and return the response JSON."""
    resp = client.post("/interviews", json=sample_interview_payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# 1. test_schedule_interview  —  POST /interviews
# ---------------------------------------------------------------------------

class TestScheduleInterview:
    """Tests for POST /interviews."""

    def test_schedule_interview_success(self, client, sample_interview_payload):
        """A valid payload returns 201 and the created interview object."""
        resp = client.post("/interviews", json=sample_interview_payload)

        assert resp.status_code == 201
        body = resp.json()
        assert "id" in body
        assert body["candidate_id"] == sample_interview_payload["candidate_id"]
        assert body["job_id"] == sample_interview_payload["job_id"]
        assert body["interviewer_id"] == sample_interview_payload["interviewer_id"]
        assert body["mode"] == sample_interview_payload["mode"]
        assert body["status"] == "scheduled"

    def test_schedule_interview_missing_required_fields(self, client):
        """Omitting required fields returns 422."""
        resp = client.post("/interviews", json={})
        assert resp.status_code == 422

    def test_schedule_interview_invalid_datetime(self, client, sample_interview_payload):
        """A non-ISO datetime string returns 422."""
        sample_interview_payload["scheduled_at"] = "not-a-date"
        resp = client.post("/interviews", json=sample_interview_payload)
        assert resp.status_code == 422

    def test_schedule_interview_negative_duration(self, client, sample_interview_payload):
        """A negative duration returns 422."""
        sample_interview_payload["duration_minutes"] = -30
        resp = client.post("/interviews", json=sample_interview_payload)
        assert resp.status_code == 422

    def test_schedule_interview_zero_duration(self, client, sample_interview_payload):
        """A zero duration returns 422."""
        sample_interview_payload["duration_minutes"] = 0
        resp = client.post("/interviews", json=sample_interview_payload)
        assert resp.status_code == 422

    def test_schedule_interview_invalid_mode(self, client, sample_interview_payload):
        """An unrecognised interview mode returns 422."""
        sample_interview_payload["mode"] = "telepathy"
        resp = client.post("/interviews", json=sample_interview_payload)
        assert resp.status_code == 422

    def test_schedule_interview_nonexistent_candidate(self, client, sample_interview_payload):
        """A candidate_id that does not exist returns 404."""
        sample_interview_payload["candidate_id"] = 999_999
        resp = client.post("/interviews", json=sample_interview_payload)
        assert resp.status_code == 404

    def test_schedule_interview_nonexistent_job(self, client, sample_interview_payload):
        """A job_id that does not exist returns 404."""
        sample_interview_payload["job_id"] = 999_999
        resp = client.post("/interviews", json=sample_interview_payload)
        assert resp.status_code == 404

    def test_schedule_interview_nonexistent_interviewer(self, client, sample_interview_payload):
        """An interviewer_id that does not exist returns 404."""
        sample_interview_payload["interviewer_id"] = 999_999
        resp = client.post("/interviews", json=sample_interview_payload)
        assert resp.status_code == 404

    def test_schedule_interview_past_datetime(self, client, sample_interview_payload):
        """Scheduling in the past returns 422."""
        past = datetime.now(timezone.utc) - timedelta(days=1)
        sample_interview_payload["scheduled_at"] = past.isoformat()
        resp = client.post("/interviews", json=sample_interview_payload)
        assert resp.status_code == 422

    def test_schedule_interview_duplicate_conflict(self, client, sample_interview_payload):
        """Double-booking the same interviewer returns 409."""
        # First booking succeeds.
        resp1 = client.post("/interviews", json=sample_interview_payload)
        assert resp1.status_code == 201

        # Second identical booking conflicts.
        resp2 = client.post("/interviews", json=sample_interview_payload)
        assert resp2.status_code == 409

    def test_schedule_interview_response_has_timestamps(self, client, sample_interview_payload):
        """The created interview includes created_at / updated_at fields."""
        resp = client.post("/interviews", json=sample_interview_payload)
        body = resp.json()
        assert "created_at" in body
        assert "updated_at" in body


# ---------------------------------------------------------------------------
# 2. test_list_interviews  —  GET /interviews
# ---------------------------------------------------------------------------

class TestListInterviews:
    """Tests for GET /interviews."""

    def test_list_interviews_empty(self, client):
        """With no interviews the endpoint returns an empty list."""
        resp = client.get("/interviews")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_interviews_returns_created(self, client, created_interview):
        """A previously created interview appears in the list."""
        resp = client.get("/interviews")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) >= 1
        ids = [item["id"] for item in body]
        assert created_interview["id"] in ids

    def test_list_interviews_pagination(self, client, sample_interview_payload):
        """The endpoint honours limit / offset query parameters."""
        # Create three interviews.
        for _ in range(3):
            client.post("/interviews", json=sample_interview_payload)

        resp = client.get("/interviews?limit=2&offset=0")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) <= 2

        resp2 = client.get("/interviews?limit=2&offset=2")
        assert resp2.status_code == 200
        body2 = resp2.json()
        assert len(body2) <= 2

    def test_list_interviews_filter_by_candidate(self, client, sample_interview_payload):
        """Filtering by candidate_id returns only matching interviews."""
        # Create for candidate 1.
        client.post("/interviews", json=sample_interview_payload)

        # Create for candidate 2.
        payload2 = {**sample_interview_payload, "candidate_id": 2}
        client.post("/interviews", json=payload2)

        resp = client.get("/interviews?candidate_id=1")
        assert resp.status_code == 200
        body = resp.json()
        assert all(item["candidate_id"] == 1 for item in body)

    def test_list_interviews_filter_by_job(self, client, sample_interview_payload):
        """Filtering by job_id returns only matching interviews."""
        client.post("/interviews", json=sample_interview_payload)

        payload2 = {**sample_interview_payload, "job_id": 2}
        client.post("/interviews", json=payload2)

        resp = client.get("/interviews?job_id=1")
        assert resp.status_code == 200
        body = resp.json()
        assert all(item["job_id"] == 1 for item in body)

    def test_list_interviews_filter_by_status(self, client, sample_interview_payload):
        """Filtering by status returns only matching interviews."""
        client.post("/interviews", json=sample_interview_payload)

        resp = client.get("/interviews?status=scheduled")
        assert resp.status_code == 200
        body = resp.json()
        assert all(item["status"] == "scheduled" for item in body)

    def test_list_interviews_invalid_limit(self, client):
        """A negative limit returns 422."""
        resp = client.get("/interviews?limit=-1")
        assert resp.status_code == 422

    def test_list_interviews_response_structure(self, client, created_interview):
        """Each item in the list has the expected keys."""
        resp = client.get("/interviews")
        body = resp.json()
        if body:
            item = body[0]
            expected_keys = {"id", "candidate_id", "job_id", "interviewer_id", "scheduled_at", "mode", "status"}
            assert expected_keys.issubset(item.keys())


# ---------------------------------------------------------------------------
# 3. test_reschedule_interview  —  PATCH /interviews/{id}
# ---------------------------------------------------------------------------

class TestRescheduleInterview:
    """Tests for PATCH /interviews/{id}."""

    def test_reschedule_interview_success(self, client, created_interview):
        """Updating the scheduled_at returns 200 and the updated record."""
        interview_id = created_interview["id"]
        new_time = datetime.now(timezone.utc) + timedelta(days=2)
        resp = client.patch(
            f"/interviews/{interview_id}",
            json={"scheduled_at": new_time.isoformat()},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == interview_id
        # The timestamp should reflect the new value (compare ISO strings).
        assert new_time.isoformat()[:19] in body["scheduled_at"].replace("Z", "").replace("+00:00", "")[:19] or \
               body["scheduled_at"] == new_time.isoformat()

    def test_reschedule_interview_not_found(self, client):
        """Patching a non-existent interview returns 404."""
        resp = client.patch(
            "/interviews/999999",
            json={"scheduled_at": datetime.now(timezone.utc).isoformat()},
        )
        assert resp.status_code == 404

    def test_reschedule_interview_invalid_datetime(self, client, created_interview):
        """A non-ISO datetime returns 422."""
        interview_id = created_interview["id"]
        resp = client.patch(
            f"/interviews/{interview_id}",
            json={"scheduled_at": "tomorrow at 3pm"},
        )
        assert resp.status_code == 422

    def test_reschedule_interview_past_datetime(self, client, created_interview):
        """Rescheduling to a past datetime returns 422."""
        interview_id = created_interview["id"]
        past = datetime.now(timezone.utc) - timedelta(days=1)
        resp = client.patch(
            f"/interviews/{interview_id}",
            json={"scheduled_at": past.isoformat()},
        )
        assert resp.status_code == 422

    def test_reschedule_interview_empty_body(self, client, created_interview):
        """An empty PATCH body returns 422 (nothing to update)."""
        interview_id = created_interview["id"]
        resp = client.patch(f"/interviews/{interview_id}", json={})
        assert resp.status_code == 422

    def test_reschedule_interview_change_mode(self, client, created_interview):
        """Changing the interview mode via PATCH succeeds."""
        interview_id = created_interview["id"]
        resp = client.patch(
            f"/interviews/{interview_id}",
            json={"mode": "in_person"},
        )
        assert resp.status_code == 200
        assert resp.json()["mode"] == "in_person"

    def test_reschedule_interview_change_status(self, client, created_interview):
        """Changing the status via PATCH succeeds."""
        interview_id = created_interview["id"]
        resp = client.patch(
            f"/interviews/{interview_id}",
            json={"status": "cancelled"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

    def test_reschedule_interview_change_duration(self, client, created_interview):
        """Changing the duration via PATCH succeeds."""
        interview_id = created_interview["id"]
        resp = client.patch(
            f"/interviews/{interview_id}",
            json={"duration_minutes": 90},
        )
        assert resp.status_code == 200
        assert resp.json()["duration_minutes"] == 90

    def test_reschedule_interview_multiple_fields(self, client, created_interview):
        """Updating several fields at once succeeds."""
        interview_id = created_interview["id"]
        new_time = datetime.now(timezone.utc) + timedelta(days=3)
        resp = client.patch(
            f"/interviews/{interview_id}",
            json={
                "scheduled_at": new_time.isoformat(),
                "duration_minutes": 45,
                "mode": "phone",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["duration_minutes"] == 45
        assert body["mode"] == "phone"

    def test_reschedule_interview_invalid_mode(self, client, created_interview):
        """An invalid mode value returns 422."""
        interview_id = created_interview["id"]
        resp = client.patch(
            f"/interviews/{interview_id}",
            json={"mode": "smoke_signals"},
        )
        assert resp.status_code == 422

    def test_reschedule_interview_negative_duration(self, client, created_interview):
        """A negative duration returns 422."""
        interview_id = created_interview["id"]
        resp = client.patch(
            f"/interviews/{interview_id}",
            json={"duration_minutes": -10},
        )
        assert resp.status_code == 422

    def test_reschedule_interview_idempotent(self, client, created_interview):
        """Applying the same reschedule twice does not error."""
        interview_id = created_interview["id"]
        new_time = datetime.now(timezone.utc) + timedelta(days=5)
        payload = {"scheduled_at": new_time.isoformat()}

        resp1 = client.patch(f"/interviews/{interview_id}", json=payload)
        assert resp1.status_code == 200

        resp2 = client.patch(f"/interviews/{interview_id}", json=payload)
        assert resp2.status_code == 200
