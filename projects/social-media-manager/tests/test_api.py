"""Tests for the FastAPI application and API routes."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from social_media_manager.api.store import post_store
from social_media_manager.main import app


@pytest.fixture(autouse=True)
def _clean_store() -> None:
    """Reset the in-memory post store between tests."""
    post_store._items.clear()


@pytest.fixture
def client() -> TestClient:
    """Return a test client bound to the application."""
    return TestClient(app)


class TestHealth:
    """Health and agent-listing endpoints."""

    def test_health(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert "version" in body

    def test_list_agents(self, client: TestClient) -> None:
        response = client.get("/api/v1/agents")
        assert response.status_code == 200
        names = {a["name"] for a in response.json()["agents"]}
        assert names == {
            "content_creation",
            "scheduling",
            "engagement",
            "social_listening",
            "influencer_identification",
            "performance_analytics",
        }


class TestPostRoutes:
    """CRUD behaviour for posts."""

    def test_create_and_get_post(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/posts",
            json={"platform": "twitter", "content": "Hello world"},
        )
        assert response.status_code == 201
        post = response.json()
        assert post["status"] == "draft"

        fetched = client.get(f"/api/v1/posts/{post['id']}")
        assert fetched.status_code == 200
        assert fetched.json()["content"] == "Hello world"

    def test_scheduled_post_status(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/posts",
            json={
                "platform": "linkedin",
                "content": "Scheduled",
                "scheduled_at": "2026-05-01T12:00:00Z",
            },
        )
        assert response.status_code == 201
        assert response.json()["status"] == "scheduled"

    def test_blank_content_rejected(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/posts", json={"platform": "twitter", "content": "   "}
        )
        assert response.status_code == 422

    def test_unsupported_platform_rejected(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/posts", json={"platform": "myspace", "content": "hi"}
        )
        assert response.status_code == 422

    def test_list_pagination(self, client: TestClient) -> None:
        for i in range(5):
            client.post(
                "/api/v1/posts",
                json={"platform": "facebook", "content": f"post {i}"},
            )
        response = client.get("/api/v1/posts?limit=2&offset=0")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 5
        assert len(body["items"]) == 2

    def test_update_status(self, client: TestClient) -> None:
        created = client.post(
            "/api/v1/posts", json={"platform": "tiktok", "content": "video"}
        ).json()
        response = client.patch(
            f"/api/v1/posts/{created['id']}/status?new_status=published"
        )
        assert response.status_code == 200
        assert response.json()["status"] == "published"

    def test_delete_post(self, client: TestClient) -> None:
        created = client.post(
            "/api/v1/posts", json={"platform": "twitter", "content": "delete me"}
        ).json()
        assert client.delete(f"/api/v1/posts/{created['id']}").status_code == 204
        assert client.get(f"/api/v1/posts/{created['id']}").status_code == 404

    def test_get_missing_post_404(self, client: TestClient) -> None:
        assert client.get("/api/v1/posts/does-not-exist").status_code == 404


class TestAnalyticsRoutes:
    """Analytics aggregation endpoints."""

    def test_overview_empty(self, client: TestClient) -> None:
        response = client.get("/api/v1/analytics")
        assert response.status_code == 200
        assert response.json()["total_posts"] == 0

    def test_overview_counts(self, client: TestClient) -> None:
        client.post("/api/v1/posts", json={"platform": "twitter", "content": "a"})
        client.post("/api/v1/posts", json={"platform": "twitter", "content": "b"})
        client.post("/api/v1/posts", json={"platform": "linkedin", "content": "c"})
        body = client.get("/api/v1/analytics").json()
        assert body["total_posts"] == 3
        assert body["posts_by_platform"]["twitter"] == 2

    def test_platform_analytics(self, client: TestClient) -> None:
        client.post(
            "/api/v1/posts",
            json={
                "platform": "instagram",
                "content": "hello",
                "metadata": {"impressions": 1000, "likes": 50, "comments": 5, "shares": 2},
            },
        )
        response = client.get("/api/v1/analytics/instagram")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["totals"]["impressions"] == 1000

    def test_platform_analytics_missing_404(self, client: TestClient) -> None:
        assert client.get("/api/v1/analytics/tiktok").status_code == 404


class TestAgentInvocation:
    """Direct agent invocation endpoint."""

    def test_invoke_content_agent(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/agents/content_creation/invoke",
            json={"payload": {"topic": "ai", "platform": "twitter"}},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_invoke_unknown_agent_404(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/agents/nonexistent/invoke", json={"payload": {}}
        )
        assert response.status_code == 404

    def test_invoke_with_bad_payload_reports_failure(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/agents/scheduling/invoke", json={"payload": {}}
        )
        assert response.status_code == 200
        assert response.json()["success"] is False
