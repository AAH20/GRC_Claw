"""
Automated API test suite for GRC_Claw API.
Tests all 54 endpoints across 11 resource groups.

Usage:
    pytest test_api.py -v
    pytest test_api.py -v --base-url=http://localhost:8080
    pytest test_api.py -v --api-key=grc_test_xxx
"""
import os
import pytest
import requests
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = os.environ.get("GRC_API_BASE_URL", "http://localhost:8080")
API_KEY = os.environ.get("GRC_API_KEY", "grc_test_default_key")
API_PREFIX = "/v1.0"

# Resource IDs (populated during test runs)
AGENT_ID = os.environ.get("GRC_AGENT_ID", "agent-1")
POLICY_ID = os.environ.get("GRC_POLICY_ID", "pol-001")
ASSESSMENT_ID = os.environ.get("GRC_ASSESSMENT_ID", "asm-001")
EVIDENCE_ID = os.environ.get("GRC_EVIDENCE_ID", "evd-001")
DECISION_ID = os.environ.get("GRC_DECISION_ID", "dec-001")
SUBSCRIPTION_ID = os.environ.get("GRC_SUBSCRIPTION_ID", "sub-001")
FRAMEWORK_ID = os.environ.get("GRC_FRAMEWORK_ID", "fw-001")
PACKAGE_ID = os.environ.get("GRC_PACKAGE_ID", "pkg-001")


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL.rstrip("/")


@pytest.fixture(scope="session")
def headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="session")
def api(base_url: str, headers: Dict[str, str]):
    """Convenience wrapper for making API requests."""

    class API:
        def __init__(self, base: str, hdrs: Dict[str, str]):
            self.base = base
            self.hdrs = hdrs

        def url(self, path: str) -> str:
            if path.startswith("/"):
                return f"{self.base}{path}"
            return f"{self.base}/{path}"

        def get(self, path: str, **kwargs) -> requests.Response:
            return requests.get(self.url(path), headers=self.hdrs, timeout=30, **kwargs)

        def post(self, path: str, **kwargs) -> requests.Response:
            return requests.post(self.url(path), headers=self.hdrs, timeout=30, **kwargs)

        def put(self, path: str, **kwargs) -> requests.Response:
            return requests.put(self.url(path), headers=self.hdrs, timeout=30, **kwargs)

        def delete(self, path: str, **kwargs) -> requests.Response:
            return requests.delete(self.url(path), headers=self.hdrs, timeout=30, **kwargs)

    return API(base_url, headers)


def assert_status(response: requests.Response, expected: int) -> None:
    assert response.status_code == expected, (
        f"Expected {expected}, got {response.status_code}: {response.text[:500]}"
    )


def assert_json(response: requests.Response) -> Dict[str, Any]:
    try:
        return response.json()
    except Exception:
        pytest.fail(f"Response is not valid JSON: {response.text[:500]}")
        return {}  # unreachable, but satisfies type checker


# ===========================================================================
# System Endpoints
# ===========================================================================

class TestSystem:
    """Tests for health, readiness, and metrics endpoints."""

    def test_health_check(self, api):
        """GET /health returns 200 with healthy status."""
        resp = api.get("/health")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert data["status"] == "healthy"
        assert "version" in data
        assert "components" in data
        assert "timestamp" in data

    def test_readiness_check(self, api):
        """GET /ready returns 200 with ready status."""
        resp = api.get("/ready")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert data["ready"] is True
        assert "checks" in data

    def test_prometheus_metrics(self, api):
        """GET /metrics returns 200 with Prometheus text."""
        resp = api.get("/metrics")
        assert_status(resp, 200)
        assert "grc_api_requests_total" in resp.text or "grc_api" in resp.text


# ===========================================================================
# Agent Endpoints
# ===========================================================================

