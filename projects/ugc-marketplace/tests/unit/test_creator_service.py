"""Unit tests for CreatorService."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from ugc_marketplace.services.creator_service import CreatorService
from ugc_marketplace.models.creator import Creator


@pytest.fixture
def mock_repository():
    """Fixture providing a mock creator repository."""
    repo = MagicMock()
    return repo


@pytest.fixture
def creator_service(mock_repository):
    """Fixture providing a CreatorService instance with mocked repository."""
    return CreatorService(repository=mock_repository)


@pytest.fixture
def sample_creator():
    """Fixture providing a sample Creator instance."""
    return Creator(
        id="creator-001",
        username="test_creator",
        email="creator@example.com",
        display_name="Test Creator",
        bio="A test creator for unit tests",
        is_verified=True,
        created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def sample_creator_data():
    """Fixture providing raw creator data for creation tests."""
    return {
        "username": "new_creator",
        "email": "new@example.com",
        "display_name": "New Creator",
        "bio": "A newly created creator",
    }


class TestCreateCreator:
    """Tests for CreatorService.create_creator."""

    def test_create_creator(self, creator_service, mock_repository, sample_creator_data, sample_creator):
        """Test that create_creator persists a new creator and returns it."""
        mock_repository.create.return_value = sample_creator

        result = creator_service.create_creator(**sample_creator_data)

        mock_repository.create.assert_called_once_with(**sample_creator_data)
        assert result is not None
        assert result.id == "creator-001"
        assert result.username == "test_creator"
        assert result.email == "creator@example.com"
        assert result.display_name == "Test Creator"
        assert result.is_verified is True

    def test_create_creator_with_minimal_data(self, creator_service, mock_repository):
        """Test creator creation with only required fields."""
        minimal_data = {"username": "minimal_user", "email": "minimal@example.com"}
        expected_creator = Creator(
            id="creator-002",
            username="minimal_user",
            email="minimal@example.com",
            display_name="",
            bio="",
            is_verified=False,
        )
        mock_repository.create.return_value = expected_creator

        result = creator_service.create_creator(**minimal_data)

        mock_repository.create.assert_called_once_with(**minimal_data)
        assert result.username == "minimal_user"
        assert result.is_verified is False

    def test_create_creator_repository_failure(self, creator_service, mock_repository, sample_creator_data):
        """Test that repository exceptions propagate correctly."""
        mock_repository.create.side_effect = ValueError("Duplicate username")

        with pytest.raises(ValueError, match="Duplicate username"):
            creator_service.create_creator(**sample_creator_data)


class TestGetCreator:
    """Tests for CreatorService.get_creator."""

    def test_get_creator(self, creator_service, mock_repository, sample_creator):
        """Test that get_creator retrieves a creator by ID."""
        mock_repository.get_by_id.return_value = sample_creator

        result = creator_service.get_creator("creator-001")

        mock_repository.get_by_id.assert_called_once_with("creator-001")
        assert result is not None
        assert result.id == "creator-001"
        assert result.username == "test_creator"
        assert result.email == "creator@example.com"
        assert result.display_name == "Test Creator"
        assert result.bio == "A test creator for unit tests"
        assert result.is_verified is True

    def test_get_creator_not_found(self, creator_service, mock_repository):
        """Test that get_creator returns None when creator does not exist."""
        mock_repository.get_by_id.return_value = None

        result = creator_service.get_creator("nonexistent-id")

        mock_repository.get_by_id.assert_called_once_with("nonexistent-id")
        assert result is None

    def test_get_creator_by_username(self, creator_service, mock_repository, sample_creator):
        """Test that get_creator can retrieve by username."""
        mock_repository.get_by_username.return_value = sample_creator

        result = creator_service.get_creator_by_username("test_creator")

        mock_repository.get_by_username.assert_called_once_with("test_creator")
        assert result is not None
        assert result.username == "test_creator"


class TestListCreators:
    """Tests for CreatorService.list_creators."""

    def test_list_creators(self, creator_service, mock_repository, sample_creator):
        """Test that list_creators returns all creators."""
        creators = [
            sample_creator,
            Creator(
                id="creator-002",
                username="second_creator",
                email="second@example.com",
                display_name="Second Creator",
                bio="Another creator",
                is_verified=False,
            ),
            Creator(
                id="creator-003",
                username="third_creator",
                email="third@example.com",
                display_name="Third Creator",
                bio="Yet another creator",
                is_verified=True,
            ),
        ]
        mock_repository.list_all.return_value = creators

        result = creator_service.list_creators()

        mock_repository.list_all.assert_called_once()
        assert result is not None
        assert len(result) == 3
        assert result[0].id == "creator-001"
        assert result[1].id == "creator-002"
        assert result[2].id == "creator-003"

    def test_list_creators_empty(self, creator_service, mock_repository):
        """Test that list_creators returns empty list when no creators exist."""
        mock_repository.list_all.return_value = []

        result = creator_service.list_creators()

        mock_repository.list_all.assert_called_once()
        assert result is not None
        assert len(result) == 0
        assert result == []

    def test_list_creators_with_pagination(self, creator_service, mock_repository, sample_creator):
        """Test that list_creators supports pagination parameters."""
        creators = [sample_creator]
        mock_repository.list_all.return_value = creators

        result = creator_service.list_creators(limit=10, offset=0)

        mock_repository.list_all.assert_called_once_with(limit=10, offset=0)
        assert len(result) == 1

    def test_list_creators_with_verified_filter(self, creator_service, mock_repository, sample_creator):
        """Test that list_creators can filter by verified status."""
        verified_creators = [sample_creator]
        mock_repository.list_all.return_value = verified_creators

        result = creator_service.list_creators(is_verified=True)

        mock_repository.list_all.assert_called_once_with(is_verified=True)
        assert len(result) == 1
        assert result[0].is_verified is True
