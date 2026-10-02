"""Tests for agent implementations."""

from __future__ import annotations

import pytest

from candidate_matcher.agents.bias_aware_ranker import BiasAwareRankerAgent
from candidate_matcher.agents.culture_fit_assessor import CultureFitAssessorAgent
from candidate_matcher.agents.match_explainer import MatchExplainerAgent
from candidate_matcher.agents.semantic_matcher import SemanticMatcherAgent
from candidate_matcher.agents.skills_gap_analyzer import SkillsGapAnalyzerAgent
from candidate_matcher.integrations.embedding_client import MockEmbeddingClient
from candidate_matcher.integrations.llm_client import MockLLMClient
from candidate_matcher.models.schemas import MatchResult


@pytest.mark.asyncio
async def test_semantic_matcher_agent(sample_candidate, sample_job) -> None:
    """Test the semantic matcher agent.

    Args:
        sample_candidate: Sample candidate fixture.
        sample_job: Sample job fixture.
    """
    agent = SemanticMatcherAgent(embedding_client=MockEmbeddingClient())
    result = await agent.execute(candidate=sample_candidate, job=sample_job)
    assert "embedding_similarity" in result
    assert "combined_score" in result
    assert 0 <= result["combined_score"] <= 1


@pytest.mark.asyncio
async def test_skills_gap_analyzer_agent(sample_candidate, sample_job) -> None:
    """Test the skills gap analyzer agent.

    Args:
        sample_candidate: Sample candidate fixture.
        sample_job: Sample job fixture.
    """
    agent = SkillsGapAnalyzerAgent()
    result = await agent.execute(candidate=sample_candidate, job=sample_job)
    assert result.candidate_id == sample_candidate.id
    assert result.job_id == sample_job.id
    assert 0 <= result.gap_score <= 1
    assert 0 <= result.coverage_ratio <= 1


@pytest.mark.asyncio
async def test_bias_aware_ranker_agent(sample_candidate, sample_job) -> None:
    """Test the bias-aware ranker agent.

    Args:
        sample_candidate: Sample candidate fixture.
        sample_job: Sample job fixture.
    """
    agent = BiasAwareRankerAgent()
    base_scores = {"semantic": 0.8, "skills": 0.7, "experience": 0.6, "culture": 0.9}
    result = await agent.execute(candidate=sample_candidate, job=sample_job, base_scores=base_scores)
    assert "adjusted_score" in result
    assert "bias_score" in result
    assert "bias_report" in result
    assert 0 <= result["adjusted_score"] <= 1


@pytest.mark.asyncio
async def test_culture_fit_assessor_agent(sample_candidate, sample_job) -> None:
    """Test the culture fit assessor agent.

    Args:
        sample_candidate: Sample candidate fixture.
        sample_job: Sample job fixture.
    """
    agent = CultureFitAssessorAgent()
    result = await agent.execute(candidate=sample_candidate, job=sample_job)
    assert "fit_score" in result
    assert "aligned_values" in result
    assert "summary" in result
    assert 0 <= result["fit_score"] <= 1


@pytest.mark.asyncio
async def test_match_explainer_agent(sample_candidate, sample_job) -> None:
    """Test the match explainer agent.

    Args:
        sample_candidate: Sample candidate fixture.
        sample_job: Sample job fixture.
    """
    agent = MatchExplainerAgent()
    match_result = MatchResult(
        job_id=sample_job.id,
        candidate_id=sample_candidate.id,
        overall_score=0.75,
        semantic_score=0.8,
        skills_score=0.7,
        experience_score=0.6,
        culture_score=0.9,
    )
    result = await agent.execute(
        candidate=sample_candidate,
        job=sample_job,
        match_result=match_result,
    )
    assert result.match_id == match_result.match_id
    assert "summary" in result.summary or len(result.summary) > 0
    assert isinstance(result.strengths, list)
    assert isinstance(result.weaknesses, list)