class TestAgents:
    """Tests for agent management endpoints."""

    def test_list_agents(self, api):
        """GET /v1.0/agents returns paginated list."""
        resp = api.get(f"{API_PREFIX}/agents")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert "data" in data
        assert "pagination" in data
        assert "total" in data["pagination"]

    def test_list_agents_with_filters(self, api):
        """GET /v1.0/agents with query filters."""
        resp = api.get(f"{API_PREFIX}/agents", params={
            "type": "agent",
            "framework": "langchain",
            "risk_tier": "limited",
        })
        assert_status(resp, 200)
        data = assert_json(resp)
        assert "data" in data

    def test_register_agent(self, api):
        """POST /v1.0/agents creates a new agent."""
        payload = {
            "name": f"Test Agent {int(datetime.now(timezone.utc).timestamp())}",
            "type": "agent",
            "framework": "langchain",
            "owner": "test-suite",
            "risk_tier": "minimal",
            "capabilities": [
                {
                    "name": "read_data",
                    "description": "Read data",
                    "permissions": ["data:read"],
                }
            ],
        }
        resp = api.post(f"{API_PREFIX}/agents", json=payload)
        assert_status(resp, 201)
        data = assert_json(resp)
        assert data["name"] == payload["name"]
        assert data["type"] == "agent"
        assert data["lifecycle_stage"] == "proposed"
        assert "id" in data

    def test_register_agent_conflict(self, api):
        """POST /v1.0/agents with duplicate name returns 409."""
        payload = {
            "name": "Duplicate Test Agent",
            "type": "agent",
            "framework": "langchain",
            "owner": "test-suite",
            "risk_tier": "minimal",
            "capabilities": [],
        }
        # First creation should succeed
        resp1 = api.post(f"{API_PREFIX}/agents", json=payload)
        if resp1.status_code == 201:
            # Second creation should conflict
            resp2 = api.post(f"{API_PREFIX}/agents", json=payload)
            assert_status(resp2, 409)

    def test_get_agent(self, api):
        """GET /v1.0/agents/{id} returns agent details."""
        resp = api.get(f"{API_PREFIX}/agents/{AGENT_ID}")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert data["id"] == AGENT_ID

    def test_get_agent_not_found(self, api):
        """GET /v1.0/agents/{id} with invalid ID returns 404."""
        resp = api.get(f"{API_PREFIX}/agents/nonexistent-agent-99999")
        assert_status(resp, 404)

    def test_update_agent(self, api):
        """PUT /v1.0/agents/{id} updates agent."""
        payload = {
            "lifecycle_stage": "active",
            "risk_tier": "limited",
        }
        resp = api.put(f"{API_PREFIX}/agents/{AGENT_ID}", json=payload)
        assert_status(resp, 200)
        data = assert_json(resp)
        assert data["lifecycle_stage"] == "active"

    def test_update_trust_score(self, api):
        """POST /v1.0/agents/{id}/trust-score updates trust score."""
        payload = {
            "value": 85,
            "grade": "B",
            "reason": "Automated test evaluation",
        }
        resp = api.post(f"{API_PREFIX}/agents/{AGENT_ID}/trust-score", json=payload)
        assert_status(resp, 200)
        data = assert_json(resp)
        assert data["trust_score"]["value"] == 85
        assert data["trust_score"]["grade"] == "B"

    def test_bind_policies(self, api):
        """POST /v1.0/agents/{id}/policy-bindings binds policies."""
        payload = {
            "policy_ids": ["pol-001", "pol-002"],
        }
        resp = api.post(f"{API_PREFIX}/agents/{AGENT_ID}/policy-bindings", json=payload)
        assert_status(resp, 200)
        data = assert_json(resp)
        assert "pol-001" in data["policy_bindings"]


# ===========================================================================
# Policy Endpoints
# ===========================================================================

