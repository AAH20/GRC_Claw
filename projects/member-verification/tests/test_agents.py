"""Tests for member verification agents."""

from __future__ import annotations

import pytest

from member_verification.agents.document_checker import DocumentCheckerAgent
from member_verification.agents.explainer import VerificationExplainerAgent
from member_verification.agents.fraud_preventor import FraudPreventorAgent
from member_verification.agents.identity_verifier import IdentityVerifierAgent
from member_verification.agents.trust_scorer import TrustScorerAgent


class TestIdentityVerifierAgent:
    """Tests for IdentityVerifierAgent."""

    @pytest.fixture
    def agent(self) -> IdentityVerifierAgent:
        """Create an identity verifier agent.

        Returns:
            IdentityVerifierAgent instance.
        """
        return IdentityVerifierAgent()

    @pytest.mark.asyncio
    async def test_run_with_complete_data(self, agent: IdentityVerifierAgent) -> None:
        """Test identity verification with complete data.

        Args:
            agent: The agent instance.
        """
        result = await agent.run(
            {
                "identity": {
                    "full_name": "John Doe",
                    "date_of_birth": "1990-01-15",
                    "email": "john@example.com",
                    "phone": "+1234567890",
                    "address": "123 Main St",
                    "government_id": "ID123",
                },
                "documents": [
                    {
                        "document_type": "passport",
                        "document_number": "P123",
                        "issuing_country": "US",
                    }
                ],
            }
        )
        assert "status" in result
        assert "confidence" in result
        assert "checks_performed" in result
        assert result["confidence"] > 0.0

    @pytest.mark.asyncio
    async def test_run_with_minimal_data(self, agent: IdentityVerifierAgent) -> None:
        """Test identity verification with minimal data.

        Args:
            agent: The agent instance.
        """
        result = await agent.run(
            {
                "identity": {
                    "full_name": "Jane Doe",
                    "date_of_birth": "1985-05-20",
                    "email": "jane@example.com",
                },
                "documents": [],
            }
        )
        assert "status" in result
        assert "failure_reasons" in result

    @pytest.mark.asyncio
    async def test_health_check(self, agent: IdentityVerifierAgent) -> None:
        """Test agent health check.

        Args:
            agent: The agent instance.
        """
        assert await agent.health_check() is True

    def test_get_capabilities(self, agent: IdentityVerifierAgent) -> None:
        """Test getting agent capabilities.

        Args:
            agent: The agent instance.
        """
        capabilities = agent.get_capabilities()
        assert isinstance(capabilities, list)
        assert len(capabilities) > 0


class TestTrustScorerAgent:
    """Tests for TrustScorerAgent."""

    @pytest.fixture
    def agent(self) -> TrustScorerAgent:
        """Create a trust scorer agent.

        Returns:
            TrustScorerAgent instance.
        """
        return TrustScorerAgent()

    @pytest.mark.asyncio
    async def test_run(self, agent: TrustScorerAgent) -> None:
        """Test trust score calculation.

        Args:
            agent: The agent instance.
        """
        result = await agent.run(
            {
                "member_id": "test-member-001",
                "include_history": True,
            }
        )
        assert "score" in result
        assert "level" in result
        assert "factors" in result
        assert 0.0 <= result["score"] <= 1.0

    @pytest.mark.asyncio
    async def test_run_without_history(self, agent: TrustScorerAgent) -> None:
        """Test trust score calculation without history.

        Args:
            agent: The agent instance.
        """
        result = await agent.run(
            {
                "member_id": "test-member-002",
                "include_history": False,
            }
        )
        assert "score" in result
        assert result.get("history", []) == []

    @pytest.mark.asyncio
    async def test_health_check(self, agent: TrustScorerAgent) -> None:
        """Test agent health check.

        Args:
            agent: The agent instance.
        """
        assert await agent.health_check() is True


