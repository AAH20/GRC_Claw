"""Integration tests for API endpoints."""
from __future__ import annotations

from fastapi.testclient import TestClient


class TestHealthIntegration:
    def test_health_check(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_readiness_check(self, client: TestClient) -> None:
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json() == {"ready": True}

    def test_liveness_check(self, client: TestClient) -> None:
        response = client.get("/live")
        assert response.status_code == 200
        assert response.json() == {"alive": True}


class TestTiersIntegration:
    def test_create_tier(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/tiers",
            json={"name": "Gold", "level": "gold", "description": "Gold tier", "price": 9.99, "benefits": ["priority_support"]},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Gold"
        assert data["level"] == "gold"

    def test_list_tiers(self, client: TestClient) -> None:
        response = client.get("/api/v1/tiers")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestModerationIntegration:
    def test_create_moderation_item(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/moderation/queue",
            json={"content": "Test content", "content_type": "text", "author_id": "user123", "community_id": "community456"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "Test content"
        assert data["status"] == "pending"

    def test_get_moderation_queue(self, client: TestClient) -> None:
        response = client.get("/api/v1/moderation/queue")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestWebSocketIntegration:
    def test_websocket_connection(self, client: TestClient) -> None:
        with client.websocket_connect("/ws/community123") as websocket:
            websocket.send_text('{"type": "test"}')
            data = websocket.receive_json()
            assert data["type"] == "message"
            assert data["community_id"] == "community123"


class TestExportIntegration:
    def test_export_members_csv(self, client: TestClient) -> None:
        response = client.get("/api/v1/export/members?format=csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    def test_export_members_json(self, client: TestClient) -> None:
        response = client.get("/api/v1/export/members?format=json")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]


class TestSearchIntegration:
    def test_search(self, client: TestClient) -> None:
        response = client.get("/api/v1/search?q=python")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
        assert data["query"] == "python"


class TestBulkOperationsIntegration:
    def test_bulk_member_update(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/bulk/members",
            json={"member_ids": ["1", "2", "3"], "action": "update_role", "value": "moderator"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "failed" in data


class TestAuditIntegration:
    def test_create_audit_log(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/audit",
            json={"action": "member_created", "user_id": "user123", "resource_type": "member", "resource_id": "member456", "details": {"role": "admin"}},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["action"] == "member_created"

    def test_list_audit_logs(self, client: TestClient) -> None:
        response = client.get("/api/v1/audit")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