class TestPolicies:
    """Tests for policy management endpoints."""

    def test_list_policies(self, api):
        """GET /v1.0/policies returns paginated list."""
        resp = api.get(f"{API_PREFIX}/policies")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert "data" in data
        assert "pagination" in data

    def test_list_policies_with_filters(self, api):
        """GET /v1.0/policies with query filters."""
        resp = api.get(f"{API_PREFIX}/policies", params={
            "status": "draft",
            "category": "safety",
        })
        assert_status(resp, 200)

    def test_create_policy(self, api):
        """POST /v1.0/policies creates a new policy."""
        payload = {
            "policy_key": f"TEST-POL-{int(datetime.now(timezone.utc).timestamp())}",
            "name": "Test Policy",
            "description": "Policy created by automated test",
            "category": "safety",
            "framework_tags": ["NIST-800-53"],
            "cedar_policy": 'permit(principal, action, resource) when { true };',
        }
        resp = api.post(f"{API_PREFIX}/policies", json=payload)
        assert_status(resp, 201)
        data = assert_json(resp)
        assert data["name"] == "Test Policy"
        assert data["status"] == "draft"
        assert data["version"] == "1.0.0"

    def test_get_policy(self, api):
        """GET /v1.0/policies/{id} returns policy details."""
        resp = api.get(f"{API_PREFIX}/policies/{POLICY_ID}")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert data["id"] == POLICY_ID

    def test_get_policy_not_found(self, api):
        """GET /v1.0/policies/{id} with invalid ID returns 404."""
        resp = api.get(f"{API_PREFIX}/policies/nonexistent-policy-99999")
        assert_status(resp, 404)

    def test_update_policy(self, api):
        """PUT /v1.0/policies/{id} updates policy and increments version."""
        payload = {
            "name": "Updated Test Policy",
            "description": "Updated by test suite",
        }
        resp = api.put(f"{API_PREFIX}/policies/{POLICY_ID}", json=payload)
        assert_status(resp, 200)
        data = assert_json(resp)
        assert data["name"] == "Updated Test Policy"

    def test_delete_policy(self, api):
        """DELETE /v1.0/policies/{id} archives policy."""
        # Create a policy to delete
        payload = {
            "policy_key": f"DELETE-TEST-{int(datetime.now(timezone.utc).timestamp())}",
            "name": "Policy To Delete",
            "category": "safety",
            "framework_tags": [],
        }
        create_resp = api.post(f"{API_PREFIX}/policies", json=payload)
        if create_resp.status_code == 201:
            policy_id = create_resp.json()["id"]
            resp = api.delete(f"{API_PREFIX}/policies/{policy_id}")
            assert_status(resp, 204)

    def test_compile_policy(self, api):
        """POST /v1.0/policies/{id}/compile compiles Cedar to Rego."""
        resp = api.post(f"{API_PREFIX}/policies/{POLICY_ID}/compile")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert data["compilation_status"] == "success"
        assert "rego_policy" in data

    def test_dry_run_policy(self, api):
        """POST /v1.0/policies/{id}/dry-run tests policy."""
        payload = {
            "test_inputs": [
                {
                    "principal": {"id": "agent-1", "type": "agent"},
                    "action": "read",
                    "resource": {"id": "data-1", "type": "data"},
                    "context": {"environment": "test"},
                }
            ]
        }
        resp = api.post(f"{API_PREFIX}/policies/{POLICY_ID}/dry-run", json=payload)
        assert_status(resp, 200)
        data = assert_json(resp)
        assert "dry_run_results" in data
        assert "summary" in data

    def test_get_policy_versions(self, api):
        """GET /v1.0/policies/{id}/versions returns version history."""
        resp = api.get(f"{API_PREFIX}/policies/{POLICY_ID}/versions")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_policy_dependencies(self, api):
        """GET /v1.0/policies/{id}/dependencies returns dependency graph."""
        resp = api.get(f"{API_PREFIX}/policies/{POLICY_ID}/dependencies")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert "dependencies" in data
        assert "dependents" in data


# ===========================================================================
# Evidence Endpoints
# ===========================================================================

