"""Tests for remediation API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_remediate_violation(client: TestClient) -> None:
    """Test remediating a violation."""
    policy_data = {"name": "Test Policy", "category": "security"}
    policy_response = client.post("/api/v1/policies", json=policy_data)
    policy_id = policy_response.json()["id"]

    violation_data = {
        "policy_id": policy_id,
        "title": "Test Violation",
        "severity": "high",
    }
    violation_response = client.post("/api/v1/violations", json=violation_data)
    violation_id = violation_response.json()["id"]

    remediation_data = {
        "action_type": "revoke_access",
        "description": "Revoke user access to restricted resource",
        "auto_execute": True,
    }
    response = client.post(f"/api/v1/remediate/{violation_id}", json=remediation_data)
    assert response.status_code == 200
    data = response.json()
    assert data["action_type"] == "revoke_access"
    assert data["status"] == "completed"


def test_remediate_violation_not_found(client: TestClient) -> None:
    """Test remediating a non-existent violation."""
    remediation_data = {
        "action_type": "test_action",
        "description": "Test remediation",
    }
    response = client.post(
        "/api/v1/remediate/00000000-0000-0000-0000-000000000000",
        json=remediation_data,
    )
    assert response.status_code == 404


def test_compliance_report(client: TestClient) -> None:
    """Test getting the comprehensive compliance report."""
    response = client.get("/api/v1/reports/compliance")
    assert response.status_code == 200
    data = response.json()
    assert "overall_compliance_score" in data
    assert "risk_level" in data
    assert "total_policies" in data
    assert "total_violations" in data
