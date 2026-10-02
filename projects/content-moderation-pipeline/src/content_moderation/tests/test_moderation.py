"""Moderation endpoint tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from content_moderation.models.schemas import ContentType, ModerationRequest


def test_moderate_text(client: TestClient) -> None:
    """Test text moderation endpoint."""
    request = ModerationRequest(
        content="Hello, this is a test message",
        content_type=ContentType.TEXT,
    )
    response = client.post("/api/v1/moderate/text", json=request.model_dump())
    assert response.status_code == 200
    data = response.json()
    assert "action" in data
    assert "confidence" in data
    assert data["content_type"] == "text"


def test_moderate_image(client: TestClient) -> None:
    """Test image moderation endpoint."""
    request = ModerationRequest(
        content="https://example.com/image.jpg",
        content_type=ContentType.IMAGE,
    )
    response = client.post("/api/v1/moderate/image", json=request.model_dump())
    assert response.status_code == 200
    data = response.json()
    assert "action" in data
    assert data["content_type"] == "image"


def test_moderate_video(client: TestClient) -> None:
    """Test video moderation endpoint."""
    request = ModerationRequest(
        content="https://example.com/video.mp4",
        content_type=ContentType.VIDEO,
    )
    response = client.post("/api/v1/moderate/video", json=request.model_dump())
    assert response.status_code == 200
    data = response.json()
    assert "action" in data
    assert data["content_type"] == "video"


def test_moderate_batch(client: TestClient) -> None:
    """Test batch moderation endpoint."""
    payload = {
        "items": [
            {"content": "Test text 1", "content_type": "text"},
            {"content": "Test text 2", "content_type": "text"},
        ],
        "priority": "normal",
    }
    response = client.post("/api/v1/moderate/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_processed"] == 2
    assert len(data["results"]) == 2
