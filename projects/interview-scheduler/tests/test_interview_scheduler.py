"""Tests for interview scheduler."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from interview_scheduler.api.routes import get_interview_service
from interview_scheduler.main import create_app
from interview_scheduler.models.conflict import ConflictCreate, ConflictType
from interview_scheduler.models.interview import (
    InterviewCreate,
    InterviewStatus,
    InterviewType,
    InterviewUpdate,
    Participant,
)
from interview_scheduler.models.reminder import ReminderCreate, ReminderType
from interview_scheduler.models.schedule import ScheduleCreate
from interview_scheduler.models.timeslot import TimeSlotRequest
from interview_scheduler.services.interview_service import InterviewService


@pytest.fixture
def client() -> TestClient:
    """Create a test client.

    Returns:
        TestClient instance.
    """
    app = create_app()
    shared_service = InterviewService()

    def override_get_service() -> InterviewService:
        return shared_service

    app.dependency_overrides[get_interview_service] = override_get_service
    return TestClient(app)


@pytest.fixture
def sample_interview_create() -> InterviewCreate:
    """Create sample interview data.

    Returns:
        InterviewCreate instance.
    """
    return InterviewCreate(
        title="Test Interview",
        description="A test interview",
        interview_type=InterviewType.VIDEO,
        participants=[
            Participant(
                name="John Doe",
                email="john@example.com",
                role="candidate",
                timezone="America/New_York",
            ),
            Participant(
                name="Jane Smith",
                email="jane@example.com",
                role="interviewer",
                timezone="Europe/London",
            ),
        ],
        duration_minutes=60,
        preferred_timezones=["America/New_York", "Europe/London"],
    )


@pytest.fixture
def sample_schedule_create() -> ScheduleCreate:
    """Create sample schedule data.

    Returns:
        ScheduleCreate instance.
    """
    return ScheduleCreate(
        name="Test Schedule",
        description="A test schedule",
        timezone="UTC",
    )


@pytest.fixture
def sample_reminder_create() -> ReminderCreate:
    """Create sample reminder data.

    Returns:
        ReminderCreate instance.
    """
    return ReminderCreate(
        interview_id=str(uuid.uuid4()),
        reminder_type=ReminderType.EMAIL,
        minutes_before=60,
        recipient="test@example.com",
        subject="Test Reminder",
        message="This is a test reminder",
    )


@pytest.fixture
def sample_timeslot_request() -> TimeSlotRequest:
    """Create sample time slot request.

    Returns:
        TimeSlotRequest instance.
    """
    now = datetime.utcnow()
    return TimeSlotRequest(
        participant_ids=["user1", "user2"],
        duration_minutes=60,
        start_date=now,
        end_date=now + timedelta(days=7),
    )


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check(self, client: TestClient) -> None:
        """Test health check endpoint.

        Args:
            client: Test client.
        """
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "interview-scheduler"


class TestInterviewEndpoints:
    """Tests for interview endpoints."""

    def test_create_interview(
        self, client: TestClient, sample_interview_create: InterviewCreate
    ) -> None:
        """Test creating an interview.

        Args:
            client: Test client.
            sample_interview_create: Sample interview data.
        """
        response = client.post(
            "/api/v1/interviews",
            json=sample_interview_create.model_dump(mode="json"),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Interview"
        assert data["status"] == "pending"
        assert len(data["participants"]) == 2
        assert "id" in data

    def test_get_interview(
        self, client: TestClient, sample_interview_create: InterviewCreate
    ) -> None:
        """Test getting an interview by ID.

        Args:
            client: Test client.
            sample_interview_create: Sample interview data.
        """
        create_response = client.post(
            "/api/v1/interviews",
            json=sample_interview_create.model_dump(mode="json"),
        )
        interview_id = create_response.json()["id"]

        response = client.get(f"/api/v1/interviews/{interview_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == interview_id
        assert data["title"] == "Test Interview"

    def test_get_interview_not_found(self, client: TestClient) -> None:
        """Test getting a non-existent interview.

        Args:
            client: Test client.
        """
        response = client.get(f"/api/v1/interviews/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_list_interviews(self, client: TestClient) -> None:
        """Test listing interviews.

        Args:
            client: Test client.
        """
        response = client.get("/api/v1/interviews")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_update_interview(
        self, client: TestClient, sample_interview_create: InterviewCreate
    ) -> None:
        """Test updating an interview.

        Args:
            client: Test client.
            sample_interview_create: Sample interview data.
        """
        create_response = client.post(
            "/api/v1/interviews",
            json=sample_interview_create.model_dump(mode="json"),
        )
        interview_id = create_response.json()["id"]

        response = client.put(
            f"/api/v1/interviews/{interview_id}",
            json={"title": "Updated Interview", "status": "scheduled"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Interview"
        assert data["status"] == "scheduled"

    def test_delete_interview(
        self, client: TestClient, sample_interview_create: InterviewCreate
    ) -> None:
        """Test deleting an interview.

        Args:
            client: Test client.
            sample_interview_create: Sample interview data.
        """
        create_response = client.post(
            "/api/v1/interviews",
            json=sample_interview_create.model_dump(mode="json"),
        )
        interview_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/interviews/{interview_id}")
        assert response.status_code == 204

        get_response = client.get(f"/api/v1/interviews/{interview_id}")
        assert get_response.status_code == 404


class TestScheduleEndpoints:
    """Tests for schedule endpoints."""

    def test_create_schedule(
        self, client: TestClient, sample_schedule_create: ScheduleCreate
    ) -> None:
        """Test creating a schedule.

        Args:
            client: Test client.
            sample_schedule_create: Sample schedule data.
        """
        response = client.post(
            "/api/v1/schedules",
            json=sample_schedule_create.model_dump(mode="json"),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Schedule"
        assert data["status"] == "draft"

    def test_list_schedules(self, client: TestClient) -> None:
        """Test listing schedules.

        Args:
            client: Test client.
        """
        response = client.get("/api/v1/schedules")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestTimeSlotEndpoints:
    """Tests for time slot endpoints."""

    def test_find_time_slots(
        self, client: TestClient, sample_timeslot_request: TimeSlotRequest
    ) -> None:
        """Test finding time slots.

        Args:
            client: Test client.
            sample_timeslot_request: Sample time slot request.
        """
        response = client.post(
            "/api/v1/timeslots/find",
            json=sample_timeslot_request.model_dump(mode="json"),
        )
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data
        assert "total_found" in data
        assert isinstance(data["slots"], list)


class TestConflictEndpoints:
    """Tests for conflict endpoints."""

    def test_list_conflicts(self, client: TestClient) -> None:
        """Test listing conflicts.

        Args:
            client: Test client.
        """
        response = client.get("/api/v1/conflicts")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_detect_conflicts_interview_not_found(self, client: TestClient) -> None:
        """Test detecting conflicts for non-existent interview.

        Args:
            client: Test client.
        """
        response = client.post(f"/api/v1/conflicts/detect?interview_id={uuid.uuid4()}")
        assert response.status_code == 404


class TestReminderEndpoints:
    """Tests for reminder endpoints."""

    def test_create_reminder(
        self, client: TestClient, sample_reminder_create: ReminderCreate
    ) -> None:
        """Test creating a reminder.

        Args:
            client: Test client.
            sample_reminder_create: Sample reminder data.
        """
        response = client.post(
            "/api/v1/reminders",
            json=sample_reminder_create.model_dump(mode="json"),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["reminder_type"] == "email"
        assert data["status"] == "pending"

    def test_list_reminders(self, client: TestClient) -> None:
        """Test listing reminders.

        Args:
            client: Test client.
        """
        response = client.get("/api/v1/reminders")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestAgentPipeline:
    """Tests for agent pipeline endpoint."""

    def test_schedule_pipeline_interview_not_found(self, client: TestClient) -> None:
        """Test scheduling pipeline for non-existent interview.

        Args:
            client: Test client.
        """
        response = client.post(f"/api/v1/agents/schedule?interview_id={uuid.uuid4()}")
        assert response.status_code == 404


class TestInterviewService:
    """Tests for InterviewService."""

    def test_create_and_get_interview(self) -> None:
        """Test creating and retrieving an interview."""
        service = InterviewService()
        data = InterviewCreate(
            title="Service Test",
            participants=[
                Participant(name="Test", email="test@test.com", role="candidate")
            ],
        )
        interview = service.create_interview(data)
        assert interview.id is not None
        assert interview.title == "Service Test"

        retrieved = service.get_interview(interview.id)
        assert retrieved is not None
        assert retrieved.id == interview.id

    def test_list_interviews_with_status_filter(self) -> None:
        """Test listing interviews with status filter."""
        service = InterviewService()
        data = InterviewCreate(
            title="Filter Test",
            participants=[
                Participant(name="Test", email="test@test.com", role="candidate")
            ],
        )
        interview = service.create_interview(data)
        service.update_interview(interview.id, InterviewUpdate(status=InterviewStatus.SCHEDULED))

        pending = service.list_interviews(status="pending")
        scheduled = service.list_interviews(status="scheduled")
        assert len(pending) == 0
        assert len(scheduled) == 1

    def test_delete_interview(self) -> None:
        """Test deleting an interview."""
        service = InterviewService()
        data = InterviewCreate(
            title="Delete Test",
            participants=[
                Participant(name="Test", email="test@test.com", role="candidate")
            ],
        )
        interview = service.create_interview(data)
        assert service.delete_interview(interview.id) is True
        assert service.get_interview(interview.id) is None
        assert service.delete_interview(interview.id) is False

    def test_find_time_slots(self) -> None:
        """Test finding time slots."""
        service = InterviewService()
        now = datetime.utcnow()
        request = TimeSlotRequest(
            participant_ids=["user1"],
            duration_minutes=60,
            start_date=now,
            end_date=now + timedelta(days=1),
        )
        response = service.find_time_slots(request)
        assert response.total_found > 0
        assert len(response.slots) > 0