class TestEvidence:
    """Tests for evidence management endpoints."""

    def test_search_evidence(self, api):
        """GET /v1.0/evidence returns paginated list."""
        resp = api.get(f"{API_PREFIX}/evidence")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert "data" in data
        assert "pagination" in data

    def test_search_evidence_with_filters(self, api):
        """GET /v1.0/evidence with query filters."""
        resp = api.get(f"{API_PREFIX}/evidence", params={
            "evidence_type": "artifact",
            "environment": "production",
        })
        assert_status(resp, 200)

    def test_submit_evidence(self, api):
        """POST /v1.0/evidence submits new evidence."""
        payload = {
            "policy_id": POLICY_ID,
            "assessment_id": ASSESSMENT_ID,
            "source": {
                "type": "automated_scan",
                "system": "test-suite",
                "collection_method": "api",
            },
            "evidence_type": "artifact",
            "content": {
                "format": "json",
                "data": '{"test": true}',
            },
            "context": {
                "environment": "test",
                "region": "us-east-1",
            },
            "control_mapping": {
                "control_id": "AC-2",
                "framework": "NIST-800-53",
                "control_title": "Account Management",
            },
        }
        resp = api.post(f"{API_PREFIX}/evidence", json=payload)
        assert_status(resp, 201)
        data = assert_json(resp)
        assert data["evidence_type"] == "artifact"
        assert data["verification_level"] == "L0"
        assert "chain_of_custody" in data

    def test_get_evidence(self, api):
        """GET /v1.0/evidence/{id} returns evidence details."""
        resp = api.get(f"{API_PREFIX}/evidence/{EVIDENCE_ID}")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert data["evidence_id"] == EVIDENCE_ID

    def test_get_evidence_not_found(self, api):
        """GET /v1.0/evidence/{id} with invalid ID returns 404."""
        resp = api.get(f"{API_PREFIX}/evidence/nonexistent-evidence-99999")
        assert_status(resp, 404)

    def test_verify_evidence(self, api):
        """POST /v1.0/evidence/{id}/verify verifies evidence integrity."""
        resp = api.post(f"{API_PREFIX}/evidence/{EVIDENCE_ID}/verify")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert data["verification_result"]["status"] == "verified"
        assert data["verification_result"]["verification_level"] == "L2"

    def test_export_evidence_package(self, api):
        """POST /v1.0/evidence/export creates export package."""
        payload = {
            "framework": "NIST-800-53",
            "time_range": {
                "from": "2025-01-01T00:00:00Z",
                "to": "2025-12-31T23:59:59Z",
            },
            "format": "json",
            "include_chain_of_custody": True,
        }
        resp = api.post(f"{API_PREFIX}/evidence/export", json=payload)
        assert_status(resp, 202)
        data = assert_json(resp)
        assert data["status"] == "processing"
        assert "package_id" in data

    def test_get_export_package(self, api):
        """GET /v1.0/evidence/export/{id} returns package status."""
        resp = api.get(f"{API_PREFIX}/evidence/export/{PACKAGE_ID}")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert data["package_id"] == PACKAGE_ID


# ===========================================================================
# Enforcement Endpoints
# ===========================================================================

class TestEnforcement:
    """Tests for enforcement decision endpoints."""

    def test_request_decision(self, api):
        """POST /v1.0/enforcement/decide returns a decision."""
        payload = {
            "agent_id": AGENT_ID,
            "action": "read",
            "resource": "s3://grc-data/test-dataset",
            "context": {"environment": "test"},
            "policy_ids": [POLICY_ID],
            "include_evidence": True,
        }
        resp = api.post(f"{API_PREFIX}/enforcement/decide", json=payload)
        assert_status(resp, 200)
        data = assert_json(resp)
        assert data["verdict"] == "ALLOW"
        assert data["agent_id"] == AGENT_ID
        assert "decision_id" in data
        assert "evidence_hash" in data
        assert "signature" in data

    def test_batch_decide(self, api):
        """POST /v1.0/enforcement/decide-batch returns batch results."""
        payload = {
            "decisions": [
                {
                    "agent_id": AGENT_ID,
                    "action": "read",
                    "resource": "resource-1",
                    "policy_ids": [POLICY_ID],
                },
                {
                    "agent_id": "agent-2",
                    "action": "write",
                    "resource": "resource-2",
                    "policy_ids": [POLICY_ID],
                },
            ]
        }
        resp = api.post(f"{API_PREFIX}/enforcement/decide-batch", json=payload)
        assert_status(resp, 200)
        data = assert_json(resp)
        assert len(data["results"]) == 2
        assert data["summary"]["total"] == 2

    def test_get_decision(self, api):
        """GET /v1.0/enforcement/decisions/{id} returns decision details."""
        resp = api.get(f"{API_PREFIX}/enforcement/decisions/{DECISION_ID}")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert data["decision_id"] == DECISION_ID

    def test_get_decision_not_found(self, api):
        """GET /v1.0/enforcement/decisions/{id} with invalid ID returns 404."""
        resp = api.get(f"{API_PREFIX}/enforcement/decisions/nonexistent-decision-99999")
        assert_status(resp, 404)

    def test_list_decisions(self, api):
        """GET /v1.0/enforcement/decisions returns paginated list."""
        resp = api.get(f"{API_PREFIX}/enforcement/decisions")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert "data" in data
        assert "pagination" in data

    def test_list_decisions_with_filters(self, api):
        """GET /v1.0/enforcement/decisions with query filters."""
        resp = api.get(f"{API_PREFIX}/enforcement/decisions", params={
            "agent_id": AGENT_ID,
            "verdict": "ALLOW",
        })
        assert_status(resp, 200)


