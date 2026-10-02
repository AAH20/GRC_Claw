"""Tests for lead nurture agent and API."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from lead_scorer.agents.lead_nurture import LeadNurtureAgent, NurtureConfig, NurtureStatus
from lead_scorer.agents.scoring import LeadGrade
from lead_scorer.models.routing import (
    NurtureCampaign,
    NurtureChannel,
    NurtureEnrollment,
    NurtureEnrollmentRequest,
    NurtureSequence,
    NurtureSequenceCreate,
    NurtureStep,
    NurtureStepStatus,
    RouteDestination,
)
from lead_scorer.main import create_app


@pytest.fixture
def nurture_agent() -> LeadNurtureAgent:
    """Create a nurture agent for testing."""
    return LeadNurtureAgent(timeout_seconds=10, max_retries=1)


@pytest.fixture
def sample_sequence_data() -> NurtureSequenceCreate:
    """Create sample sequence data."""
    return NurtureSequenceCreate(
        name="Test Nurture Sequence",
        description="A test nurture sequence",
        steps=[
            {
                "channel": "email",
                "subject": "Welcome!",
                "content_template": "welcome_email",
                "delay_days": 0,
            },
            {
                "channel": "email",
                "subject": "Case Study",
                "content_template": "case_study_email",
                "delay_days": 3,
            },
            {
                "channel": "linkedin",
                "subject": "Connect on LinkedIn",
                "content_template": "linkedin_connect",
                "delay_days": 7,
            },
        ],
        target_grade="cold",
        target_destination=RouteDestination.NURTURE,
    )


@pytest.fixture
def client() -> TestClient:
    """Create a test client."""
    app = create_app()
    return TestClient(app)


class TestNurtureSequence:
    """Tests for nurture sequence operations."""

    def test_create_sequence(
        self, nurture_agent: LeadNurtureAgent, sample_sequence_data: NurtureSequenceCreate
    ) -> None:
        """Test creating a nurture sequence."""
        sequence = nurture_agent.create_sequence(sample_sequence_data)
        assert isinstance(sequence, NurtureSequence)
        assert sequence.name == "Test Nurture Sequence"
        assert len(sequence.steps) == 3
        assert sequence.is_active is True
        assert sequence.target_grade == "cold"

    def test_create_sequence_invalid_name(self, nurture_agent: LeadNurtureAgent) -> None:
        """Test creating a sequence with empty name raises error."""
        data = NurtureSequenceCreate(
            name="",
            steps=[{"channel": "email", "subject": "Test"}],
        )
        with pytest.raises(ValueError):
            nurture_agent.create_sequence(data)

    def test_create_sequence_no_steps(self, nurture_agent: LeadNurtureAgent) -> None:
        """Test creating a sequence with no steps raises error."""
        data = NurtureSequenceCreate(
            name="Empty Sequence",
            steps=[],
        )
        with pytest.raises(ValueError):
            nurture_agent.create_sequence(data)

    def test_get_sequence(
        self, nurture_agent: LeadNurtureAgent, sample_sequence_data: NurtureSequenceCreate
    ) -> None:
        """Test getting a sequence by ID."""
        created = nurture_agent.create_sequence(sample_sequence_data)
        fetched = nurture_agent.get_sequence(created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == created.name

    def test_get_sequence_not_found(self, nurture_agent: LeadNurtureAgent) -> None:
        """Test getting a non-existent sequence."""
        assert nurture_agent.get_sequence("nonexistent") is None

    def test_list_sequences(
        self, nurture_agent: LeadNurtureAgent, sample_sequence_data: NurtureSequenceCreate
    ) -> None:
        """Test listing sequences."""
        nurture_agent.create_sequence(sample_sequence_data)
        sequences = nurture_agent.list_sequences()
        assert len(sequences) == 1

    def test_list_sequences_active_only(
        self, nurture_agent: LeadNurtureAgent, sample_sequence_data: NurtureSequenceCreate
    ) -> None:
        """Test listing only active sequences."""
        seq = nurture_agent.create_sequence(sample_sequence_data)
        nurture_agent.update_sequence(seq.id, is_active=False)
        active = nurture_agent.list_sequences(active_only=True)
        all_seqs = nurture_agent.list_sequences(active_only=False)
        assert len(active) == 0
        assert len(all_seqs) == 1

    def test_update_sequence(
        self, nurture_agent: LeadNurtureAgent, sample_sequence_data: NurtureSequenceCreate
    ) -> None:
        """Test updating a sequence."""
        seq = nurture_agent.create_sequence(sample_sequence_data)
        updated = nurture_agent.update_sequence(seq.id, name="Updated Name")
        assert updated is not None
        assert updated.name == "Updated Name"

    def test_delete_sequence(
        self, nurture_agent: LeadNurtureAgent, sample_sequence_data: NurtureSequenceCreate
    ) -> None:
        """Test deleting a sequence."""
        seq = nurture_agent.create_sequence(sample_sequence_data)
        assert nurture_agent.delete_sequence(seq.id) is True
        assert nurture_agent.get_sequence(seq.id) is None

    def test_delete_nonexistent_sequence(self, nurture_agent: LeadNurtureAgent) -> None:
        """Test deleting a non-existent sequence."""
        assert nurture_agent.delete_sequence("nonexistent") is False


class TestNurtureEnrollment:
    """Tests for nurture enrollment operations."""

    @pytest.mark.asyncio
    async def test_enroll_lead(
        self, nurture_agent: LeadNurtureAgent, sample_sequence_data: NurtureSequenceCreate
    ) -> None:
        """Test enrolling a lead in a sequence."""
        seq = nurture_agent.create_sequence(sample_sequence_data)
        request = NurtureEnrollmentRequest(
            lead_id="lead-enroll-1",
            sequence_id=seq.id,
        )
        enrollment = await nurture_agent.enroll(request)
        assert isinstance(enrollment, NurtureEnrollment)
        assert enrollment.lead_id == "lead-enroll-1"
        assert enrollment.sequence_id == seq.id
        assert enrollment.status == NurtureStatus.ACTIVE
        assert enrollment.current_step == 0

    @pytest.mark.asyncio
    async def test_enroll_invalid_lead_id(
        self, nurture_agent: LeadNurtureAgent, sample_sequence_data: NurtureSequenceCreate
    ) -> None:
        """Test enrolling with empty lead_id raises error."""
        seq = nurture_agent.create_sequence(sample_sequence_data)
        request = NurtureEnrollmentRequest(lead_id="", sequence_id=seq.id)
        with pytest.raises(ValueError):
            await nurture_agent.enroll(request)

    @pytest.mark.asyncio
    async def test_enroll_invalid_sequence(
        self, nurture_agent: LeadNurtureAgent
    ) -> None:
        """Test enrolling in non-existent sequence raises error."""
        request = NurtureEnrollmentRequest(
            lead_id="lead-1",
            sequence_id="nonexistent",
        )
        with pytest.raises(ValueError):
            await nurture_agent.enroll(request)

    @pytest.mark.asyncio
    async def test_get_enrollment(
        self, nurture_agent: LeadNurtureAgent, sample_sequence_data: NurtureSequenceCreate
    ) -> None:
        """Test getting an enrollment by ID."""
        seq = nurture_agent.create_sequence(sample_sequence_data)
        request = NurtureEnrollmentRequest(lead_id="lead-1", sequence_id=seq.id)
        enrollment = await nurture_agent.enroll(request)
        fetched = nurture_agent.get_enrollment(enrollment.id)
        assert fetched is not None
        assert fetched.id == enrollment.id

    @pytest.mark.asyncio
    async def test_get_lead_enrollments(
        self, nurture_agent: LeadNurtureAgent, sample_sequence_data: NurtureSequenceCreate
    ) -> None:
        """Test getting all enrollments for a lead."""
        seq = nurture_agent.create_sequence(sample_sequence_data)
        await nurture_agent.enroll(
            NurtureEnrollmentRequest(lead_id="lead-multi", sequence_id=seq.id)
        )
        await nurture_agent.enroll(
            NurtureEnrollmentRequest(lead_id="lead-multi", sequence_id=seq.id)
        )
        enrollments = nurture_agent.get_lead_enrollments("lead-multi")
        assert len(enrollments) == 2


class TestNurtureEngagement:
    """Tests for nurture engagement processing."""

    @pytest.mark.asyncio
    async def test_process_engagement(
        self, nurture_agent: LeadNurtureAgent, sample_sequence_data: NurtureSequenceCreate
    ) -> None:
        """Test processing an engagement event."""
        seq = nurture_agent.create_sequence(sample_sequence_data)
        enrollment = await nurture_agent.enroll(
            NurtureEnrollmentRequest(lead_id="lead-engage", sequence_id=seq.id)
        )
        event = await nurture_agent.process_engagement(
            enrollment_id=enrollment.id,
            event_type="opened",
        )
        assert event is not None
        assert event.event_type == "opened"
        assert event.lead_id == "lead-engage"

    @pytest.mark.asyncio
    async def test_process_engagement_invalid_enrollment(
        self, nurture_agent: LeadNurtureAgent
    ) -> None:
        """Test processing engagement for non-existent enrollment."""
        with pytest.raises(ValueError):
            await nurture_agent.process_engagement(
                enrollment_id="nonexistent",
                event_type="opened",
            )

    @pytest.mark.asyncio
    async def test_advance_step(
        self, nurture_agent: LeadNurtureAgent, sample_sequence_data: NurtureSequenceCreate
    ) -> None:
        """Test advancing to the next step."""
        seq = nurture_agent.create_sequence(sample_sequence_data)
        enrollment = await nurture_agent.enroll(
            NurtureEnrollmentRequest(lead_id="lead-advance", sequence_id=seq.id)
        )
        updated = await nurture_agent.advance_step(enrollment.id)
        assert updated is not None
        assert updated.current_step == 1

    @pytest.mark.asyncio
    async def test_advance_step_to_completion(
        self, nurture_agent: LeadNurtureAgent
    ) -> None:
        """Test advancing through all steps to completion."""
        seq_data = NurtureSequenceCreate(
            name="Short Sequence",
            steps=[
                {"channel": "email", "subject": "Step 1"},
                {"channel": "email", "subject": "Step 2"},
            ],
        )
        seq = nurture_agent.create_sequence(seq_data)
        enrollment = await nurture_agent.enroll(
            NurtureEnrollmentRequest(lead_id="lead-complete", sequence_id=seq.id)
        )
        await nurture_agent.advance_step(enrollment.id)
        final = await nurture_agent.advance_step(enrollment.id)
        assert final is not None
        assert final.status == NurtureStatus.COMPLETED


class TestNurtureExit:
    """Tests for nurture exit evaluation."""

    @pytest.mark.asyncio
    async def test_evaluate_exit_too_early(
        self, nurture_agent: LeadNurtureAgent, sample_sequence_data: NurtureSequenceCreate
    ) -> None:
        """Test that exit is denied before minimum steps."""
        seq = nurture_agent.create_sequence(sample_sequence_data)
        enrollment = await nurture_agent.enroll(
            NurtureEnrollmentRequest(lead_id="lead-exit", sequence_id=seq.id)
        )
        result = await nurture_agent.evaluate_exit(
            enrollment_id=enrollment.id,
            current_score=95.0,
            current_grade=LeadGrade.HOT,
        )
        assert result["should_exit"] is False
        assert "Minimum" in result["reason"]

    @pytest.mark.asyncio
    async def test_evaluate_exit_hot_lead(
        self, nurture_agent: LeadNurtureAgent, sample_sequence_data: NurtureSequenceCreate
    ) -> None:
        """Test exit when lead becomes hot."""
        seq = nurture_agent.create_sequence(sample_sequence_data)
        enrollment = await nurture_agent.enroll(
            NurtureEnrollmentRequest(lead_id="lead-hot-exit", sequence_id=seq.id)
        )
        # Advance past minimum steps
        await nurture_agent.advance_step(enrollment.id)
        await nurture_agent.advance_step(enrollment.id)
        result = await nurture_agent.evaluate_exit(
            enrollment_id=enrollment.id,
            current_score=90.0,
            current_grade=LeadGrade.HOT,
        )
        assert result["should_exit"] is True
        assert result["destination"] == RouteDestination.SALES

    @pytest.mark.asyncio
    async def test_evaluate_exit_qualified(
        self, nurture_agent: LeadNurtureAgent, sample_sequence_data: NurtureSequenceCreate
    ) -> None:
        """Test exit when lead becomes qualified."""
        seq = nurture_agent.create_sequence(sample_sequence_data)
        enrollment = await nurture_agent.enroll(
            NurtureEnrollmentRequest(lead_id="lead-qual-exit", sequence_id=seq.id)
        )
        await nurture_agent.advance_step(enrollment.id)
        await nurture_agent.advance_step(enrollment.id)
        result = await nurture_agent.evaluate_exit(
            enrollment_id=enrollment.id,
            qualification_status="qualified",
        )
        assert result["should_exit"] is True
        assert result["destination"] == RouteDestination.SALES_DEVELOPMENT

    @pytest.mark.asyncio
    async def test_evaluate_exit_invalid_enrollment(
        self, nurture_agent: LeadNurtureAgent
    ) -> None:
        """Test exit evaluation for non-existent enrollment."""
        with pytest.raises(ValueError):
            await nurture_agent.evaluate_exit(enrollment_id="nonexistent")

    @pytest.mark.asyncio
    async def test_evaluate_exit_continue_nurture(
        self, nurture_agent: LeadNurtureAgent, sample_sequence_data: NurtureSequenceCreate
    ) -> None:
        """Test that nurture continues when no exit criteria met."""
        seq = nurture_agent.create_sequence(sample_sequence_data)
        enrollment = await nurture_agent.enroll(
            NurtureEnrollmentRequest(lead_id="lead-continue", sequence_id=seq.id)
        )
        await nurture_agent.advance_step(enrollment.id)
        await nurture_agent.advance_step(enrollment.id)
        result = await nurture_agent.evaluate_exit(
            enrollment_id=enrollment.id,
            current_score=30.0,
            current_grade=LeadGrade.COLD,
        )
        assert result["should_exit"] is False


class TestNurtureStats:
    """Tests for nurture statistics."""

    def test_get_nurture_stats(
        self, nurture_agent: LeadNurtureAgent, sample_sequence_data: NurtureSequenceCreate
    ) -> None:
        """Test getting nurture statistics."""
        nurture_agent.create_sequence(sample_sequence_data)
        stats = nurture_agent.get_nurture_stats()
        assert stats["total_sequences"] == 1
        assert stats["total_enrollments"] == 0
        assert stats["active_enrollments"] == 0

    def test_get_nurture_stats_with_enrollments(
        self, nurture_agent: LeadNurtureAgent, sample_sequence_data: NurtureSequenceCreate
    ) -> None:
        """Test stats with active enrollments."""
        seq = nurture_agent.create_sequence(sample_sequence_data)

        async def setup() -> None:
            await nurture_agent.enroll(
                NurtureEnrollmentRequest(lead_id="lead-stats", sequence_id=seq.id)
            )

        import asyncio

        asyncio.get_event_loop().run_until_complete(setup())
        stats = nurture_agent.get_nurture_stats()
        assert stats["total_enrollments"] == 1
        assert stats["active_enrollments"] == 1


class TestNurtureAPI:
    """Tests for nurture API endpoints."""

    def test_create_sequence_api(self, client: TestClient) -> None:
        """Test creating a sequence via API."""
        response = client.post(
            "/api/v1/nurture/sequences",
            json={
                "name": "API Sequence",
                "steps": [
                    {"channel": "email", "subject": "Welcome"},
                    {"channel": "email", "subject": "Follow Up"},
                ],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "API Sequence"

    def test_list_sequences_api(self, client: TestClient) -> None:
        """Test listing sequences via API."""
        response = client.get("/api/v1/nurture/sequences")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["sequences"], list)

    def test_get_sequence_api(self, client: TestClient) -> None:
        """Test getting a sequence via API."""
        # Create first
        create_resp = client.post(
            "/api/v1/nurture/sequences",
            json={
                "name": "Get Test",
                "steps": [{"channel": "email", "subject": "Test"}],
            },
        )
        seq_id = create_resp.json()["data"]["id"]
        # Get
        response = client.get(f"/api/v1/nurture/sequences/{seq_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == seq_id

    def test_get_sequence_not_found(self, client: TestClient) -> None:
        """Test getting a non-existent sequence."""
        response = client.get("/api/v1/nurture/sequences/nonexistent")
        assert response.status_code == 404

    def test_enroll_lead_api(self, client: TestClient) -> None:
        """Test enrolling a lead via API."""
        # Create sequence first
        seq_resp = client.post(
            "/api/v1/nurture/sequences",
            json={
                "name": "Enroll Test",
                "steps": [{"channel": "email", "subject": "Test"}],
            },
        )
        seq_id = seq_resp.json()["data"]["id"]
        # Enroll
        response = client.post(
            "/api/v1/nurture/enroll",
            json={
                "lead_id": "lead-api-enroll",
                "sequence_id": seq_id,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["lead_id"] == "lead-api-enroll"

    def test_enroll_lead_not_found(self, client: TestClient) -> None:
        """Test enrolling in non-existent sequence."""
        response = client.post(
            "/api/v1/nurture/enroll",
            json={
                "lead_id": "lead-1",
                "sequence_id": "nonexistent",
            },
        )
        assert response.status_code == 400

    def test_record_engagement_api(self, client: TestClient) -> None:
        """Test recording engagement via API."""
        # Create sequence and enroll
        seq_resp = client.post(
            "/api/v1/nurture/sequences",
            json={
                "name": "Engagement Test",
                "steps": [{"channel": "email", "subject": "Test"}],
            },
        )
        seq_id = seq_resp.json()["data"]["id"]
        enroll_resp = client.post(
            "/api/v1/nurture/enroll",
            json={"lead_id": "lead-engage-api", "sequence_id": seq_id},
        )
        enrollment_id = enroll_resp.json()["data"]["id"]
        # Record engagement
        response = client.post(
            "/api/v1/nurture/engagement",
            json={
                "enrollment_id": enrollment_id,
                "event_type": "opened",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_advance_step_api(self, client: TestClient) -> None:
        """Test advancing step via API."""
        # Setup
        seq_resp = client.post(
            "/api/v1/nurture/sequences",
            json={
                "name": "Advance Test",
                "steps": [
                    {"channel": "email", "subject": "Step 1"},
                    {"channel": "email", "subject": "Step 2"},
                ],
            },
        )
        seq_id = seq_resp.json()["data"]["id"]
        enroll_resp = client.post(
            "/api/v1/nurture/enroll",
            json={"lead_id": "lead-advance-api", "sequence_id": seq_id},
        )
        enrollment_id = enroll_resp.json()["data"]["id"]
        # Advance
        response = client.post(f"/api/v1/nurture/advance/{enrollment_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["current_step"] == 1

    def test_evaluate_exit_api(self, client: TestClient) -> None:
        """Test exit evaluation via API."""
        # Setup
        seq_resp = client.post(
            "/api/v1/nurture/sequences",
            json={
                "name": "Exit Test",
                "steps": [
                    {"channel": "email", "subject": "Step 1"},
                    {"channel": "email", "subject": "Step 2"},
                    {"channel": "email", "subject": "Step 3"},
                ],
            },
        )
        seq_id = seq_resp.json()["data"]["id"]
        enroll_resp = client.post(
            "/api/v1/nurture/enroll",
            json={"lead_id": "lead-exit-api", "sequence_id": seq_id},
        )
        enrollment_id = enroll_resp.json()["data"]["id"]
        # Advance past minimum
        client.post(f"/api/v1/nurture/advance/{enrollment_id}")
        client.post(f"/api/v1/nurture/advance/{enrollment_id}")
        # Evaluate
        response = client.post(
            "/api/v1/nurture/evaluate-exit",
            json={
                "enrollment_id": enrollment_id,
                "current_score": 90.0,
                "current_grade": "hot",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["should_exit"] is True

    def test_nurture_stats_api(self, client: TestClient) -> None:
        """Test getting nurture stats via API."""
        response = client.get("/api/v1/nurture/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_sequences" in data["stats"]
