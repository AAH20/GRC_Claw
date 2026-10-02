"""Appeal management endpoint tests."""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from content_moderation.models.schemas import AppealSubmission


def test_submit_appeal(client: TestClient) -> None:
    """Test appeal submission endpoint."""
    submission = AppealSubmission(
        moderation_result_id=uuid4(),
        user_id="user-123",
        reason="This content was incorrectly flagged as inappropriate",
        evidence={"context": "Educational content about art history"},
    )
    response = client.post("/api/v1/appeals", json=submission.model_dump(mode="json"))
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == "user-123"
    assert data["status"] == "pending"


def test_get_appeal(client: TestClient) -> None:
    """Test getting appeal status."""
    submission = AppealSubmission(
        moderation_result_id=uuid4(),
        user_id="user-456",
        reason="False positive on my content",
    )
    create_response = client.post("/api/v1/appeals", json=submission.model_dump(mode="json"))
    appeal_id = create_response.json()["id"]

    response = client.get(f"/api/v1/appeals/{appeal_id}")
    assert response.status_code == 200
    assert response.json()["id"] == appeal_id


def test_review_appeal(client: TestClient) -> None:
    """Test appeal review endpoint."""
    submission = AppealSubmission(
        moderation_result_id=uuid4(),
        user_id="user-789",
        reason="Please review this decision, I believe it was made in error",
    )
    create_response = client.post("/api/v1/appeals", json=submission.model_dump(mode="json"))
    appeal_id = create_response.json()["id"]

    response = client.post(f"/api/v1/appeals/{appeal_id}/review")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["approved", "rejected", "escalated", "under_review"]