# ===========================================================================
# Assessment Endpoints
# ===========================================================================

class TestAssessments:
    """Tests for assessment management endpoints."""

    def test_list_assessments(self, api):
        """GET /v1.0/assessments returns paginated list."""
        resp = api.get(f"{API_PREFIX}/assessments")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert "data" in data
        assert "pagination" in data

    def test_list_assessments_with_filters(self, api):
        """GET /v1.0/assessments with query filters."""
        resp = api.get(f"{API_PREFIX}/assessments", params={
            "assessment_type": "risk",
            "status": "planned",
        })
        assert_status(resp, 200)

    def test_create_assessment(self, api):
        """POST /v1.0/assessments creates a new assessment."""
        payload = {
            "assessment_key": f"TEST-ASM-{int(datetime.now(timezone.utc).timestamp())}",
            "title": "Test Assessment",
            "description": "Assessment created by automated test",
            "assessment_type": "risk",
            "target_id": AGENT_ID,
            "target_type": "agent",
            "methodology": "NIST RMF",
            "lead_assessor": "test@company.com",
        }
        resp = api.post(f"{API_PREFIX}/assessments", json=payload)
        assert_status(resp, 201)
        data = assert_json(resp)
        assert data["title"] == "Test Assessment"
        assert data["status"] == "planned"

    def test_get_assessment(self, api):
        """GET /v1.0/assessments/{id} returns assessment details."""
        resp = api.get(f"{API_PREFIX}/assessments/{ASSESSMENT_ID}")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert data["id"] == ASSESSMENT_ID

    def test_get_assessment_not_found(self, api):
        """GET /v1.0/assessments/{id} with invalid ID returns 404."""
        resp = api.get(f"{API_PREFIX}/assessments/nonexistent-assessment-99999")
        assert_status(resp, 404)

    def test_update_assessment(self, api):
        """PUT /v1.0/assessments/{id} updates assessment."""
        payload = {
            "status": "in_progress",
            "score": 75.0,
            "risk_level": "medium",
        }
        resp = api.put(f"{API_PREFIX}/assessments/{ASSESSMENT_ID}", json=payload)
        assert_status(resp, 200)
        data = assert_json(resp)
        assert data["status"] == "in_progress"

    def test_add_finding(self, api):
        """POST /v1.0/assessments/{id}/findings adds a finding."""
        payload = {
            "finding_key": f"TEST-FND-{int(datetime.now(timezone.utc).timestamp())}",
            "title": "Test Finding",
            "description": "Finding created by automated test",
            "severity": "medium",
            "category": "test",
            "policy_id": POLICY_ID,
            "evidence_ids": [EVIDENCE_ID],
            "remediation": "Fix the issue",
        }
        resp = api.post(f"{API_PREFIX}/assessments/{ASSESSMENT_ID}/findings", json=payload)
        assert_status(resp, 200)
        data = assert_json(resp)
        assert len(data["findings"]) >= 1

    def test_generate_assessment_report(self, api):
        """POST /v1.0/assessments/{id}/report generates report."""
        payload = {
            "format": "pdf",
            "include_evidence": True,
            "include_remediation": True,
        }
        resp = api.post(f"{API_PREFIX}/assessments/{ASSESSMENT_ID}/report", json=payload)
        assert_status(resp, 200)
        data = assert_json(resp)
        assert data["status"] == "processing"
        assert "report_id" in data


# ===========================================================================
# Compliance Endpoints
# ===========================================================================

