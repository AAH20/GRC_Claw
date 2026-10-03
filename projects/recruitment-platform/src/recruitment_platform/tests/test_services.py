"""Tests for service layer."""

from __future__ import annotations

import pytest

from recruitment_platform.services.agent_registry import AgentRegistry, register_default_agents
from recruitment_platform.services.parsing_service import ParsingService


class TestAgentRegistry:
    """Test agent registry."""

    def test_register_agent(self) -> None:
        """Test agent registration."""
        registry = AgentRegistry()
        from recruitment_platform.agents.resume_parser.contact_extractor_agent import (
            ContactExtractorAgent,
        )

        registry.register("test_contact", ContactExtractorAgent)
        assert "test_contact" in registry.list_agents()

    def test_get_agent(self) -> None:
        """Test getting an agent instance."""
        registry = AgentRegistry()
        from recruitment_platform.agents.resume_parser.contact_extractor_agent import (
            ContactExtractorAgent,
        )

        registry.register("test_contact", ContactExtractorAgent)
        agent = registry.get("test_contact")
        assert isinstance(agent, ContactExtractorAgent)

    def test_register_default_agents(self) -> None:
        """Test registering all default agents."""
        registry = AgentRegistry()
        register_default_agents(registry)
        agents = registry.list_agents()
        assert len(agents) > 0

    def test_get_by_category(self) -> None:
        """Test getting agents by category."""
        registry = AgentRegistry()
        register_default_agents(registry)
        resume_agents = registry.get_by_category("resume")
        assert len(resume_agents) > 0


class TestParsingService:
    """Test parsing service."""

    @pytest.mark.asyncio
    async def test_parse(self) -> None:
        """Test resume parsing."""
        service = ParsingService()
        result = await service.parse("John Doe\nPython, AWS")
        assert "contact" in result
        assert "skills" in result
