"""Tests for agent implementations."""

from __future__ import annotations

import pytest

from resume_parser.agents import (
    BaseAgent,
    ContactExtractorAgent,
    EducationExtractorAgent,
    ExperienceExtractorAgent,
    ResumeParserAgent,
    SkillsExtractorAgent,
)
from resume_parser.config import Settings
from resume_parser.integrations import BaseLLMClient
from resume_parser.models import AgentResult
from resume_parser.tests.conftest import MockLLMClient


class TestBaseAgent:
    """Test cases for BaseAgent."""

    @pytest.fixture
    def settings(self) -> Settings:
        """Create test settings.

        Returns:
            Settings: Test settings.
        """
        return Settings(
            openai_api_key="test-key",
            openai_model="gpt-4o-mini",
        )

    @pytest.fixture
    def mock_llm(self) -> MockLLMClient:
        """Create mock LLM client.

        Returns:
            MockLLMClient: Mock LLM client.
        """
        return MockLLMClient()

    def test_agent_name_property(
        self, mock_llm: MockLLMClient, settings: Settings
    ) -> None:
        """Test agent name property.

        Args:
            mock_llm: Mock LLM client.
            settings: Test settings.
        """
        agent = ContactExtractorAgent(mock_llm, settings)
        assert agent.name == "ContactExtractorAgent"

    def test_agent_description_property(
        self, mock_llm: MockLLMClient, settings: Settings
    ) -> None:
        """Test agent description property.

        Args:
            mock_llm: Mock LLM client.
            settings: Test settings.
        """
        agent = ContactExtractorAgent(mock_llm, settings)
        assert "contact" in agent.description.lower()

    @pytest.mark.asyncio
    async def test_agent_run_success(
        self, mock_llm: MockLLMClient, settings: Settings
    ) -> None:
        """Test successful agent execution.

        Args:
            mock_llm: Mock LLM client.
            settings: Test settings.
        """
        mock_llm.add_response('{"full_name": "John Doe", "email": "john@example.com"}')
        agent = ContactExtractorAgent(mock_llm, settings)
        result = await agent.run("John Doe's resume")

        assert result.success is True
        assert result.agent_name == "ContactExtractorAgent"
        assert result.data.get("full_name") == "John Doe"
        assert result.execution_time_seconds >= 0

    @pytest.mark.asyncio
    async def test_agent_run_failure(
        self, mock_llm: MockLLMClient, settings: Settings
    ) -> None:
        """Test agent execution failure handling.

        Args:
            mock_llm: Mock LLM client.
            settings: Test settings.
        """
        mock_llm.add_response("invalid json response")
        agent = ContactExtractorAgent(mock_llm, settings)
        result = await agent.run("test resume")

        # Should still succeed but with empty or raw data
        assert result.agent_name == "ContactExtractorAgent"


class TestContactExtractorAgent:
    """Test cases for ContactExtractorAgent."""

    @pytest.fixture
    def settings(self) -> Settings:
        """Create test settings.

        Returns:
            Settings: Test settings.
        """
        return Settings(openai_api_key="test-key")

    @pytest.fixture
    def mock_llm(self) -> MockLLMClient:
        """Create mock LLM client.

        Returns:
            MockLLMClient: Mock LLM client.
        """
        return MockLLMClient()

    def test_name(self, mock_llm: MockLLMClient, settings: Settings) -> None:
        """Test agent name.

        Args:
            mock_llm: Mock LLM client.
            settings: Test settings.
        """
        agent = ContactExtractorAgent(mock_llm, settings)
        assert agent.name == "ContactExtractorAgent"

    def test_description(self, mock_llm: MockLLMClient, settings: Settings) -> None:
        """Test agent description.

        Args:
            mock_llm: Mock LLM client.
            settings: Test settings.
        """
        agent = ContactExtractorAgent(mock_llm, settings)
        assert "contact" in agent.description.lower()


