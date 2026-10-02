"""Pytest configuration and fixtures."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from candidate_matcher.config.settings import Settings
from candidate_matcher.integrations.embedding_client import MockEmbeddingClient
from candidate_matcher.integrations.llm_client import MockLLMClient
from candidate_matcher.integrations.vector_store import InMemoryVectorStore
from candidate_matcher.main import create_app
from candidate_matcher.models.schemas import (
    Candidate,
    JobPosting,
    JobRequirement,
    Skill,
    SkillLevel,
)


@pytest.fixture
def settings() -> Settings:
    """Create test settings.

    Returns:
        Test settings with mock LLM provider.
    """
    return Settings(
        llm_provider="mock",
        environment="development",
        debug=True,
    )


@pytest.fixture
def mock_llm_client() -> MockLLMClient:
    """Create a mock LLM client.

    Returns:
        Mock LLM client instance.
    """
    return MockLLMClient()


@pytest.fixture
def mock_embedding_client() -> MockEmbeddingClient:
    """Create a mock embedding client.

    Returns:
        Mock embedding client instance.
    """
    return MockEmbeddingClient()


@pytest.fixture
def sample_candidate() -> Candidate:
    """Create a sample candidate for testing.

    Returns:
        Sample candidate profile.
    """
    return Candidate(
        id=uuid4(),
        name="Jane Doe",
        email="jane@example.com",
        skills=[
            Skill(name="Python", level=SkillLevel.ADVANCED, years_experience=5.0),
            Skill(name="Machine Learning", level=SkillLevel.INTERMEDIATE, years_experience=3.0),
            Skill(name="SQL", level=SkillLevel.ADVANCED, years_experience=4.0),
        ],
        experience_years=5.0,
        education=[{"degree": "BS", "field": "Computer Science"}],
        work_history=[{"title": "Software Engineer", "company": "TechCorp"}],
        preferences={"work_style": "collaborative", "values": ["innovation", "transparency"]},
    )


@pytest.fixture
def sample_job() -> JobPosting:
    """Create a sample job posting for testing.

    Returns:
        Sample job posting.
    """
    return JobPosting(
        id=uuid4(),
        title="Senior Software Engineer",
        description="We are looking for a senior software engineer to join our innovative team.",
        company="TechCorp",
        department="Engineering",
        location="Remote",
        requirements=[
            JobRequirement(skill_name="Python", minimum_level=SkillLevel.ADVANCED),
            JobRequirement(skill_name="Machine Learning", minimum_level=SkillLevel.INTERMEDIATE),
            JobRequirement(
                skill_name="Kubernetes",
                minimum_level=SkillLevel.INTERMEDIATE,
                preferred=True,
            ),
        ],
        responsibilities=["Design and implement scalable systems", "Mentor junior engineers"],
        culture_values=["innovation", "transparency", "collaboration"],
    )


@pytest.fixture
def test_client(
    settings: Settings,  # noqa: ARG001
    mock_llm_client: MockLLMClient,
    mock_embedding_client: MockEmbeddingClient,
    sample_candidate: Candidate,
    sample_job: JobPosting,
) -> TestClient:
    """Create a test client with pre-populated state.

    Args:
        settings: Test settings.
        mock_llm_client: Mock LLM client.
        mock_embedding_client: Mock embedding client.
        sample_candidate: Sample candidate.
        sample_job: Sample job.

    Returns:
        Configured test client.
    """
    from candidate_matcher.agents.bias_aware_ranker import BiasAwareRankerAgent
    from candidate_matcher.agents.culture_fit_assessor import CultureFitAssessorAgent
    from candidate_matcher.agents.match_explainer import MatchExplainerAgent
    from candidate_matcher.agents.semantic_matcher import SemanticMatcherAgent
    from candidate_matcher.agents.skills_gap_analyzer import SkillsGapAnalyzerAgent

    app = create_app()

    # Override app state with test doubles
    app.state.llm_client = mock_llm_client
    app.state.embedding_client = mock_embedding_client
    app.state.vector_store = InMemoryVectorStore()
    app.state.candidate_store = {sample_candidate.id: sample_candidate}
    app.state.job_store = {sample_job.id: sample_job}
    app.state.match_store = {}

    # Initialize agents
    app.state.semantic_matcher = SemanticMatcherAgent(
        embedding_client=mock_embedding_client,
        llm_client=mock_llm_client,
    )
    app.state.skills_gap_analyzer = SkillsGapAnalyzerAgent(llm_client=mock_llm_client)
    app.state.bias_aware_ranker = BiasAwareRankerAgent(llm_client=mock_llm_client)
    app.state.culture_fit_assessor = CultureFitAssessorAgent(llm_client=mock_llm_client)
    app.state.match_explainer = MatchExplainerAgent(llm_client=mock_llm_client)

    return TestClient(app)
