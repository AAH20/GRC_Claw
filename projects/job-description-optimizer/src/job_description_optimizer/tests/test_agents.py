"""Tests for agent implementations."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from job_description_optimizer.agents.ats_compatibility import ATSCompatibilityAgent
from job_description_optimizer.agents.bias_remover import BiasRemoverAgent
from job_description_optimizer.agents.keyword_optimizer import KeywordOptimizerAgent
from job_description_optimizer.agents.seo_optimizer import SEOOptimizerAgent
from job_description_optimizer.agents.tone_analyzer import ToneAnalyzerAgent
from job_description_optimizer.config import Settings
from job_description_optimizer.models import JobDescription


@pytest.fixture
def mock_llm():
    """Create a mock language model."""
    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=MagicMock(content='{"result": "test"}'))
    return llm


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        app_name="test",
        app_env="testing",
        openai_api_key="sk-test",
        openai_model="gpt-4o-mini",
    )


@pytest.fixture
def sample_jd():
    """Create a sample job description."""
    return JobDescription(
        title="Software Engineer",
        description="We are looking for a software engineer.",
    )


class TestBiasRemoverAgent:
    """Tests for BiasRemoverAgent."""

    def test_agent_name(self, mock_llm, settings) -> None:
        """Test agent name property."""
        agent = BiasRemoverAgent(llm=mock_llm, settings=settings)
        assert agent.name == "bias_remover"

    def test_agent_description(self, mock_llm, settings) -> None:
        """Test agent description property."""
        agent = BiasRemoverAgent(llm=mock_llm, settings=settings)
        assert "bias" in agent.description.lower()

    def test_agent_capabilities(self, mock_llm, settings) -> None:
        """Test agent capabilities."""
        agent = BiasRemoverAgent(llm=mock_llm, settings=settings)
        caps = agent.get_capabilities()
        assert len(caps) > 0
        assert "bias_detection" in caps

    def test_to_info(self, mock_llm, settings) -> None:
        """Test agent info serialization."""
        agent = BiasRemoverAgent(llm=mock_llm, settings=settings)
        info = agent.to_info()
        assert info["name"] == "bias_remover"
        assert info["status"] == "available"


class TestSEOOptimizerAgent:
    """Tests for SEOOptimizerAgent."""

    def test_agent_name(self, mock_llm, settings) -> None:
        """Test agent name property."""
        agent = SEOOptimizerAgent(llm=mock_llm, settings=settings)
        assert agent.name == "seo_optimizer"

    def test_agent_capabilities(self, mock_llm, settings) -> None:
        """Test agent capabilities."""
        agent = SEOOptimizerAgent(llm=mock_llm, settings=settings)
        caps = agent.get_capabilities()
        assert "keyword_optimization" in caps


class TestATSCompatibilityAgent:
    """Tests for ATSCompatibilityAgent."""

    def test_agent_name(self, mock_llm, settings) -> None:
        """Test agent name property."""
        agent = ATSCompatibilityAgent(llm=mock_llm, settings=settings)
        assert agent.name == "ats_compatibility"

    def test_agent_capabilities(self, mock_llm, settings) -> None:
        """Test agent capabilities."""
        agent = ATSCompatibilityAgent(llm=mock_llm, settings=settings)
        caps = agent.get_capabilities()
        assert "ats_formatting_check" in caps


class TestToneAnalyzerAgent:
    """Tests for ToneAnalyzerAgent."""

    def test_agent_name(self, mock_llm, settings) -> None:
        """Test agent name property."""
        agent = ToneAnalyzerAgent(llm=mock_llm, settings=settings)
        assert agent.name == "tone_analyzer"

    def test_agent_capabilities(self, mock_llm, settings) -> None:
        """Test agent capabilities."""
        agent = ToneAnalyzerAgent(llm=mock_llm, settings=settings)
        caps = agent.get_capabilities()
        assert "tone_detection" in caps


class TestKeywordOptimizerAgent:
    """Tests for KeywordOptimizerAgent."""

    def test_agent_name(self, mock_llm, settings) -> None:
        """Test agent name property."""
        agent = KeywordOptimizerAgent(llm=mock_llm, settings=settings)
        assert agent.name == "keyword_optimizer"

    def test_agent_capabilities(self, mock_llm, settings) -> None:
        """Test agent capabilities."""
        agent = KeywordOptimizerAgent(llm=mock_llm, settings=settings)
        caps = agent.get_capabilities()
        assert "keyword_extraction" in caps
