"""Tests for GRC_Claw API."""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
async def client():
    """Create test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers():
    """Get authentication headers for testing."""
    return {"Authorization": "Bearer grc_live_test_key_for_development_only"}


class TestHealthEndpoints:
    """Test health and monitoring endpoints."""

    async def test_health_check(self, client):
        """Test health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "components" in data

    async def test_readiness_check(self, client):
        """Test readiness check endpoint."""
        response = await client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
        assert "checks" in data

    async def test_metrics(self, client):
        """Test Prometheus metrics endpoint."""
        response = await client.get("/metrics")
        assert response.status_code == 200
        assert "grc_api_requests_total" in response.text


class TestPolicyEndpoints:
    """Test policy management endpoints."""

    async def test_create_policy(self, client, auth_headers):
        """Test creating a policy."""
        response = await client.post(
            "/v1.0/policies",
            headers=auth_headers,
            json={
                "policy_key": "TEST-POLICY-001",
                "name": "Test Policy",
                "description": "A test policy",
                "category": "safety",
                "framework_tags": ["SOC2"],
                "cedar_policy": 'permit(principal, action, resource);',
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["policy_key"] == "TEST-POLICY-001"
        assert data["status"] == "draft"
        assert data["version"] == "1.0.0"

    async def test_list_policies(self, client, auth_headers):
        """Test listing policies."""
        response = await client.get("/v1.0/policies", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data

    async def test_get_policy(self, client, auth_headers):
        """Test getting a policy by ID."""
        # First create a policy
        create_response = await client.post(
            "/v1.0/policies",
            headers=auth_headers,
            json={
                "policy_key": "TEST-POLICY-002",
                "name": "Test Policy 2",
                "category": "privacy",
                "framework_tags": ["GDPR"],
            },
        )
        policy_id = create_response.json()["id"]

        # Then get it
        response = await client.get(f"/v1.0/policies/{policy_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == policy_id

    async def test_update_policy(self, client, auth_headers):
        """Test updating a policy."""
        # Create first
        create_response = await client.post(
            "/v1.0/policies",
            headers=auth_headers,
            json={
                "policy_key": "TEST-POLICY-003",
                "name": "Test Policy 3",
                "category": "ethics",
                "framework_tags": [],
            },
        )
        policy_id = create_response.json()["id"]

        # Update
        response = await client.put(
            f"/v1.0/policies/{policy_id}",
            headers=auth_headers,
            json={"name": "Updated Policy Name"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Policy Name"

    async def test_delete_policy(self, client, auth_headers):
        """Test deleting a policy."""
        # Create first
        create_response = await client.post(
            "/v1.0/policies",
            headers=auth_headers,
            json={
                "policy_key": "TEST-POLICY-004",
                "name": "Test Policy 4",
                "category": "fairness",
                "framework_tags": [],
            },
        )
        policy_id = create_response.json()["id"]

        # Delete
        response = await client.delete(
            f"/v1.0/policies/{policy_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

    async def test_compile_policy(self, client, auth_headers):
        """Test compiling a policy."""
        # Create first
        create_response = await client.post(
            "/v1.0/policies",
            headers=auth_headers,
            json={
                "policy_key": "TEST-POLICY-005",
                "name": "Test Policy 5",
                "category": "safety",
                "framework_tags": [],
                "cedar_policy": 'permit(principal, action, resource);',
            },
        )
        policy_id = create_response.json()["id"]

        # Compile
        response = await client.post(
            f"/v1.0/policies/{policy_id}/compile",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["compilation_status"] == "success"
        assert "rego_policy" in data

    async def test_dry_run_policy(self, client, auth_headers):
        """Test dry-running a policy."""
        # Create first
        create_response = await client.post(
            "/v1.0/policies",
            headers=auth_headers,
            json={
                "policy_key": "TEST-POLICY-006",
                "name": "Test Policy 6",
                "category": "privacy",
                "framework_tags": [],
            },
        )
        policy_id = create_response.json()["id"]

        # Dry run
        response = await client.post(
            f"/v1.0/policies/{policy_id}/dry-run",
            headers=auth_headers,
            json={
                "test_inputs": [
                    {
                        "principal": {"id": "agent-1", "clearance": 3},
                        "action": "read",
                        "resource": {"id": "dataset-1", "classification": 2},
                        "context": {"environment": "production"},
                    }
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "dry_run_results" in data
        assert "summary" in data


class TestEvidenceEndpoints:
    """Test evidence management endpoints."""

    async def test_submit_evidence(self, client, auth_headers):
        """Test submitting evidence."""
        response = await client.post(
            "/v1.0/evidence",
            headers=auth_headers,
            json={
                "policy_id": "pol-001",
                "source": {
                    "type": "scan",
                    "system": "aws-config",
                    "collection_method": "api-query",
                },
                "evidence_type": "config",
                "content": {
                    "format": "json",
                    "data": '{"encryption": "AES-256"}',
                },
                "context": {
                    "environment": "prod",
                    "region": "us-east-1",
                },
                "control_mapping": {
                    "control_id": "AC-2",
                    "framework": "NIST-800-53",
                    "control_title": "Account Management",
                },
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["evidence_type"] == "config"
        assert data["verification_level"] == "L0"

    async def test_search_evidence(self, client, auth_headers):
        """Test searching evidence."""
        response = await client.get("/v1.0/evidence", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data

    async def test_verify_evidence(self, client, auth_headers):
        """Test verifying evidence."""
        # Submit first
        submit_response = await client.post(
            "/v1.0/evidence",
            headers=auth_headers,
            json={
                "source": {"type": "scan", "system": "test", "collection_method": "manual"},
                "evidence_type": "artifact",
                "content": {"format": "json", "data": "{}"},
                "context": {"environment": "test"},
            },
        )
        evidence_id = submit_response.json()["evidence_id"]

        # Verify
        response = await client.post(
            f"/v1.0/evidence/{evidence_id}/verify",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["verification_result"]["status"] == "verified"


class TestEnforcementEndpoints:
    """Test enforcement decision endpoints."""

    async def test_request_decision(self, client, auth_headers):
        """Test requesting an enforcement decision."""
        response = await client.post(
            "/v1.0/enforcement/decide",
            headers=auth_headers,
            json={
                "agent_id": "agent-42",
                "action": "read",
                "resource": "s3://data/public/dataset.csv",
                "context": {"environment": "production"},
                "policy_ids": ["pol-001"],
                "include_evidence": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["verdict"] == "ALLOW"
        assert data["agent_id"] == "agent-42"
        assert "decision_id" in data

    async def test_batch_decide(self, client, auth_headers):
        """Test batch enforcement decisions."""
        response = await client.post(
            "/v1.0/enforcement/decide-batch",
            headers=auth_headers,
            json={
                "decisions": [
                    {
                        "agent_id": "agent-42",
                        "action": "read",
                        "resource": "s3://data/public/file1.csv",
                        "context": {"environment": "production"},
                    },
                    {
                        "agent_id": "agent-43",
                        "action": "write",
                        "resource": "s3://data/restricted/pii.db",
                        "context": {"environment": "production"},
                    },
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "summary" in data
        assert data["summary"]["total"] == 2

    async def test_list_decisions(self, client, auth_headers):
        """Test listing enforcement decisions."""
        response = await client.get("/v1.0/enforcement/decisions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data


class TestAgentEndpoints:
    """Test agent registry endpoints."""

    async def test_register_agent(self, client, auth_headers):
        """Test registering an agent."""
        response = await client.post(
            "/v1.0/agents",
            headers=auth_headers,
            json={
                "name": "Test Agent",
                "type": "agent",
                "framework": "custom",
                "owner": "user-001",
                "risk_tier": "limited",
                "capabilities": [
                    {
                        "name": "read_data",
                        "description": "Read data from approved sources",
                        "permissions": ["read"],
                        "resource_scope": "s3://data/public/*",
                    }
                ],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Agent"
        assert data["lifecycle_stage"] == "proposed"

    async def test_list_agents(self, client, auth_headers):
        """Test listing agents."""
        response = await client.get("/v1.0/agents", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data

    async def test_update_trust_score(self, client, auth_headers):
        """Test updating agent trust score."""
        # Register first
        register_response = await client.post(
            "/v1.0/agents",
            headers=auth_headers,
            json={
                "name": "Trust Test Agent",
                "type": "agent",
                "framework": "custom",
                "owner": "user-001",
                "risk_tier": "limited",
                "capabilities": [],
            },
        )
        agent_id = register_response.json()["id"]

        # Update trust score
        response = await client.post(
            f"/v1.0/agents/{agent_id}/trust-score",
            headers=auth_headers,
            json={
                "value": 92,
                "grade": "A",
                "reason": "Consistent compliant behavior",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["trust_score"]["value"] == 92
        assert data["trust_score"]["grade"] == "A"


class TestWebhookEndpoints:
    """Test webhook subscription endpoints."""

    async def test_create_subscription(self, client, auth_headers):
        """Test creating a webhook subscription."""
        response = await client.post(
            "/v1.0/webhooks/subscriptions",
            headers=auth_headers,
            json={
                "url": "https://example.com/webhooks/grc-claw",
                "events": ["policy.created", "enforcement.decision_made"],
                "secret": "whsec_test_secret_key_12345",
                "description": "Test webhook",
                "active": True,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["url"] == "https://example.com/webhooks/grc-claw"
        assert len(data["events"]) == 2

    async def test_list_subscriptions(self, client, auth_headers):
        """Test listing webhook subscriptions."""
        response = await client.get("/v1.0/webhooks/subscriptions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data

    async def test_test_subscription(self, client, auth_headers):
        """Test sending a test webhook."""
        # Create first
        create_response = await client.post(
            "/v1.0/webhooks/subscriptions",
            headers=auth_headers,
            json={
                "url": "https://example.com/webhooks/test",
                "events": ["policy.created"],
                "secret": "whsec_test_secret_key_67890",
                "active": True,
            },
        )
        sub_id = create_response.json()["subscription_id"]

        # Test
        response = await client.post(
            f"/v1.0/webhooks/subscriptions/{sub_id}/test",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["delivery_status"] == "delivered"


class TestAuthentication:
    """Test authentication and authorization."""

    async def test_unauthenticated_request(self, client):
        """Test that unauthenticated requests are rejected."""
        response = await client.get("/v1.0/policies")
        assert response.status_code == 403

    async def test_invalid_token(self, client):
        """Test that invalid tokens are rejected."""
        response = await client.get(
            "/v1.0/policies",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 403


class TestGraphQL:
    """Test GraphQL endpoint."""

    async def test_graphql_query(self, client, auth_headers):
        """Test GraphQL query."""
        response = await client.post(
            "/v1.0/graphql",
            headers=auth_headers,
            json={
                "query": """
                    query {
                        me {
                            id
                            name
                            email
                            roles
                        }
                    }
                """
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "me" in data["data"]

    async def test_graphql_policies(self, client, auth_headers):
        """Test GraphQL policies query."""
        response = await client.post(
            "/v1.0/graphql",
            headers=auth_headers,
            json={
                "query": """
                    query {
                        policies(first: 10) {
                            edges {
                                node {
                                    id
                                    name
                                    status
                                }
                            }
                            pageInfo {
                                hasNextPage
                                totalCount
                            }
                        }
                    }
                """
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "policies" in data["data"]
