"""Tests for compliance API endpoints."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from compliance.api.policies import reset_store as reset_policies
from compliance.api.violations import reset_store as reset_violations
from compliance.main import app


@pytest.fixture(autouse=True)
def reset_stores():
    reset_policies()
    reset_violations()
    yield
    reset_policies()
    reset_violations()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_check(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestPolicyEndpoints:
    def test_create_policy(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/policies",
            json={
                "name": "Test Policy",
                "description": "A test policy",
                "severity": "high",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Policy"
        assert data["id"].startswith("pol_")

    def test_list_policies(self, client: TestClient) -> None:
        client.post(
            "/api/v1/policies",
            json={"name": "Policy 1", "severity": "medium"},
        )
        response = client.get("/api/v1/policies")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_policy(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/v1/policies",
            json={"name": "Test Policy"},
        )
        policy_id = create_resp.json()["id"]
        response = client.get(f"/api/v1/policies/{policy_id}")
        assert response.status_code == 200
        assert response.json()["id"] == policy_id

    def test_get_policy_not_found(self, client: TestClient) -> None:
        response = client.get("/api/v1/policies/nonexistent")
        assert response.status_code == 404

    def test_delete_policy(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/v1/policies",
            json={"name": "Delete Me"},
        )
        policy_id = create_resp.json()["id"]
        response = client.delete(f"/api/v1/policies/{policy_id}")
        assert response.status_code == 204


class TestViolationEndpoints:
    def test_create_violation(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/violations",
            json={
                "content_id": "content_1",
                "source": "mailchimp",
                "rule": "unsubscribe_missing",
                "severity": "high",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content_id"] == "content_1"
        assert data["id"].startswith("vio_")

    def test_list_violations(self, client: TestClient) -> None:
        client.post(
            "/api/v1/violations",
            json={
                "content_id": "content_1",
                "source": "mailchimp",
                "rule": "test_rule",
            },
        )
        response = client.get("/api/v1/violations")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_resolve_violation(self, client: TestClient) -> None:
        create_resp = client.post(
            "/api/v1/violations",
            json={
                "content_id": "content_1",
                "source": "mailchimp",
                "rule": "test_rule",
            },
        )
        violation_id = create_resp.json()["id"]
        response = client.put(
            f"/api/v1/violations/{violation_id}/resolve",
            json={"resolution": "Fixed the issue"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "resolved"


class TestScanEndpoint:
    def test_trigger_scan(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/monitor/scan",
            json={
                "campaigns": [
                    {
                        "id": "camp_1",
                        "source": "mailchimp",
                        "content": "Buy now!",
                        "channel": "email",
                    }
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "succeeded"
        assert "metrics" in data
