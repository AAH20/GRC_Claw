"""Tests for GRC_Claw FastAPI endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from grcclaw.api import app


client = TestClient(app)


class TestHealth:
    def test_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_ready(self):
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"


class TestPolicyEndpoints:
    def test_create_policy(self):
        response = client.post("/api/v1/policies", json={
            "name": "test-policy",
            "version": "1.0.0",
            "owner": "test@example.com",
            "rules": [
                {
                    "name": "allow-read",
                    "description": "Allow read",
                    "condition": {"type": "cedar", "expression": 'principal.action == "read"'},
                    "effect": "allow",
                    "priority": 100,
                }
            ],
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test-policy"
        assert data["status"] == "draft"

    def test_list_policies(self):
        response = client.get("/api/v1/policies")
        assert response.status_code == 200
        assert "data" in response.json()

    def test_get_policy_not_found(self):
        response = client.get("/api/v1/policies/nonexistent")
        assert response.status_code == 404

    def test_validate_policy_not_found(self):
        response = client.post("/api/v1/policies/nonexistent/validate")
        assert response.status_code == 404


class TestEnforcementEndpoints:
    def test_evaluate_action(self):
        # First create and deploy a policy
        client.post("/api/v1/policies", json={
            "name": "test-enforce-policy",
            "version": "1.0.0",
            "owner": "test@example.com",
            "rules": [
                {
                    "name": "allow-read",
                    "description": "Allow read",
                    "condition": {"type": "cedar", "expression": 'principal.action == "read"'},
                    "effect": "allow",
                    "priority": 100,
                }
            ],
        })
        response = client.post("/api/v1/enforcements", json={
            "agent_id": "agent-1",
            "action": "read",
            "resource": "data",
            "environment": "production",
        })
        assert response.status_code == 200
        data = response.json()
        assert "effect" in data
        assert "reason" in data

    def test_enforcement_stats(self):
        response = client.get("/api/v1/enforcements/stats")
        assert response.status_code == 200
        assert "total" in response.json()


class TestEvidenceEndpoints:
    def test_submit_evidence(self):
        response = client.post("/api/v1/evidence", json={
            "type": "policy_evaluation",
            "subject": {"agent_id": "agent-1", "action": "export"},
            "decision": {"effect": "deny", "reason": "PII blocked"},
            "compliance_tags": ["iso-42001:6.1"],
        })
        assert response.status_code == 201
        data = response.json()
        assert data["evidence_id"].startswith("EVD-")

    def test_list_evidence(self):
        response = client.get("/api/v1/evidence")
        assert response.status_code == 200
        assert "data" in response.json()

    def test_get_evidence_not_found(self):
        response = client.get("/api/v1/evidence/nonexistent")
        assert response.status_code == 404


class TestAssessmentEndpoints:
    def test_create_assessment(self):
        response = client.post("/api/v1/assessments", json={
            "system_id": "test-system",
            "assessment_type": "fairness",
            "framework": "iso-42001",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["assessment_id"].startswith("ASSESS-")
        assert data["system_id"] == "test-system"

    def test_list_assessments(self):
        response = client.get("/api/v1/assessments")
        assert response.status_code == 200
        assert "data" in response.json()


class TestComplianceEndpoints:
    def test_list_frameworks(self):
        response = client.get("/api/v1/compliance/frameworks")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) > 0

    def test_get_framework_controls(self):
        response = client.get("/api/v1/compliance/frameworks/iso-42001/controls")
        assert response.status_code == 200
        assert "controls" in response.json()

    def test_get_compliance_mapping(self):
        response = client.get("/api/v1/compliance/mappings/GRC-CTRL-001")
        assert response.status_code == 200
        assert response.json()["control_id"] == "GRC-CTRL-001"


class TestAuditEndpoints:
    def test_query_audit(self):
        response = client.get("/api/v1/audit")
        assert response.status_code == 200
        assert "data" in response.json()

    def test_verify_audit(self):
        response = client.get("/api/v1/audit/verify")
        assert response.status_code == 200
        assert response.json()["valid"] is True

    def test_merkle_root(self):
        response = client.get("/api/v1/audit/merkle-root")
        assert response.status_code == 200
        assert "merkle_root" in response.json()