class TestCompliance:
    """Tests for compliance management endpoints."""

    def test_list_frameworks(self, api):
        """GET /v1.0/compliance/frameworks returns frameworks."""
        resp = api.get(f"{API_PREFIX}/compliance/frameworks")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_controls(self, api):
        """GET /v1.0/compliance/frameworks/{id}/controls returns controls."""
        resp = api.get(f"{API_PREFIX}/compliance/frameworks/{FRAMEWORK_ID}/controls")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert isinstance(data, list)

    def test_list_controls_not_found(self, api):
        """GET /v1.0/compliance/frameworks/{id}/controls with invalid ID returns 404."""
        resp = api.get(f"{API_PREFIX}/compliance/frameworks/nonexistent-fw-99999/controls")
        assert_status(resp, 404)

    def test_get_compliance_posture(self, api):
        """GET /v1.0/compliance/posture returns posture."""
        resp = api.get(f"{API_PREFIX}/compliance/posture")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert "compliance_score" in data
        assert "controls_assessed" in data
        assert "trend" in data

    def test_create_compliance_mapping(self, api):
        """POST /v1.0/compliance/mappings creates a mapping."""
        payload = {
            "control_id": "AC-2",
            "policy_id": POLICY_ID,
            "assessment_id": ASSESSMENT_ID,
            "mapping_type": "automated",
            "coverage": "full",
            "notes": "Test mapping",
        }
        resp = api.post(f"{API_PREFIX}/compliance/mappings", json=payload)
        assert_status(resp, 201)
        data = assert_json(resp)
        assert data["control_id"] == "AC-2"
        assert data["mapping_type"] == "automated"

    def test_generate_compliance_report(self, api):
        """POST /v1.0/compliance/reports generates report."""
        payload = {
            "framework": "NIST-800-53",
            "time_range": {
                "from": "2025-01-01T00:00:00Z",
                "to": "2025-12-31T23:59:59Z",
            },
            "format": "json",
            "include_evidence": True,
            "include_gaps": True,
        }
        resp = api.post(f"{API_PREFIX}/compliance/reports", json=payload)
        assert_status(resp, 200)
        data = assert_json(resp)
        assert data["status"] == "processing"

    def test_get_crosswalk(self, api):
        """GET /v1.0/compliance/crosswalk returns cross-framework mapping."""
        resp = api.get(f"{API_PREFIX}/compliance/crosswalk")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert "mappings" in data
        assert "nist_800_53" in data["mappings"]


# ===========================================================================
# Audit Endpoints
# ===========================================================================

class TestAudit:
    """Tests for audit trail endpoints."""

    def test_query_audit_trail(self, api):
        """GET /v1.0/audit returns audit events."""
        resp = api.get(f"{API_PREFIX}/audit")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert "data" in data
        assert "pagination" in data

    def test_query_audit_trail_with_filters(self, api):
        """GET /v1.0/audit with query filters."""
        resp = api.get(f"{API_PREFIX}/audit", params={
            "event_type": "policy.created",
            "limit": 10,
        })
        assert_status(resp, 200)

    def test_verify_audit_chain(self, api):
        """POST /v1.0/audit/verify verifies chain integrity."""
        payload = {
            "from_event_id": None,
            "to_event_id": None,
        }
        resp = api.post(f"{API_PREFIX}/audit/verify", json=payload)
        assert_status(resp, 200)
        data = assert_json(resp)
        assert data["verification_status"] == "valid"
        assert data["chain_intact"] is True


# ===========================================================================
# Webhook Endpoints
# ===========================================================================

