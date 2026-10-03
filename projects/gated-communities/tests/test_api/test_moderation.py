"""
Comprehensive API tests for the Moderation endpoints.

Tests cover:
- POST /moderation — create moderation item
- GET /moderation/queue — retrieve moderation queue
- PATCH /moderation/{id}/resolve — resolve a moderation item
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import app and dependencies — adjust paths to match project structure
import sys
from pathlib import Path

# Add project root to path so imports work
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from app.main import app
from app.database import Base, get_db
from app.models.moderation import ModerationItem, ModerationStatus, ModerationPriority
from app.models.user import User
from app.models.community import Community
from app.core.security import create_access_token


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh in-memory SQLite database for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden DB dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user in the database."""
    user = User(
        id=1,
        username="testmoderator",
        email="moderator@test.com",
        hashed_password="fakehashedpassword",
        is_active=True,
        is_moderator=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_community(db_session):
    """Create a test community in the database."""
    community = Community(
        id=1,
        name="Test Community",
        description="A test community for moderation tests",
        owner_id=1,
        is_active=True,
    )
    db_session.add(community)
    db_session.commit()
    db_session.refresh(community)
    return community


@pytest.fixture
def auth_headers(test_user):
    """Generate authorization headers for the test user."""
    access_token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def sample_moderation_payload():
    """Return a valid payload for creating a moderation item."""
    return {
        "community_id": 1,
        "reported_user_id": 2,
        "reporter_id": 1,
        "reason": "spam",
        "description": "User posting spam links in general chat",
        "priority": "medium",
    }


@pytest.fixture
def existing_moderation_item(db_session, test_community, test_user):
    """Create an existing moderation item in the database."""
    item = ModerationItem(
        id=1,
        community_id=1,
        reported_user_id=2,
        reporter_id=1,
        reason="spam",
        description="User posting spam links",
        priority=ModerationPriority.MEDIUM,
        status=ModerationStatus.PENDING,
        moderator_id=None,
        resolution_notes=None,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


# ---------------------------------------------------------------------------
# POST /moderation — Create moderation item
# ---------------------------------------------------------------------------

class TestCreateModerationItem:
    """Tests for POST /moderation endpoint."""

    def test_create_moderation_item_success(self, client, auth_headers, sample_moderation_payload):
        """Successfully create a moderation item with valid data."""
        response = client.post(
            "/moderation",
            json=sample_moderation_payload,
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["community_id"] == sample_moderation_payload["community_id"]
        assert data["reported_user_id"] == sample_moderation_payload["reported_user_id"]
        assert data["reporter_id"] == sample_moderation_payload["reporter_id"]
        assert data["reason"] == sample_moderation_payload["reason"]
        assert data["description"] == sample_moderation_payload["description"]
        assert data["status"] == "pending"
        assert "id" in data
        assert "created_at" in data

    def test_create_moderation_item_unauthenticated(self, client, sample_moderation_payload):
        """Creating a moderation item without authentication should fail."""
        response = client.post("/moderation", json=sample_moderation_payload)
        assert response.status_code == 401

    def test_create_moderation_item_missing_required_fields(self, client, auth_headers):
        """Creating a moderation item with missing required fields should fail."""
        incomplete_payload = {
            "community_id": 1,
            # missing reported_user_id, reporter_id, reason
        }
        response = client.post(
            "/moderation",
            json=incomplete_payload,
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_moderation_item_invalid_priority(self, client, auth_headers):
        """Creating a moderation item with invalid priority should fail."""
        payload = {
            "community_id": 1,
            "reported_user_id": 2,
            "reporter_id": 1,
            "reason": "spam",
            "description": "Test",
            "priority": "super-urgent",  # invalid
        }
        response = client.post(
            "/moderation",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_moderation_item_nonexistent_community(self, client, auth_headers):
        """Creating a moderation item for a non-existent community should fail."""
        payload = {
            "community_id": 99999,
            "reported_user_id": 2,
            "reporter_id": 1,
            "reason": "spam",
            "description": "Test",
            "priority": "low",
        }
        response = client.post(
            "/moderation",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_create_moderation_item_invalid_reason(self, client, auth_headers):
        """Creating a moderation item with an invalid reason should fail."""
        payload = {
            "community_id": 1,
            "reported_user_id": 2,
            "reporter_id": 1,
            "reason": "not_a_valid_reason",
            "description": "Test",
            "priority": "low",
        }
        response = client.post(
            "/moderation",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_moderation_item_empty_description(self, client, auth_headers):
        """Creating a moderation item with empty description should fail."""
        payload = {
            "community_id": 1,
            "reported_user_id": 2,
            "reporter_id": 1,
            "reason": "spam",
            "description": "",
            "priority": "low",
        }
        response = client.post(
            "/moderation",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_moderation_item_self_report(self, client, auth_headers):
        """A user should not be able to report themselves."""
        payload = {
            "community_id": 1,
            "reported_user_id": 1,  # same as reporter
            "reporter_id": 1,
            "reason": "spam",
            "description": "Self report",
            "priority": "low",
        }
        response = client.post(
            "/moderation",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_create_moderation_item_duplicate_report(self, client, auth_headers, existing_moderation_item):
        """Duplicate report for the same user in the same community should be handled."""
        payload = {
            "community_id": 1,
            "reported_user_id": 2,
            "reporter_id": 1,
            "reason": "spam",
            "description": "Duplicate report",
            "priority": "medium",
        }
        response = client.post(
            "/moderation",
            json=payload,
            headers=auth_headers,
        )
        # Should either return 409 Conflict or 200 with existing item
        assert response.status_code in (200, 409)

    def test_create_moderation_item_all_valid_priorities(self, client, auth_headers):
        """Creating moderation items with each valid priority should succeed."""
        for priority in ["low", "medium", "high", "critical"]:
            payload = {
                "community_id": 1,
                "reported_user_id": 2,
                "reporter_id": 1,
                "reason": "spam",
                "description": f"Test with {priority} priority",
                "priority": priority,
            }
            response = client.post(
                "/moderation",
                json=payload,
                headers=auth_headers,
            )
            assert response.status_code == 201
            assert response.json()["priority"] == priority

    def test_create_moderation_item_all_valid_reasons(self, client, auth_headers):
        """Creating moderation items with each valid reason should succeed."""
        valid_reasons = ["spam", "harassment", "hate_speech", "inappropriate_content", "impersonation", "other"]
        for reason in valid_reasons:
            payload = {
                "community_id": 1,
                "reported_user_id": 2,
                "reporter_id": 1,
                "reason": reason,
                "description": f"Test with {reason} reason",
                "priority": "low",
            }
            response = client.post(
                "/moderation",
                json=payload,
                headers=auth_headers,
            )
            assert response.status_code == 201
            assert response.json()["reason"] == reason


# ---------------------------------------------------------------------------
# GET /moderation/queue — Retrieve moderation queue
# ---------------------------------------------------------------------------

class TestGetModerationQueue:
    """Tests for GET /moderation/queue endpoint."""

    def test_get_moderation_queue_success(self, client, auth_headers, existing_moderation_item):
        """Successfully retrieve the moderation queue."""
        response = client.get("/moderation/queue", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_moderation_queue_unauthenticated(self, client):
        """Retrieving the moderation queue without authentication should fail."""
        response = client.get("/moderation/queue")
        assert response.status_code == 401

    def test_get_moderation_queue_empty(self, client, auth_headers):
        """Retrieving an empty moderation queue should return an empty list."""
        response = client.get("/moderation/queue", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_moderation_queue_filter_by_status(self, client, auth_headers, db_session):
        """Filter moderation queue by status."""
        # Create items with different statuses
        for i, status in enumerate([ModerationStatus.PENDING, ModerationStatus.PENDING, ModerationStatus.RESOLVED]):
            item = ModerationItem(
                id=i + 1,
                community_id=1,
                reported_user_id=i + 10,
                reporter_id=1,
                reason="spam",
                description=f"Test item {i}",
                priority=ModerationPriority.MEDIUM,
                status=status,
            )
            db_session.add(item)
        db_session.commit()

        response = client.get("/moderation/queue?status=pending", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        for item in data:
            assert item["status"] == "pending"

    def test_get_moderation_queue_filter_by_priority(self, client, auth_headers, db_session):
        """Filter moderation queue by priority."""
        for i, priority in enumerate([ModerationPriority.LOW, ModerationPriority.HIGH, ModerationPriority.CRITICAL]):
            item = ModerationItem(
                id=i + 1,
                community_id=1,
                reported_user_id=i + 10,
                reporter_id=1,
                reason="spam",
                description=f"Test item {i}",
                priority=priority,
                status=ModerationStatus.PENDING,
            )
            db_session.add(item)
        db_session.commit()

        response = client.get("/moderation/queue?priority=high", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["priority"] == "high"

    def test_get_moderation_queue_filter_by_community(self, client, auth_headers, db_session):
        """Filter moderation queue by community_id."""
        for i in range(3):
            item = ModerationItem(
                id=i + 1,
                community_id=1 if i < 2 else 2,
                reported_user_id=i + 10,
                reporter_id=1,
                reason="spam",
                description=f"Test item {i}",
                priority=ModerationPriority.MEDIUM,
                status=ModerationStatus.PENDING,
            )
            db_session.add(item)
        db_session.commit()

        response = client.get("/moderation/queue?community_id=1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        for item in data:
            assert item["community_id"] == 1

    def test_get_moderation_queue_pagination(self, client, auth_headers, db_session):
        """Test pagination of the moderation queue."""
        # Create 10 items
        for i in range(10):
            item = ModerationItem(
                id=i + 1,
                community_id=1,
                reported_user_id=i + 10,
                reporter_id=1,
                reason="spam",
                description=f"Test item {i}",
                priority=ModerationPriority.MEDIUM,
                status=ModerationStatus.PENDING,
            )
            db_session.add(item)
        db_session.commit()

        # Test limit
        response = client.get("/moderation/queue?limit=5", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

        # Test offset
        response = client.get("/moderation/queue?limit=5&offset=5", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    def test_get_moderation_queue_sort_by_priority(self, client, auth_headers, db_session):
        """Test sorting the moderation queue by priority."""
        priorities = [ModerationPriority.LOW, ModerationPriority.CRITICAL, ModerationPriority.MEDIUM]
        for i, priority in enumerate(priorities):
            item = ModerationItem(
                id=i + 1,
                community_id=1,
                reported_user_id=i + 10,
                reporter_id=1,
                reason="spam",
                description=f"Test item {i}",
                priority=priority,
                status=ModerationStatus.PENDING,
            )
            db_session.add(item)
        db_session.commit()

        response = client.get("/moderation/queue?sort_by=priority&sort_order=desc", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Critical should come first in descending order
        assert data[0]["priority"] == "critical"

    def test_get_moderation_queue_sort_by_created_at(self, client, auth_headers, db_session):
        """Test sorting the moderation queue by created_at."""
        for i in range(3):
            item = ModerationItem(
                id=i + 1,
                community_id=1,
                reported_user_id=i + 10,
                reporter_id=1,
                reason="spam",
                description=f"Test item {i}",
                priority=ModerationPriority.MEDIUM,
                status=ModerationStatus.PENDING,
            )
            db_session.add(item)
        db_session.commit()

        response = client.get("/moderation/queue?sort_by=created_at&sort_order=desc", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_get_moderation_queue_response_structure(self, client, auth_headers, existing_moderation_item):
        """Verify the response structure of queue items."""
        response = client.get("/moderation/queue", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        item = data[0]
        required_fields = ["id", "community_id", "reported_user_id", "reporter_id", "reason", "status", "priority", "created_at"]
        for field in required_fields:
            assert field in item, f"Missing field: {field}"

    def test_get_moderation_queue_combined_filters(self, client, auth_headers, db_session):
        """Test combining multiple filters."""
        for i in range(6):
            item = ModerationItem(
                id=i + 1,
                community_id=1 if i < 4 else 2,
                reported_user_id=i + 10,
                reporter_id=1,
                reason="spam",
                description=f"Test item {i}",
                priority=ModerationPriority.HIGH if i % 2 == 0 else ModerationPriority.LOW,
                status=ModerationStatus.PENDING if i < 3 else ModerationStatus.RESOLVED,
            )
            db_session.add(item)
        db_session.commit()

        response = client.get(
            "/moderation/queue?community_id=1&status=pending&priority=high",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        for item in data:
            assert item["community_id"] == 1
            assert item["status"] == "pending"
            assert item["priority"] == "high"


# ---------------------------------------------------------------------------
# PATCH /moderation/{id}/resolve — Resolve a moderation item
# ---------------------------------------------------------------------------

class TestResolveModerationItem:
    """Tests for PATCH /moderation/{id}/resolve endpoint."""

    def test_resolve_moderation_item_success(self, client, auth_headers, existing_moderation_item):
        """Successfully resolve a pending moderation item."""
        response = client.patch(
            f"/moderation/{existing_moderation_item.id}/resolve",
            json={"resolution_notes": "User warned for spam", "action_taken": "warning"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == existing_moderation_item.id
        assert data["status"] == "resolved"
        assert data["resolution_notes"] == "User warned for spam"
        assert data["moderator_id"] is not None
        assert "resolved_at" in data

    def test_resolve_moderation_item_unauthenticated(self, client, existing_moderation_item):
        """Resolving a moderation item without authentication should fail."""
        response = client.patch(
            f"/moderation/{existing_moderation_item.id}/resolve",
            json={"resolution_notes": "Test"},
        )
        assert response.status_code == 401

    def test_resolve_moderation_item_not_found(self, client, auth_headers):
        """Resolving a non-existent moderation item should return 404."""
        response = client.patch(
            "/moderation/99999/resolve",
            json={"resolution_notes": "Test"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_resolve_moderation_item_already_resolved(self, client, auth_headers, db_session):
        """Resolving an already-resolved item should fail or be idempotent."""
        resolved_item = ModerationItem(
            id=99,
            community_id=1,
            reported_user_id=2,
            reporter_id=1,
            reason="spam",
            description="Already resolved",
            priority=ModerationPriority.LOW,
            status=ModerationStatus.RESOLVED,
            moderator_id=1,
            resolution_notes="Already handled",
        )
        db_session.add(resolved_item)
        db_session.commit()

        response = client.patch(
            f"/moderation/{resolved_item.id}/resolve",
            json={"resolution_notes": "Trying to resolve again"},
            headers=auth_headers,
        )
        # Should return 400 (bad request) or 409 (conflict)
        assert response.status_code in (400, 409)

    def test_resolve_moderation_item_without_notes(self, client, auth_headers, existing_moderation_item):
        """Resolving a moderation item without resolution notes."""
        response = client.patch(
            f"/moderation/{existing_moderation_item.id}/resolve",
            json={},
            headers=auth_headers,
        )
        # Should either succeed with default or fail with 422
        assert response.status_code in (200, 422)

    def test_resolve_moderation_item_with_action_taken(self, client, auth_headers, existing_moderation_item):
        """Resolving with a specific action_taken value."""
        response = client.patch(
            f"/moderation/{existing_moderation_item.id}/resolve",
            json={
                "resolution_notes": "User banned for repeated spam",
                "action_taken": "ban",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resolved"
        assert data["action_taken"] == "ban"

    def test_resolve_moderation_item_dismiss(self, client, auth_headers, existing_moderation_item):
        """Resolving a moderation item by dismissing it."""
        response = client.patch(
            f"/moderation/{existing_moderation_item.id}/resolve",
            json={
                "resolution_notes": "No action needed, false report",
                "action_taken": "dismiss",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resolved"
        assert data["action_taken"] == "dismiss"

    def test_resolve_moderation_item_sets_moderator(self, client, auth_headers, existing_moderation_item, test_user):
        """Resolving should set the moderator_id to the current user."""
        response = client.patch(
            f"/moderation/{existing_moderation_item.id}/resolve",
            json={"resolution_notes": "Resolved by test moderator"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["moderator_id"] == test_user.id

    def test_resolve_moderation_item_sets_resolved_at(self, client, auth_headers, existing_moderation_item):
        """Resolving should set the resolved_at timestamp."""
        response = client.patch(
            f"/moderation/{existing_moderation_item.id}/resolve",
            json={"resolution_notes": "Resolved"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["resolved_at"] is not None

    def test_resolve_moderation_item_invalid_action(self, client, auth_headers, existing_moderation_item):
        """Resolving with an invalid action_taken should fail."""
        response = client.patch(
            f"/moderation/{existing_moderation_item.id}/resolve",
            json={
                "resolution_notes": "Test",
                "action_taken": "invalid_action",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_resolve_moderation_item_notes_too_long(self, client, auth_headers, existing_moderation_item):
        """Resolving with excessively long resolution notes should fail."""
        response = client.patch(
            f"/moderation/{existing_moderation_item.id}/resolve",
            json={"resolution_notes": "x" * 10000},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_resolve_moderation_item_invalid_id_format(self, client, auth_headers):
        """Resolving with a non-integer ID should return 422."""
        response = client.patch(
            "/moderation/abc/resolve",
            json={"resolution_notes": "Test"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_resolve_moderation_item_forbidden_for_non_moderator(self, client, db_session):
        """Non-moderator users should not be able to resolve items."""
        # Create a non-moderator user
        regular_user = User(
            id=2,
            username="regularuser",
            email="regular@test.com",
            hashed_password="fakehashedpassword",
            is_active=True,
            is_moderator=False,
        )
        db_session.add(regular_user)
        db_session.commit()

        # Create a pending moderation item
        item = ModerationItem(
            id=50,
            community_id=1,
            reported_user_id=3,
            reporter_id=1,
            reason="spam",
            description="Test",
            priority=ModerationPriority.LOW,
            status=ModerationStatus.PENDING,
        )
        db_session.add(item)
        db_session.commit()

        # Generate token for non-moderator
        access_token = create_access_token(data={"sub": str(regular_user.id)})
        headers = {"Authorization": f"Bearer {access_token}"}

        response = client.patch(
            f"/moderation/{item.id}/resolve",
            json={"resolution_notes": "Trying to resolve"},
            headers=headers,
        )
        assert response.status_code == 403
