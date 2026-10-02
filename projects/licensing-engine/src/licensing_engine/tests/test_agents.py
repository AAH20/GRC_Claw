"""Tests for agent implementations."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from licensing_engine.agents import (
    AgentContext,
    ComplianceTrackerAgent,
    ContractAnalyzerAgent,
    LicenseGeneratorAgent,
    RoyaltyCalculatorAgent,
    TermsNegotiatorAgent,
)
from licensing_engine.config.settings import Settings


@pytest.fixture
def settings() -> Settings:
    """Create test settings."""
    return Settings(
        openai_api_key="test-key",
        llm_model="gpt-4o",
        llm_temperature=0.1,
        llm_max_tokens=1024,
        agent_timeout_seconds=30,
    )


@pytest.fixture
def context(settings: Settings) -> AgentContext:
    """Create agent context."""
    return AgentContext(settings=settings)


class TestLicenseGeneratorAgent:
    """Tests for LicenseGeneratorAgent."""

    @pytest.mark.asyncio
    async def test_execute_success(self, context: AgentContext) -> None:
        """Test successful license generation."""
        agent = LicenseGeneratorAgent(context)
        agent._llm = MagicMock()
        agent._llm.ainvoke = AsyncMock(
            return_value=MagicMock(content="Generated license terms")
        )

        result = await agent.execute(
            {
                "content_id": "content-123",
                "content_type": "text",
                "license_type": "non_exclusive",
                "licensor_id": "licensor-1",
                "licensee_id": "licensee-1",
                "terms": {"usage_rights": ["read", "display"]},
            }
        )

        assert result.success is True
        assert "generated_terms" in result.data
        assert result.data["content_id"] == "content-123"

    @pytest.mark.asyncio
    async def test_execute_failure(self, context: AgentContext) -> None:
        """Test license generation failure."""
        agent = LicenseGeneratorAgent(context)
        agent._llm = MagicMock()
        agent._llm.ainvoke = AsyncMock(side_effect=Exception("LLM error"))

        result = await agent.execute(
            {
                "content_id": "content-123",
                "content_type": "text",
                "license_type": "non_exclusive",
                "licensor_id": "licensor-1",
                "licensee_id": "licensee-1",
                "terms": {},
            }
        )

        assert result.success is False
        assert result.error is not None


class TestTermsNegotiatorAgent:
    """Tests for TermsNegotiatorAgent."""

    @pytest.mark.asyncio
    async def test_execute_success(self, context: AgentContext) -> None:
        """Test successful negotiation."""
        agent = TermsNegotiatorAgent(context)
        agent._llm = MagicMock()
        agent._llm.ainvoke = AsyncMock(
            return_value=MagicMock(content="Negotiation analysis")
        )

        result = await agent.execute(
            {
                "license_id": "license-123",
                "proposals": [{"proposed_by": "party-a", "terms": {}}],
            }
        )

        assert result.success is True
        assert "negotiation_analysis" in result.data

    @pytest.mark.asyncio
    async def test_execute_failure(self, context: AgentContext) -> None:
        """Test negotiation failure."""
        agent = TermsNegotiatorAgent(context)
        agent._llm = MagicMock()
        agent._llm.ainvoke = AsyncMock(side_effect=Exception("LLM error"))

        result = await agent.execute(
            {
                "license_id": "license-123",
                "proposals": [],
            }
        )

        assert result.success is False


class TestComplianceTrackerAgent:
    """Tests for ComplianceTrackerAgent."""

    @pytest.mark.asyncio
    async def test_execute_success(self, context: AgentContext) -> None:
        """Test successful compliance check."""
        agent = ComplianceTrackerAgent(context)
        agent._llm = MagicMock()
        agent._llm.ainvoke = AsyncMock(
            return_value=MagicMock(content="Compliance analysis")
        )

        result = await agent.execute(
            {
                "license_id": "license-123",
                "license_terms": {"usage_rights": ["read"]},
                "usage_data": {"usage_count": 10},
            }
        )

        assert result.success is True
        assert "compliance_status" in result.data

    @pytest.mark.asyncio
    async def test_execute_failure(self, context: AgentContext) -> None:
        """Test compliance check failure."""
        agent = ComplianceTrackerAgent(context)
        agent._llm = MagicMock()
        agent._llm.ainvoke = AsyncMock(side_effect=Exception("LLM error"))

        result = await agent.execute(
            {
                "license_id": "license-123",
                "license_terms": {},
                "usage_data": {},
            }
        )

        assert result.success is False


class TestRoyaltyCalculatorAgent:
    """Tests for RoyaltyCalculatorAgent."""

    @pytest.mark.asyncio
    async def test_execute_success(self, context: AgentContext) -> None:
        """Test successful royalty calculation."""
        agent = RoyaltyCalculatorAgent(context)
        agent._llm = MagicMock()
        agent._llm.ainvoke = AsyncMock(
            return_value=MagicMock(content="Royalty calculation")
        )

        result = await agent.execute(
            {
                "license_id": "license-123",
                "usage_count": 1000,
                "revenue": 50000.0,
                "tiers": [{"min_usage": 0, "max_usage": 1000, "rate": 0.05}],
                "currency": "USD",
            }
        )

        assert result.success is True
        assert "total_royalty" in result.data

    @pytest.mark.asyncio
    async def test_execute_failure(self, context: AgentContext) -> None:
        """Test royalty calculation failure."""
        agent = RoyaltyCalculatorAgent(context)
        agent._llm = MagicMock()
        agent._llm.ainvoke = AsyncMock(side_effect=Exception("LLM error"))

        result = await agent.execute(
            {
                "license_id": "license-123",
                "usage_count": 0,
                "revenue": 0.0,
                "tiers": [],
                "currency": "USD",
            }
        )

        assert result.success is False


class TestContractAnalyzerAgent:
    """Tests for ContractAnalyzerAgent."""

    @pytest.mark.asyncio
    async def test_execute_success(self, context: AgentContext) -> None:
        """Test successful contract analysis."""
        agent = ContractAnalyzerAgent(context)
        agent._llm = MagicMock()
        agent._llm.ainvoke = AsyncMock(
            return_value=MagicMock(content="Contract analysis")
        )

        result = await agent.execute(
            {
                "contract_text": "This is a sample contract...",
                "contract_type": "license",
                "focus_areas": ["liability", "termination"],
            }
        )

        assert result.success is True
        assert "summary" in result.data

    @pytest.mark.asyncio
    async def test_execute_failure(self, context: AgentContext) -> None:
        """Test contract analysis failure."""
        agent = ContractAnalyzerAgent(context)
        agent._llm = MagicMock()
        agent._llm.ainvoke = AsyncMock(side_effect=Exception("LLM error"))

        result = await agent.execute(
            {
                "contract_text": "",
                "contract_type": "license",
                "focus_areas": [],
            }
        )

        assert result.success is False