class TestFraudPreventorAgent:
    """Tests for FraudPreventorAgent."""

    @pytest.fixture
    def agent(self) -> FraudPreventorAgent:
        """Create a fraud preventor agent.

        Returns:
            FraudPreventorAgent instance.
        """
        return FraudPreventorAgent()

    @pytest.mark.asyncio
    async def test_run_basic_check(self, agent: FraudPreventorAgent) -> None:
        """Test basic fraud check.

        Args:
            agent: The agent instance.
        """
        result = await agent.run(
            {
                "member_id": "test-member-001",
                "identity": {
                    "full_name": "John Doe",
                    "date_of_birth": "1990-01-15",
                    "email": "john@example.com",
                },
                "check_depth": "basic",
            }
        )
        assert "risk_score" in result
        assert "risk_level" in result
        assert "recommendation" in result
        assert 0.0 <= result["risk_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_run_deep_check(self, agent: FraudPreventorAgent) -> None:
        """Test deep fraud check.

        Args:
            agent: The agent instance.
        """
        result = await agent.run(
            {
                "member_id": "test-member-002",
                "identity": {
                    "full_name": "Jane Doe",
                    "date_of_birth": "1985-05-20",
                    "email": "jane@example.com",
                    "phone": "+1234567890",
                    "address": "123 Main St",
                },
                "check_depth": "deep",
            }
        )
        assert "risk_score" in result
        assert "flags" in result

    @pytest.mark.asyncio
    async def test_health_check(self, agent: FraudPreventorAgent) -> None:
        """Test agent health check.

        Args:
            agent: The agent instance.
        """
        assert await agent.health_check() is True


class TestDocumentCheckerAgent:
    """Tests for DocumentCheckerAgent."""

    @pytest.fixture
    def agent(self) -> DocumentCheckerAgent:
        """Create a document checker agent.

        Returns:
            DocumentCheckerAgent instance.
        """
        return DocumentCheckerAgent()

    @pytest.mark.asyncio
    async def test_run_with_valid_document(self, agent: DocumentCheckerAgent) -> None:
        """Test document verification with valid document.

        Args:
            agent: The agent instance.
        """
        result = await agent.run(
            {
                "document": {
                    "document_type": "passport",
                    "document_number": "P12345678",
                    "issuing_country": "US",
                    "issue_date": "2020-01-01",
                    "expiry_date": "2030-01-01",
                    "document_hash": "abc123",
                },
                "identity": {"government_id": "P12345678"},
                "cross_reference": True,
            }
        )
        assert "is_authentic" in result
        assert "confidence" in result
        assert "tampering_detected" in result

    @pytest.mark.asyncio
    async def test_run_with_expired_document(self, agent: DocumentCheckerAgent) -> None:
        """Test document verification with expired document.

        Args:
            agent: The agent instance.
        """
        result = await agent.run(
            {
                "document": {
                    "document_type": "drivers_license",
                    "document_number": "DL98765432",
                    "issuing_country": "US",
                    "expiry_date": "2020-01-01",
                },
                "identity": {},
                "cross_reference": False,
            }
        )
        assert result.get("expiry_status") == "expired"

    @pytest.mark.asyncio
    async def test_health_check(self, agent: DocumentCheckerAgent) -> None:
        """Test agent health check.

        Args:
            agent: The agent instance.
        """
        assert await agent.health_check() is True


class TestVerificationExplainerAgent:
    """Tests for VerificationExplainerAgent."""

    @pytest.fixture
    def agent(self) -> VerificationExplainerAgent:
        """Create a verification explainer agent.

        Returns:
            VerificationExplainerAgent instance.
        """
        return VerificationExplainerAgent()

    @pytest.mark.asyncio
    async def test_run_verified(self, agent: VerificationExplainerAgent) -> None:
        """Test explanation for verified status.

        Args:
            agent: The agent instance.
        """
        result = await agent.run(
            {
                "request_id": "test-request-001",
                "verification_result": {
                    "status": "verified",
                    "confidence": 0.9,
                    "checks_performed": ["doc_check", "cross_ref"],
                    "failure_reasons": [],
                },
                "detail_level": "detailed",
            }
        )
        assert "summary" in result
        assert "factors" in result
        assert "recommendations" in result

    @pytest.mark.asyncio
    async def test_run_rejected(self, agent: VerificationExplainerAgent) -> None:
        """Test explanation for rejected status.

        Args:
            agent: The agent instance.
        """
        result = await agent.run(
            {
                "request_id": "test-request-002",
                "verification_result": {
                    "status": "rejected",
                    "confidence": 0.3,
                    "checks_performed": ["doc_check"],
                    "failure_reasons": ["Expired document"],
                },
                "detail_level": "summary",
            }
        )
        assert "summary" in result
        assert "appeal_process" in result

    @pytest.mark.asyncio
    async def test_health_check(self, agent: VerificationExplainerAgent) -> None:
        """Test agent health check.

        Args:
            agent: The agent instance.
        """
        assert await agent.health_check() is True
