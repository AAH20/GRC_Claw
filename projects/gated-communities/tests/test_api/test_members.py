"""
Comprehensive API tests for the Members endpoints.

Tests cover:
- POST /members (add member)
- GET /members (list members)
- PATCH /members/{id}/role (update member role)
"""

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Return a TestClient for the application."""
    from app.main import app
    return TestClient(app)


@pytest.fixture
def sample_member_payload():
    """Return a valid payload for creating a member."""
    return {
        "user_id": "user-123",
        "community_id": "community-456",
        "role": "member",
    }


@pytest.fixture
def created_member(client, sample_member_payload):
    """Create a member and return the response JSON."""
    response = client.post("/members", json=sample_member_payload)
    assert response.status_code == 201
    return response.json()


# ---------------------------------------------------------------------------
# POST /members — test_add_member
# ---------------------------------------------------------------------------

class TestAddMember:
    """Tests for POST /members endpoint."""

    def test_add_member_success(self, client, sample_member_payload):
        """Successfully adding a member returns 201 with member data."""
        response = client.post("/members", json=sample_member_payload)

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == sample_member_payload["user_id"]
        assert data["community_id"] == sample_member_payload["community_id"]
        assert data["role"] == sample_member_payload["role"]
        assert "id" in data
        assert "created_at" in data

    def test_add_member_missing_user_id(self, client):
        """Missing user_id returns 422 validation error."""
        payload = {
            "community_id": "community-456",
            "role": "member",
        }
        response = client.post("/members", json=payload)

        assert response.status_code == 422

    def test_add_member_missing_community_id(self, client):
        """Missing community_id returns 422 validation error."""
        payload = {
            "user_id": "user-123",
            "role": "member",
        }
        response = client.post("/members", json=payload)

        assert response.status_code == 422

    def test_add_member_invalid_role(self, client):
        """Invalid role value returns 422 validation error."""
        payload = {
            "user_id": "user-123",
            "community_id": "community-456",
            "role": "superadmin",
        }
        response = client.post("/members", json=payload)

        assert response.status_code == 422

    def test_add_member_duplicate(self, client, sample_member_payload):
        """Adding a duplicate member returns 409 conflict."""
        # First creation should succeed
        response1 = client.post("/members", json=sample_member_payload)
        assert response1.status_code == 201

        # Second creation should conflict
        response2 = client.post("/members", json=sample_member_payload)
        assert response2.status_code == 409

    def test_add_member_empty_body(self, client):
        """Empty request body returns 422 validation error."""
        response = client.post("/members", json={})

        assert response.status_code == 422

    def test_add_member_extra_fields_ignored(self, client):
        """Extra fields in payload are ignored or rejected gracefully."""
        payload = {
            "user_id": "user-789",
            "community_id": "community-101",
            "role": "member",
            "unexpected_field": "should_be_ignored",
        }
        response = client.post("/members", json=payload)

        # Should either succeed (ignoring extra) or return 422
        assert response.status_code in (201, 422)

    def test_add_member_response_content_type(self, client, sample_member_payload):
        """Response has correct content-type header."""
        response = client.post("/members", json=sample_member_payload)

        assert response.status_code == 201
        assert "application/json" in response.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# GET /members — test_list_members
# ---------------------------------------------------------------------------

class TestListMembers:
    """Tests for GET /members endpoint."""

    def test_list_members_empty(self, client):
        """Listing members with no members returns empty list."""
        response = client.get("/members")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_members_returns_created(self, client, created_member):
        """Listing members returns previously created members."""
        response = client.get("/members")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        member_ids = [m["id"] for m in data]
        assert created_member["id"] in member_ids

    def test_list_members_filter_by_community(self, client, sample_member_payload):
        """Filtering members by community_id returns only matching members."""
        # Create a member
        client.post("/members", json=sample_member_payload)

        # Filter by the community_id
        response = client.get(f"/members?community_id={sample_member_payload['community_id']}")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        for member in data:
            assert member["community_id"] == sample_member_payload["community_id"]

    def test_list_members_filter_by_user(self, client, sample_member_payload):
        """Filtering members by user_id returns only matching members."""
        client.post("/members", json=sample_member_payload)

        response = client.get(f"/members?user_id={sample_member_payload['user_id']}")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        for member in data:
            assert member["user_id"] == sample_member_payload["user_id"]

    def test_list_members_pagination(self, client):
        """Pagination parameters limit and offset results correctly."""
        response = client.get("/members?limit=5&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

    def test_list_members_response_structure(self, client, created_member):
        """Each member in the list has the expected fields."""
        response = client.get("/members")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

        member = data[0]
        expected_fields = {"id", "user_id", "community_id", "role", "created_at"}
        assert expected_fields.issubset(set(member.keys()))

    def test_list_members_content_type(self, client):
        """Response has correct content-type header."""
        response = client.get("/members")

        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")


# ---------------------------------------------------------------------------
# PATCH /members/{id}/role — test_update_member_role
# ---------------------------------------------------------------------------

class TestUpdateMemberRole:
    """Tests for PATCH /members/{id}/role endpoint."""

    def test_update_member_role_success(self, client, created_member):
        """Successfully updating a member role returns 200 with updated data."""
        member_id = created_member["id"]
        new_role = "admin"

        response = client.patch(f"/members/{member_id}/role", json={"role": new_role})

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == member_id
        assert data["role"] == new_role
        # Other fields should remain unchanged
        assert data["user_id"] == created_member["user_id"]
        assert data["community_id"] == created_member["community_id"]

    def test_update_member_role_not_found(self, client):
        """Updating role for non-existent member returns 404."""
        response = client.patch("/members/nonexistent-id/role", json={"role": "admin"})

        assert response.status_code == 404

    def test_update_member_role_invalid_role(self, client, created_member):
        """Updating to an invalid role returns 422."""
        member_id = created_member["id"]

        response = client.patch(f"/members/{member_id}/role", json={"role": "invalid_role"})

        assert response.status_code == 422

    def test_update_member_role_missing_role_field(self, client, created_member):
        """Missing role field in request body returns 422."""
        member_id = created_member["id"]

        response = client.patch(f"/members/{member_id}/role", json={})

        assert response.status_code == 422

    def test_update_member_role_persists(self, client, created_member):
        """Role update persists — verified by fetching the member afterwards."""
        member_id = created_member["id"]
        new_role = "moderator"

        # Update the role
        patch_response = client.patch(f"/members/{member_id}/role", json={"role": new_role})
        assert patch_response.status_code == 200

        # Fetch all members and verify the role was updated
        list_response = client.get("/members")
        assert list_response.status_code == 200
        members = list_response.json()

        updated_member = next((m for m in members if m["id"] == member_id), None)
        assert updated_member is not None
        assert updated_member["role"] == new_role

    def test_update_member_role_same_role(self, client, created_member):
        """Updating to the same role is idempotent and returns 200."""
        member_id = created_member["id"]
        same_role = created_member["role"]

        response = client.patch(f"/members/{member_id}/role", json={"role": same_role})

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == same_role

    def test_update_member_role_invalid_id_format(self, client):
        """Updating role with invalid ID format returns 422 or 404."""
        response = client.patch("/members/!!!invalid!!! /role", json={"role": "admin"})

        assert response.status_code in (404, 422)
