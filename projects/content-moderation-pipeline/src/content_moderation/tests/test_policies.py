"""Policy management endpoint tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from content_moderation.models.schemas import (
    ContentType,
    ModerationAction,
    Policy,
    PolicyRule,
    PolicySeverity,
)


def _create_test_policy() -> Policy:
    """Create a test policy for testing.

    Returns:
        Test policy instance.
    """
    return Policy(
        name="Test Policy",
        description="A test policy",
        rules=[
            PolicyRule(
                name="No spam",
                description="Block spam content",
                pattern="spam|buy now",
                severity=PolicySeverity.HIGH,
                action=ModerationAction.BLOCK,
            )
        ],
        content_types=[ContentType.TEXT],
    )


def test_create_policy(client: TestClient) -> None:
    """Test policy creation endpoint."""
    policy = _create_test_policy()
    response = client.post("/api/v1/policies", json=policy.model_dump(mode="json"))
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Policy"
    assert len(data["rules"]) == 1


def test_list_policies(client: TestClient) -> None:
    """Test policy listing endpoint."""
    response = client.get("/api/v1/policies")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_policy(client: TestClient) -> None:
    """Test getting a specific policy."""
    policy = _create_test_policy()
    create_response = client.post("/api/v1/policies", json=policy.model_dump(mode="json"))
    policy_id = create_response.json()["id"]

    response = client.get(f"/api/v1/policies/{policy_id}")
    assert response.status_code == 200
    assert response.json()["id"] == policy_id


def test_update_policy(client: TestClient) -> None:
    """Test policy update endpoint."""
    policy = _create_test_policy()
    create_response = client.post("/api/v1/policies", json=policy.model_dump(mode="json"))
    policy_id = create_response.json()["id"]

    policy.name = "Updated Policy"
    response = client.put(
        f"/api/v1/policies/{policy_id}",
        json=policy.model_dump(mode="json"),
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Policy"


def test_delete_policy(client: TestClient) -> None:
    """Test policy deletion endpoint."""
    policy = _create_test_policy()
    create_response = client.post("/api/v1/policies", json=policy.model_dump(mode="json"))
    policy_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/policies/{policy_id}")
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/policies/{policy_id}")
    assert get_response.status_code == 404
