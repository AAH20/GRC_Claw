"""Unit tests for the CommunityService."""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from gated_communities.services.community_service import CommunityService
from gated_communities.models.community import Community


@pytest.fixture
def mock_repository():
    """Provide a mock repository for the community service."""
    return MagicMock()


@pytest.fixture
def community_service(mock_repository):
    """Provide a CommunityService instance with a mock repository."""
    return CommunityService(repository=mock_repository)


@pytest.fixture
def sample_community():
    """Provide a sample Community instance for testing."""
    return Community(
        id="comm-001",
        name="Test Community",
        description="A test community for unit testing",
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        owner_id="user-001",
        is_active=True,
    )


@pytest.fixture
def sample_community_data():
    """Provide sample data for creating a community."""
    return {
        "name": "New Community",
        "description": "A newly created community",
        "owner_id": "user-002",
    }


class TestCreateCommunity:
    """Tests for CommunityService.create_community."""

    def test_create_community(self, community_service, mock_repository, sample_community_data):
        """Test that a community is created successfully."""
        # Arrange
        expected_community = Community(
            id="comm-new",
            name=sample_community_data["name"],
            description=sample_community_data["description"],
            owner_id=sample_community_data["owner_id"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            is_active=True,
        )
        mock_repository.create.return_value = expected_community

        # Act
        result = community_service.create_community(**sample_community_data)

        # Assert
        assert result is not None
        assert result.id == "comm-new"
        assert result.name == sample_community_data["name"]
        assert result.description == sample_community_data["description"]
        assert result.owner_id == sample_community_data["owner_id"]
        assert result.is_active is True
        mock_repository.create.assert_called_once()

    def test_create_community_persists_to_repository(
        self, community_service, mock_repository, sample_community_data
    ):
        """Test that create_community calls the repository's create method."""
        # Arrange
        mock_repository.create.return_value = MagicMock()

        # Act
        community_service.create_community(**sample_community_data)

        # Assert
        mock_repository.create.assert_called_once()
        call_args = mock_repository.create.call_args[0][0]
        assert call_args.name == sample_community_data["name"]
        assert call_args.description == sample_community_data["description"]
        assert call_args.owner_id == sample_community_data["owner_id"]


class TestGetCommunity:
    """Tests for CommunityService.get_community."""

    def test_get_community(self, community_service, mock_repository, sample_community):
        """Test that a community is retrieved successfully by ID."""
        # Arrange
        mock_repository.get_by_id.return_value = sample_community

        # Act
        result = community_service.get_community("comm-001")

        # Assert
        assert result is not None
        assert result.id == "comm-001"
        assert result.name == "Test Community"
        assert result.description == "A test community for unit testing"
        assert result.owner_id == "user-001"
        assert result.is_active is True
        mock_repository.get_by_id.assert_called_once_with("comm-001")

    def test_get_community_not_found(self, community_service, mock_repository):
        """Test that get_community returns None when the community does not exist."""
        # Arrange
        mock_repository.get_by_id.return_value = None

        # Act
        result = community_service.get_community("nonexistent-id")

        # Assert
        assert result is None
        mock_repository.get_by_id.assert_called_once_with("nonexistent-id")


class TestListCommunities:
    """Tests for CommunityService.list_communities."""

    def test_list_communities(self, community_service, mock_repository, sample_community):
        """Test that all communities are listed successfully."""
        # Arrange
        another_community = Community(
            id="comm-002",
            name="Another Community",
            description="Another test community",
            created_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
            owner_id="user-003",
            is_active=True,
        )
        expected_communities = [sample_community, another_community]
        mock_repository.get_all.return_value = expected_communities

        # Act
        result = community_service.list_communities()

        # Assert
        assert result is not None
        assert len(result) == 2
        assert result[0].id == "comm-001"
        assert result[0].name == "Test Community"
        assert result[1].id == "comm-002"
        assert result[1].name == "Another Community"
        mock_repository.get_all.assert_called_once()

    def test_list_communities_empty(self, community_service, mock_repository):
        """Test that list_communities returns an empty list when no communities exist."""
        # Arrange
        mock_repository.get_all.return_value = []

        # Act
        result = community_service.list_communities()

        # Assert
        assert result is not None
        assert len(result) == 0
        assert result == []
        mock_repository.get_all.assert_called_once()
