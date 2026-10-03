"""Tests for licensing engine agents."""

from __future__ import annotations

import pytest

from ugc_marketplace.agents.licensing_engine import (AgentContext,
                                                     ComplianceTrackerAgent,
                                                     ContractAnalyzerAgent,
                                                     LicenseGeneratorAgent,
                                                     RoyaltyCalculatorAgent,
                                                     TermsNegotiatorAgent)


@pytest.mark.asyncio
async def test_license_generator_agent() -> None:
    """Test license generator agent."""
    agent = LicenseGeneratorAgent(AgentContext())
    result = await agent.execute(
        {
            "content_id": "content_1",
            "content_type": "text",
            "license_type": "non_exclusive",
            "licensor_id": "creator_1",
            "licensee_id": "user_1",
            "terms": {},
        }
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_terms_negotiator_agent() -> None:
    """Test terms negotiator agent."""
    agent = TermsNegotiatorAgent(AgentContext())
    result = await agent.execute(
        {
            "license_id": "license_1",
            "proposals": [],
        }
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_compliance_tracker_agent() -> None:
    """Test compliance tracker agent."""
    agent = ComplianceTrackerAgent(AgentContext())
    result = await agent.execute(
        {
            "license_id": "license_1",
            "license_terms": {},
            "usage_data": {},
        }
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_royalty_calculator_agent() -> None:
    """Test royalty calculator agent."""
    agent = RoyaltyCalculatorAgent(AgentContext())
    result = await agent.execute(
        {
            "license_id": "license_1",
            "usage_count": 100,
            "revenue": 1000.0,
            "tiers": [],
            "currency": "USD",
        }
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_contract_analyzer_agent() -> None:
    """Test contract analyzer agent."""
    agent = ContractAnalyzerAgent(AgentContext())
    result = await agent.execute(
        {
            "contract_text": "Sample contract text",
            "contract_type": "license",
        }
    )
    assert result.success is True
