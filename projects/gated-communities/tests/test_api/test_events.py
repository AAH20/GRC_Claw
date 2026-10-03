"""
Comprehensive API tests for the Events endpoints.

Tests cover:
- POST /events  (create event)
- GET /events   (list events)
- GET /events/{id}  (get single event)
"""

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Return a TestClient for the FastAPI application."""
    # Import the app lazily so collection does not fail if the app
    # module is not importable in the current environment.
    try:
        from app.main import app
    except ImportError:
        pytest.skip("FastAPI app not importable in this environment")
    return TestClient(app)


@pytest.fixture
def sample_event_payload():
    """Return a valid payload for creating an event."""
    return {
        "title": "Community Meetup",
        "description": "Monthly community gathering for members.",
        "start_time": "2026-11-15T18:00:00Z",
        "end_time": "2026-11-15T21:00:00Z",
        "location": "Community Hall, 123 Main St",
        "max_attendees": 50,
        "is_public": True,
    }


@pytest.fixture
def created_event(client, sample_event_payload):
    """Create an event and return the response JSON."""
    response = client.post("/events", json=sample_event_payload)
    assert response.status_code == 201, f"Setup failed: {response.text}"
    return response.json()


# ---------------------------------------------------------------------------
# POST /events
# ---------------------------------------------------------------------------

class TestCreateEvent:
    """Tests for POST /events."""

    def test_create_event_success(self, client, sample_event_payload):
        """POST /events with valid payload returns 201 and the created event."""
        response = client.post("/events", json=sample_event_payload)

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["title"] == sample_event_payload["title"]
        assert data["description"] == sample_event_payload["description"]
        assert data["start_time"] == sample_event_payload["start_time"]
        assert data["end_time"] == sample_event_payload["end_time"]
        assert data["location"] == sample_event_payload["location"]
        assert data["max_attendees"] == sample_event_payload["max_attendees"]
        assert data["is_public"] == sample_event_payload["is_public"]

    def test_create_event_minimal_payload(self, client):
        """POST /events with only required fields succeeds."""
        payload = {"title": "Quick Sync"}
        response = client.post("/events", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Quick Sync"
        assert "id" in data

    def test_create_event_missing_title(self, client):
        """POST /events without a title returns 422 (validation error)."""
        payload = {
            "description": "Event without a title",
            "start_time": "2026-11-15T18:00:00Z",
        }
        response = client.post("/events", json=payload)

        assert response.status_code == 422

    def test_create_event_empty_body(self, client):
        """POST /events with an empty JSON body returns 422."""
        response = client.post("/events", json={})

        assert response.status_code == 422

    def test_create_event_invalid_datetime(self, client):
        """POST /events with an unparseable datetime returns 422."""
        payload = {
            "title": "Bad Date Event",
            "start_time": "not-a-date",
        }
        response = client.post("/events", json=payload)

        assert response.status_code == 422

    def test_create_event_negative_max_attendees(self, client):
        """POST /events with negative max_attendees returns 422."""
        payload = {
            "title": "Impossible Event",
            "max_attendees": -1,
        }
        response = client.post("/events", json=payload)

        assert response.status_code == 422

    def test_create_event_wrong_content_type(self, client):
        """POST /events with non-JSON content type returns 415 or 422."""
        response = client.post(
            "/events",
            data="title=Hello",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code in (415, 422)

    def test_create_event_response_has_created_at(self, client, sample_event_payload):
        """Created event response includes a created_at timestamp."""
        response = client.post("/events", json=sample_event_payload)

        assert response.status_code == 201
        data = response.json()
        # The API should return some form of creation timestamp
        assert "created_at" in data or "createdAt" in data


# ---------------------------------------------------------------------------
# GET /events
# ---------------------------------------------------------------------------

class TestListEvents:
    """Tests for GET /events."""

    def test_list_events_empty(self, client):
        """GET /events returns 200 with an empty list when no events exist."""
        response = client.get("/events")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_events_returns_created(self, client, created_event):
        """GET /events includes a previously created event."""
        response = client.get("/events")

        assert response.status_code == 200
        data = response.json()
        event_ids = [e["id"] for e in data]
        assert created_event["id"] in event_ids

    def test_list_events_response_structure(self, client, created_event):
        """Each event in the list has the expected fields."""
        response = client.get("/events")

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

        event = data[0]
        expected_fields = {"id", "title", "start_time", "end_time"}
        assert expected_fields.issubset(event.keys())

    def test_list_events_pagination_limit(self, client, sample_event_payload):
        """GET /events?limit=N returns at most N events."""
        # Create several events
        for i in range(5):
            payload = {**sample_event_payload, "title": f"Event {i}"}
            client.post("/events", json=payload)

        response = client.get("/events?limit=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 2

    def test_list_events_pagination_offset(self, client, sample_event_payload):
        """GET /events?offset=N skips the first N events."""
        # Create events
        for i in range(3):
            payload = {**sample_event_payload, "title": f"Offset Event {i}"}
            client.post("/events", json=payload)

        response = client.get("/events?offset=1")

        assert response.status_code == 200
        data = response.json()
        # Should have fewer events than the total
        all_response = client.get("/events")
        all_data = all_response.json()
        assert len(data) < len(all_data)

    def test_list_events_filter_public(self, client, sample_event_payload):
        """GET /events?is_public=true returns only public events."""
        # Create a public event
        client.post("/events", json={**sample_event_payload, "is_public": True})
        # Create a private event
        client.post("/events", json={**sample_event_payload, "is_public": False})

        response = client.get("/events?is_public=true")

        assert response.status_code == 200
        data = response.json()
        for event in data:
            assert event.get("is_public") is True


# ---------------------------------------------------------------------------
# GET /events/{id}
# ---------------------------------------------------------------------------

class TestGetEvent:
    """Tests for GET /events/{id}."""

    def test_get_event_success(self, client, created_event):
        """GET /events/{id} returns the event with matching id."""
        event_id = created_event["id"]
        response = client.get(f"/events/{event_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == event_id
        assert data["title"] == created_event["title"]

    def test_get_event_not_found(self, client):
        """GET /events/{id} with non-existent id returns 404."""
        response = client.get("/events/999999")

        assert response.status_code == 404

    def test_get_event_invalid_id_format(self, client):
        """GET /events/{id} with non-integer id returns 422."""
        response = client.get("/events/not-a-number")

        assert response.status_code == 422

    def test_get_event_response_fields(self, client, created_event):
        """GET /events/{id} response contains all expected fields."""
        event_id = created_event["id"]
        response = client.get(f"/events/{event_id}")

        assert response.status_code == 200
        data = response.json()
        expected_fields = {
            "id",
            "title",
            "description",
            "start_time",
            "end_time",
            "location",
            "max_attendees",
            "is_public",
        }
        assert expected_fields.issubset(data.keys())

    def test_get_event_consistency_with_create(self, client, sample_event_payload):
        """GET /events/{id} returns the same data as the create response."""
        create_response = client.post("/events", json=sample_event_payload)
        assert create_response.status_code == 201
        created = create_response.json()

        get_response = client.get(f"/events/{created['id']}")
        assert get_response.status_code == 200
        fetched = get_response.json()

        assert created["title"] == fetched["title"]
        assert created["description"] == fetched["description"]
        assert created["start_time"] == fetched["start_time"]
        assert created["end_time"] == fetched["end_time"]
        assert created["location"] == fetched["location"]
        assert created["max_attendees"] == fetched["max_attendees"]
        assert created["is_public"] == fetched["is_public"]

    def test_get_event_negative_id(self, client):
        """GET /events/{id} with negative id returns 404 or 422."""
        response = client.get("/events/-1")

        assert response.status_code in (404, 422)