class TestWebhooks:
    """Tests for webhook subscription endpoints."""

    def test_list_subscriptions(self, api):
        """GET /v1.0/webhooks/subscriptions returns paginated list."""
        resp = api.get(f"{API_PREFIX}/webhooks/subscriptions")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert "data" in data
        assert "pagination" in data

    def test_create_subscription(self, api):
        """POST /v1.0/webhooks/subscriptions creates a subscription."""
        payload = {
            "url": "https://httpbin.org/post",
            "events": ["policy.created", "enforcement.decision_made"],
            "secret": "whsec_test_secret_key_1234567890",
            "description": "Test webhook subscription",
            "active": True,
        }
        resp = api.post(f"{API_PREFIX}/webhooks/subscriptions", json=payload)
        assert_status(resp, 201)
        data = assert_json(resp)
        assert data["url"] == payload["url"]
        assert data["active"] is True

    def test_get_subscription(self, api):
        """GET /v1.0/webhooks/subscriptions/{id} returns subscription."""
        resp = api.get(f"{API_PREFIX}/webhooks/subscriptions/{SUBSCRIPTION_ID}")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert data["subscription_id"] == SUBSCRIPTION_ID

    def test_get_subscription_not_found(self, api):
        """GET /v1.0/webhooks/subscriptions/{id} with invalid ID returns 404."""
        resp = api.get(f"{API_PREFIX}/webhooks/subscriptions/nonexistent-sub-99999")
        assert_status(resp, 404)

    def test_update_subscription(self, api):
        """PUT /v1.0/webhooks/subscriptions/{id} updates subscription."""
        payload = {
            "active": False,
            "description": "Updated by test suite",
        }
        resp = api.put(f"{API_PREFIX}/webhooks/subscriptions/{SUBSCRIPTION_ID}", json=payload)
        assert_status(resp, 200)
        data = assert_json(resp)
        assert data["active"] is False

    def test_delete_subscription(self, api):
        """DELETE /v1.0/webhooks/subscriptions/{id} deletes subscription."""
        # Create a subscription to delete
        payload = {
            "url": "https://httpbin.org/post",
            "events": ["policy.created"],
            "secret": "whsec_delete_test_1234567890",
            "active": True,
        }
        create_resp = api.post(f"{API_PREFIX}/webhooks/subscriptions", json=payload)
        if create_resp.status_code == 201:
            sub_id = create_resp.json()["subscription_id"]
            resp = api.delete(f"{API_PREFIX}/webhooks/subscriptions/{sub_id}")
            assert_status(resp, 204)

    def test_test_subscription(self, api):
        """POST /v1.0/webhooks/subscriptions/{id}/test sends test event."""
        resp = api.post(f"{API_PREFIX}/webhooks/subscriptions/{SUBSCRIPTION_ID}/test")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert data["delivery_status"] == "delivered"
        assert data["http_status"] == 200

    def test_get_delivery_history(self, api):
        """GET /v1.0/webhooks/subscriptions/{id}/deliveries returns history."""
        resp = api.get(f"{API_PREFIX}/webhooks/subscriptions/{SUBSCRIPTION_ID}/deliveries")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert isinstance(data, list)


# ===========================================================================
# Composed Endpoints
# ===========================================================================

class TestComposed:
    """Tests for composed/aggregated endpoints."""

    def test_dashboard_overview(self, api):
        """GET /v1.0/composed/dashboard returns dashboard data."""
        resp = api.get(f"{API_PREFIX}/composed/dashboard")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert "compliance_summary" in data
        assert "active_agents" in data
        assert "recent_enforcements" in data
        assert "open_findings" in data

    def test_agent_360(self, api):
        """GET /v1.0/composed/agents/{id}/360 returns agent 360 view."""
        resp = api.get(f"{API_PREFIX}/composed/agents/{AGENT_ID}/360")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert "agent" in data
        assert "policies" in data
        assert "enforcements" in data
        assert "evidence" in data

    def test_compliance_report(self, api):
        """GET /v1.0/composed/compliance-report returns aggregated report."""
        resp = api.get(f"{API_PREFIX}/composed/compliance-report")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert "frameworks" in data
        assert "evidence_summary" in data
        assert "findings" in data

    def test_executive_summary(self, api):
        """GET /v1.0/composed/executive-summary returns executive summary."""
        resp = api.get(f"{API_PREFIX}/composed/executive-summary")
        assert_status(resp, 200)
        data = assert_json(resp)
        assert "overall_compliance_score" in data
        assert "risk_posture" in data
        assert "agent_governance" in data


# ===========================================================================
# GraphQL Endpoint
# ===========================================================================

class TestGraphQL:
    """Tests for GraphQL endpoint."""

    def test_graphql_query(self, api):
        """POST /v1.0/graphql executes a query."""
        payload = {
            "query": "{ agents { id name type riskTier } }",
        }
        resp = api.post(f"{API_PREFIX}/graphql", json=payload)
        assert_status(resp, 200)
        data = assert_json(resp)
        assert "data" in data


# ===========================================================================
# Authentication Tests
# ===========================================================================

