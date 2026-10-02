"""Tests for member verification service."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from member_verification.main import create_app


@pytest.fixture
def client() -> TestClient:
    """Create a test client.

    Returns:
        FastAPI test client.
    """
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_verification_request() -> dict:
    """Create a sample verification request.

    Returns:
        Dictionary with sample request data.
    """
    return {
        "member_id": "test-member-001",
        "identity": {
            "full_name": "John Doe",
            "date_of_birth": "1990-01-15",
            "email": "john.doe@example.com",
            "phone": "+1234567890",
            "address": "123 Main St, City, Country",
            "government_id": "ID123456789",
        },
        "documents": [
            {
                "document_type": "passport",
                "document_number": "P12345678",
                "issuing_country": "US",
                "issue_date": "2020-01-01",
                "expiry_date": "2030-01-01",
            }
        ],
        "metadata": {"source": "web"},
        "priority": "normal",
    }


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check(self, client: TestClient) -> None:
        """Test health check endpoint.

        Args:
            client: Test client.
        """
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data

    def test_readiness_check(self, client: TestClient) -> None:
        """Test readiness probe endpoint.

        Args:
            client: Test client.
        """
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"


class TestVerificationEndpoints:
    """Tests for verification endpoints."""

    def test_submit_verification(self, client: TestClient, sample_verification_request: dict) -> None:
        """Test submitting a verification request.

        Args:
            client: Test client.
            sample_verification_request: Sample request data.
        """
        response = client.post("/verify", json=sample_verification_request)
        assert response.status_code == 201
        data = response.json()
        assert data["member_id"] == "test-member-001"
        assert "status" in data
        assert "confidence" in data
        assert "trust_score" in data
        assert "fraud_risk" in data
        assert "request_id" in data

    def test_get_verification_result(
        self, client: TestClient, sample_verification_request: dict
    ) -> None:
        """Test getting a verification result.

        Args:
            client: Test client.
            sample_verification_request: Sample request data.
        """
        # First submit a request
        response = client.post("/verify", json=sample_verification_request)
        assert response.status_code == 201
        request_id = response.json()["request_id"]

        # Then retrieve the result
        response = client.get(f"/verify/{request_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["request_id"] == request_id

    def test_get_nonexistent_verification(self, client: TestClient) -> None:
        """Test getting a non-existent verification result.

        Args:
            client: Test client.
        """
        response = client.get("/verify/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    def test_batch_verification(
        self, client: TestClient, sample_verification_request: dict
    ) -> None:
        """Test batch verification.

        Args:
            client: Test client.
            sample_verification_request: Sample request data.
        """
        requests = [sample_verification_request, sample_verification_request]
        response = client.post("/verify/batch", json=requests)
        assert response.status_code == 201
        data = response.json()
        assert len(data) == 2

    def test_explain_verification(
        self, client: TestClient, sample_verification_request: dict
    ) -> None:
        """Test verification explanation.

        Args:
            client: Test client.
            sample_verification_request: Sample request data.
        """
        # First submit a request
        response = client.post("/verify", json=sample_verification_request)
        assert response.status_code == 201
        request_id = response.json()["request_id"]

        # Then get explanation
        response = client.post(
            "/verify/explain",
            json={"request_id": request_id, "detail_level": "detailed"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["request_id"] == request_id
        assert "summary" in data
        assert "factors" in data
        assert "recommendations" in data


class TestAgentEndpoints:
    """Tests for agent management endpoints."""

    def test_list_agents(self, client: TestClient) -> None:
        """Test listing all agents.

        Args:
            client: Test client.
        """
        response = client.get("/agents")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        agent_names = [a["name"] for a in data]
        assert "identity_verifier" in agent_names
        assert "trust_scorer" in agent_names
        assert "fraud_preventor" in agent_names
        assert "document_checker" in agent_names
        assert "verification_explainer" in agent_names

    def test_get_agent_status(self, client: TestClient) -> None:
        """Test getting agent status.

        Args:
            client: Test client.
        """
        response = client.get("/agents/identity_verifier/status")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "identity_verifier"
        assert data["status"] == "available"

    def test_get_nonexistent_agent(self, client: TestClient) -> None:
        """Test getting a non-existent agent.

        Args:
            client: Test client.
        """
        response = client.get("/agents/nonexistent/status")
        assert response.status_code == 404


class TestTrustScoreEndpoints:
    """Tests for trust score endpoints."""

    def test_calculate_trust_score(self, client: TestClient) -> None:
        """Test calculating trust score.

        Args:
            client: Test client.
        """
        response = client.post(
            "/trust-score",
            json={"member_id": "test-member-001", "include_history": True},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["member_id"] == "test-member-001"
        assert "score" in data
        assert "level" in data
        assert "factors" in data

    def test_get_trust_score(self, client: TestClient) -> None:
        """Test getting trust score.

        Args:
            client: Test client.
        """
        # First calculate
        client.post(
            "/trust-score",
            json={"member_id": "test-member-002", "include_history": False},
        )
        # Then get
        response = client.get("/trust-score/test-member-002")
        assert response.status_code == 200
        data = response.json()
        assert data["member_id"] == "test-member-002"

    def test_get_nonexistent_trust_score(self, client: TestClient) -> None:
        """Test getting a non-existent trust score.

        Args:
            client: Test client.
        """
        response = client.get("/trust-score/nonexistent-member")
        assert response.status_code == 404


class TestFraudEndpoints:
    """Tests for fraud check endpoints."""

    def test_run_fraud_check(self, client: TestClient) -> None:
        """Test running a fraud check.

        Args:
            client: Test client.
        """
        response = client.post(
            "/fraud/check",
            json={
                "member_id": "test-member-001",
                "identity": {
                    "full_name": "John Doe",
                    "date_of_birth": "1990-01-15",
                    "email": "john@example.com",
                },
                "check_depth": "standard",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["member_id"] == "test-member-001"
        assert "risk_score" in data
        assert "risk_level" in data
        assert "recommendation" in data

    def test_get_fraud_report(self, client: TestClient) -> None:
        """Test getting a fraud report.

        Args:
            client: Test client.
        """
        # First run check
        client.post(
            "/fraud/check",
            json={
                "member_id": "test-member-003",
                "identity": {
                    "full_name": "Jane Doe",
                    "date_of_birth": "1985-05-20",
                    "email": "jane@example.com",
                },
                "check_depth": "basic",
            },
        )
        # Then get report
        response = client.get("/fraud/report/test-member-003")
        assert response.status_code == 200
        data = response.json()
        assert data["member_id"] == "test-member-003"


class TestDocumentEndpoints:
    """Tests for document verification endpoints."""

    def test_verify_document(self, client: TestClient) -> None:
        """Test document verification.

        Args:
            client: Test client.
        """
        response = client.post(
            "/documents/verify",
            json={
                "member_id": "test-member-001",
                "document": {
                    "document_type": "passport",
                    "document_number": "P12345678",
                    "issuing_country": "US",
                    "issue_date": "2020-01-01",
                    "expiry_date": "2030-01-01",
                },
                "cross_reference": True,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "is_authentic" in data
        assert "confidence" in data
        assert "tampering_detected" in data
