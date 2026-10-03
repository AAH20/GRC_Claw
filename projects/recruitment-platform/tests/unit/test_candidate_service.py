"""Unit tests for the Candidate Service."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from recruitment_platform.services.candidate_service import CandidateService
from recruitment_platform.models.candidate import Candidate


@pytest.fixture
def mock_repository():
    """Provide a mock candidate repository."""
    return MagicMock()


@pytest.fixture
def candidate_service(mock_repository):
    """Provide a CandidateService instance with a mocked repository."""
    return CandidateService(repository=mock_repository)


@pytest.fixture
def sample_candidate():
    """Provide a sample Candidate instance."""
    return Candidate(
        id="cand-001",
        first_name="Alice",
        last_name="Johnson",
        email="alice.johnson@example.com",
        phone="+1-555-0100",
        status="active",
        created_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_candidate_data():
    """Provide raw data for creating a candidate."""
    return {
        "first_name": "Bob",
        "last_name": "Smith",
        "email": "bob.smith@example.com",
        "phone": "+1-555-0200",
        "status": "active",
    }


# ---------------------------------------------------------------------------
# Test: create_candidate
# ---------------------------------------------------------------------------


class TestCreateCandidate:
    """Tests for CandidateService.create_candidate."""

    def test_create_candidate(self, candidate_service, mock_repository, sample_candidate_data):
        """Test that a candidate is created and returned with an ID."""
        expected_candidate = Candidate(
            id="cand-002",
            **sample_candidate_data,
            created_at=datetime(2026, 2, 1, 9, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 2, 1, 9, 0, 0, tzinfo=timezone.utc),
        )
        mock_repository.create.return_value = expected_candidate

        result = candidate_service.create_candidate(**sample_candidate_data)

        mock_repository.create.assert_called_once_with(**sample_candidate_data)
        assert result is not None
        assert result.id == "cand-002"
        assert result.first_name == "Bob"
        assert result.last_name == "Smith"
        assert result.email == "bob.smith@example.com"
        assert result.status == "active"

    def test_create_candidate_assigns_timestamps(
        self, candidate_service, mock_repository, sample_candidate_data
    ):
        """Test that created_at and updated_at are set on the new candidate."""
        mock_repository.create.return_value = Candidate(
            id="cand-003",
            **sample_candidate_data,
            created_at=datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc),
        )

        result = candidate_service.create_candidate(**sample_candidate_data)

        assert result.created_at is not None
        assert result.updated_at is not None
        assert result.created_at == result.updated_at

    def test_create_candidate_raises_on_duplicate_email(
        self, candidate_service, mock_repository, sample_candidate_data
    ):
        """Test that creating a candidate with a duplicate email raises an error."""
        mock_repository.create.side_effect = ValueError("Candidate with this email already exists")

        with pytest.raises(ValueError, match="already exists"):
            candidate_service.create_candidate(**sample_candidate_data)


# ---------------------------------------------------------------------------
# Test: get_candidate
# ---------------------------------------------------------------------------


class TestGetCandidate:
    """Tests for CandidateService.get_candidate."""

    def test_get_candidate(self, candidate_service, mock_repository, sample_candidate):
        """Test that a candidate is retrieved by ID."""
        mock_repository.get_by_id.return_value = sample_candidate

        result = candidate_service.get_candidate("cand-001")

        mock_repository.get_by_id.assert_called_once_with("cand-001")
        assert result is not None
        assert result.id == "cand-001"
        assert result.first_name == "Alice"
        assert result.last_name == "Johnson"
        assert result.email == "alice.johnson@example.com"

    def test_get_candidate_not_found(self, candidate_service, mock_repository):
        """Test that retrieving a non-existent candidate returns None."""
        mock_repository.get_by_id.return_value = None

        result = candidate_service.get_candidate("nonexistent-id")

        mock_repository.get_by_id.assert_called_once_with("nonexistent-id")
        assert result is None

    def test_get_candidate_invalid_id_raises(self, candidate_service, mock_repository):
        """Test that an invalid ID raises a ValueError."""
        mock_repository.get_by_id.side_effect = ValueError("Invalid candidate ID format")

        with pytest.raises(ValueError, match="Invalid candidate ID"):
            candidate_service.get_candidate("")


# ---------------------------------------------------------------------------
# Test: list_candidates
# ---------------------------------------------------------------------------


class TestListCandidates:
    """Tests for CandidateService.list_candidates."""

    def test_list_candidates(self, candidate_service, mock_repository, sample_candidate):
        """Test that all candidates are returned."""
        other_candidate = Candidate(
            id="cand-002",
            first_name="Bob",
            last_name="Smith",
            email="bob.smith@example.com",
            phone="+1-555-0200",
            status="active",
            created_at=datetime(2026, 1, 16, 11, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2026, 1, 16, 11, 0, 0, tzinfo=timezone.utc),
        )
        mock_repository.list_all.return_value = [sample_candidate, other_candidate]

        result = candidate_service.list_candidates()

        mock_repository.list_all.assert_called_once()
        assert len(result) == 2
        assert result[0].id == "cand-001"
        assert result[1].id == "cand-002"

    def test_list_candidates_empty(self, candidate_service, mock_repository):
        """Test that an empty list is returned when no candidates exist."""
        mock_repository.list_all.return_value = []

        result = candidate_service.list_candidates()

        mock_repository.list_all.assert_called_once()
        assert result == []

    def test_list_candidates_with_status_filter(
        self, candidate_service, mock_repository, sample_candidate
    ):
        """Test that candidates can be filtered by status."""
        mock_repository.list_all.return_value = [sample_candidate]

        result = candidate_service.list_candidates(status="active")

        mock_repository.list_all.assert_called_once_with(status="active")
        assert len(result) == 1
        assert result[0].status == "active"

    def test_list_candidates_with_pagination(self, candidate_service, mock_repository):
        """Test that pagination parameters are passed through."""
        mock_repository.list_all.return_value = []

        result = candidate_service.list_candidates(limit=10, offset=20)

        mock_repository.list_all.assert_called_once_with(limit=10, offset=20)
        assert result == []