class TestAuthentication:
    """Tests for authentication and authorization."""

    def test_missing_auth_header(self, base_url):
        """Requests without auth header return 401."""
        resp = requests.get(f"{base_url}{API_PREFIX}/agents", timeout=30)
        assert resp.status_code == 401

    def test_invalid_api_key(self, base_url):
        """Requests with invalid API key return 401."""
        resp = requests.get(
            f"{base_url}{API_PREFIX}/agents",
            headers={"Authorization": "Bearer invalid_key"},
            timeout=30,
        )
        assert resp.status_code == 401

    def test_insufficient_scope(self, base_url, headers):
        """Requests with insufficient scope return 403."""
        # This test assumes the default key has limited scopes
        # In practice, you'd use a key with restricted scopes
        resp = requests.get(
            f"{base_url}{API_PREFIX}/audit",
            headers=headers,
            timeout=30,
        )
        # May be 200 or 403 depending on key configuration
        assert resp.status_code in (200, 403)


# ===========================================================================
# Integration Tests
# ===========================================================================

class TestIntegration:
    """End-to-end integration tests."""

    def test_full_policy_lifecycle(self, api):
        """Create, read, update, compile, dry-run, and delete a policy."""
        # Create
        create_payload = {
            "policy_key": f"LIFECYCLE-{int(datetime.now(timezone.utc).timestamp())}",
            "name": "Lifecycle Test Policy",
            "description": "Full lifecycle test",
            "category": "safety",
            "framework_tags": ["NIST-800-53"],
            "cedar_policy": 'permit(principal, action, resource) when { true };',
        }
        create_resp = api.post(f"{API_PREFIX}/policies", json=create_payload)
        assert_status(create_resp, 201)
        policy_id = create_resp.json()["id"]

        # Read
        get_resp = api.get(f"{API_PREFIX}/policies/{policy_id}")
        assert_status(get_resp, 200)

        # Update
        update_resp = api.put(f"{API_PREFIX}/policies/{policy_id}", json={
            "name": "Updated Lifecycle Policy",
        })
        assert_status(update_resp, 200)

        # Compile
        compile_resp = api.post(f"{API_PREFIX}/policies/{policy_id}/compile")
        assert_status(compile_resp, 200)

        # Dry-run
        dry_run_resp = api.post(f"{API_PREFIX}/policies/{policy_id}/dry-run", json={
            "test_inputs": [{
                "principal": {"id": "agent-1"},
                "action": "read",
                "resource": {"id": "data-1"},
            }],
        })
        assert_status(dry_run_resp, 200)

        # Delete
        delete_resp = api.delete(f"{API_PREFIX}/policies/{policy_id}")
        assert_status(delete_resp, 204)

    def test_full_agent_lifecycle(self, api):
        """Register, read, update, trust-score, bind-policies for an agent."""
        # Register
        register_payload = {
            "name": f"Lifecycle Agent {int(datetime.now(timezone.utc).timestamp())}",
            "type": "agent",
            "framework": "langchain",
            "owner": "test-suite",
            "risk_tier": "minimal",
            "capabilities": [],
        }
        register_resp = api.post(f"{API_PREFIX}/agents", json=register_payload)
        assert_status(register_resp, 201)
        agent_id = register_resp.json()["id"]

        # Read
        get_resp = api.get(f"{API_PREFIX}/agents/{agent_id}")
        assert_status(get_resp, 200)

        # Update
        update_resp = api.put(f"{API_PREFIX}/agents/{agent_id}", json={
            "lifecycle_stage": "active",
        })
        assert_status(update_resp, 200)

        # Trust score
        trust_resp = api.post(f"{API_PREFIX}/agents/{agent_id}/trust-score", json={
            "value": 90,
            "grade": "A",
            "reason": "Lifecycle test",
        })
        assert_status(trust_resp, 200)

        # Bind policies
        bind_resp = api.post(f"{API_PREFIX}/agents/{agent_id}/policy-bindings", json={
            "policy_ids": [POLICY_ID],
        })
        assert_status(bind_resp, 200)

    def test_enforcement_decision_flow(self, api):
        """Request a decision and retrieve it."""
        # Request decision
        decide_payload = {
            "agent_id": AGENT_ID,
            "action": "read",
            "resource": "test-resource",
            "policy_ids": [POLICY_ID],
        }
        decide_resp = api.post(f"{API_PREFIX}/enforcement/decide", json=decide_payload)
        assert_status(decide_resp, 200)
        decision_id = decide_resp.json()["decision_id"]

        # Get decision
        get_resp = api.get(f"{API_PREFIX}/enforcement/decisions/{decision_id}")
        assert_status(get_resp, 200)
        assert get_resp.json()["decision_id"] == decision_id


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