class TestSkillsExtractorAgent:
    """Test cases for SkillsExtractorAgent."""

    @pytest.fixture
    def settings(self) -> Settings:
        """Create test settings.

        Returns:
            Settings: Test settings.
        """
        return Settings(openai_api_key="test-key")

    @pytest.fixture
    def mock_llm(self) -> MockLLMClient:
        """Create mock LLM client.

        Returns:
            MockLLMClient: Mock LLM client.
        """
        return MockLLMClient()

    def test_name(self, mock_llm: MockLLMClient, settings: Settings) -> None:
        """Test agent name.

        Args:
            mock_llm: Mock LLM client.
            settings: Test settings.
        """
        agent = SkillsExtractorAgent(mock_llm, settings)
        assert agent.name == "SkillsExtractorAgent"

    def test_description(self, mock_llm: MockLLMClient, settings: Settings) -> None:
        """Test agent description.

        Args:
            mock_llm: Mock LLM client.
            settings: Test settings.
        """
        agent = SkillsExtractorAgent(mock_llm, settings)
        assert "skill" in agent.description.lower()


class TestExperienceExtractorAgent:
    """Test cases for ExperienceExtractorAgent."""

    @pytest.fixture
    def settings(self) -> Settings:
        """Create test settings.

        Returns:
            Settings: Test settings.
        """
        return Settings(openai_api_key="test-key")

    @pytest.fixture
    def mock_llm(self) -> MockLLMClient:
        """Create mock LLM client.

        Returns:
            MockLLMClient: Mock LLM client.
        """
        return MockLLMClient()

    def test_name(self, mock_llm: MockLLMClient, settings: Settings) -> None:
        """Test agent name.

        Args:
            mock_llm: Mock LLM client.
            settings: Test settings.
        """
        agent = ExperienceExtractorAgent(mock_llm, settings)
        assert agent.name == "ExperienceExtractorAgent"

    def test_description(self, mock_llm: MockLLMClient, settings: Settings) -> None:
        """Test agent description.

        Args:
            mock_llm: Mock LLM client.
            settings: Test settings.
        """
        agent = ExperienceExtractorAgent(mock_llm, settings)
        assert "experience" in agent.description.lower()


class TestEducationExtractorAgent:
    """Test cases for EducationExtractorAgent."""

    @pytest.fixture
    def settings(self) -> Settings:
        """Create test settings.

        Returns:
            Settings: Test settings.
        """
        return Settings(openai_api_key="test-key")

    @pytest.fixture
    def mock_llm(self) -> MockLLMClient:
        """Create mock LLM client.

        Returns:
            MockLLMClient: Mock LLM client.
        """
        return MockLLMClient()

    def test_name(self, mock_llm: MockLLMClient, settings: Settings) -> None:
        """Test agent name.

        Args:
            mock_llm: Mock LLM client.
            settings: Test settings.
        """
        agent = EducationExtractorAgent(mock_llm, settings)
        assert agent.name == "EducationExtractorAgent"

    def test_description(self, mock_llm: MockLLMClient, settings: Settings) -> None:
        """Test agent description.

        Args:
            mock_llm: Mock LLM client.
            settings: Test settings.
        """
        agent = EducationExtractorAgent(mock_llm, settings)
        assert "education" in agent.description.lower()


class TestResumeParserAgent:
    """Test cases for ResumeParserAgent."""

    @pytest.fixture
    def settings(self) -> Settings:
        """Create test settings.

        Returns:
            Settings: Test settings.
        """
        return Settings(openai_api_key="test-key")

    @pytest.fixture
    def mock_llm(self) -> MockLLMClient:
        """Create mock LLM client.

        Returns:
            MockLLMClient: Mock LLM client.
        """
        return MockLLMClient()

    def test_name(self, mock_llm: MockLLMClient, settings: Settings) -> None:
        """Test agent name.

        Args:
            mock_llm: Mock LLM client.
            settings: Test settings.
        """
        agent = ResumeParserAgent(mock_llm, settings)
        assert agent.name == "ResumeParserAgent"

    def test_description(self, mock_llm: MockLLMClient, settings: Settings) -> None:
        """Test agent description.

        Args:
            mock_llm: Mock LLM client.
            settings: Test settings.
        """
        agent = ResumeParserAgent(mock_llm, settings)
        assert "orchestrat" in agent.description.lower()
