"""Tests for agent implementations."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from talent_pool_manager.agents import (
    AgentRegistry,
    CandidateDiscoveryAgent,
    EngagementOptimizerAgent,
    OutreachAgent,
    PoolSegmentationAgent,
    TalentScorerAgent,
)
from talent_pool_manager.models import (
    DiscoveryRequest,
    EngagementOptimizationRequest,
    OutreachRequest,
    ScoringRequest,
    SegmentationRequest,
)


class TestBaseAgent:
    """Tests for the base agent class."""

    def test_create_default_model(self) -> None:
        """Test default model creation."""
        agent = CandidateDiscoveryAgent()
        assert agent.model is not None
        assert agent.settings is not None


class TestCandidateDiscoveryAgent:
    """Tests for the candidate discovery agent."""

    @pytest.mark.asyncio
    async def test_run_discovery(self) -> None:
        """Test running candidate discovery."""
        agent = CandidateDiscoveryAgent()
        request = DiscoveryRequest(
            pool_id=uuid4(),
            query="Python Engineer",
            sources=["linkedin"],
            max_results=10,
        )

        # Mock the LLM invocation
        with patch.object(agent, "_invoke_llm", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = "[]"
            result = await agent.run(request)

        assert result.candidates_found == 0
        assert result.query_used == "Python Engineer"
        assert result.duration_seconds >= 0

    @pytest.mark.asyncio
    async def test_build_system_prompt(self) -> None:
        """Test system prompt building."""
        agent = CandidateDiscoveryAgent()
        prompt = agent._build_system_prompt()
        assert "talent discovery" in prompt.lower()
        assert "candidate" in prompt.lower()


class TestPoolSegmentationAgent:
    """Tests for the pool segmentation agent."""

    @pytest.mark.asyncio
    async def test_run_segmentation(self) -> None:
        """Test running pool segmentation."""
        agent = PoolSegmentationAgent()
        request = SegmentationRequest(
            pool_id=uuid4(),
            segment_count=3,
        )

        with patch.object(agent, "_invoke_llm", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = "[]"
            result = await agent.run(request)

        assert result.quality_score >= 0
        assert result.duration_seconds >= 0


class TestEngagementOptimizerAgent:
    """Tests for the engagement optimizer agent."""

    @pytest.mark.asyncio
    async def test_run_optimization(self) -> None:
        """Test running engagement optimization."""
        agent = EngagementOptimizerAgent()
        request = EngagementOptimizationRequest(
            pool_id=uuid4(),
            optimization_goal="response_rate",
        )

        with patch.object(agent, "_invoke_llm", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = "{}"
            result = await agent.run(request)

        assert result.predicted_improvement >= 0
        assert result.duration_seconds >= 0


class TestTalentScorerAgent:
    """Tests for the talent scorer agent."""

    @pytest.mark.asyncio
    async def test_run_scoring(self) -> None:
        """Test running talent scoring."""
        agent = TalentScorerAgent()
        request = ScoringRequest(
            candidate_ids=[uuid4(), uuid4()],
        )

        with patch.object(agent, "_invoke_llm", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = "{}"
            result = await agent.run(request)

        assert isinstance(result.scores, dict)
        assert isinstance(result.factors, dict)
        assert result.duration_seconds >= 0


class TestOutreachAgent:
    """Tests for the outreach agent."""

    @pytest.mark.asyncio
    async def test_run_outreach(self) -> None:
        """Test running outreach."""
        agent = OutreachAgent()
        request = OutreachRequest(
            campaign_id=uuid4(),
            candidate_ids=[uuid4()],
            template_id=uuid4(),
        )

        with patch.object(agent, "_invoke_llm", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = "{}"
            result = await agent.run(request)

        assert result.messages_generated >= 0
        assert result.duration_seconds >= 0


class TestAgentRegistry:
    """Tests for the agent registry."""

    def test_registry_initialization(self) -> None:
        """Test agent registry initialization."""
        registry = AgentRegistry()
        assert registry.discovery_agent is not None
        assert registry.segmentation_agent is not None
        assert registry.engagement_agent is not None
        assert registry.scoring_agent is not None
        assert registry.outreach_agent is not None

    def test_get_agent(self) -> None:
        """Test getting an agent by name."""
        registry = AgentRegistry()
        agent = registry.get_agent("discovery")
        assert agent is not None
        assert isinstance(agent, CandidateDiscoveryAgent)

    def test_get_nonexistent_agent(self) -> None:
        """Test getting a non-existent agent."""
        registry = AgentRegistry()
        agent = registry.get_agent("nonexistent")
        assert agent is None
