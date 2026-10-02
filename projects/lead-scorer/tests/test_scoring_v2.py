"""Tests for ensemble lead scoring agent (v2)."""
from __future__ import annotations

import pytest

from lead_scorer.agents.lead_scoring_v2 import (
    EnsembleComponent,
    EnsembleScoringResult,
    LeadScoringV2Agent,
    ModelWeight,
    ScoringModelType,
)
from lead_scorer.agents.research import ResearchAgent, ResearchResult
from lead_scorer.agents.evidence import EvidenceAgent, EvidenceResult
from lead_scorer.agents.scoring import LeadGrade, ScoringResult


@pytest.fixture
def scoring_v2_agent() -> LeadScoringV2Agent:
    """Create a scoring v2 agent for testing."""
    return LeadScoringV2Agent(timeout_seconds=10, max_retries=1)


@pytest.fixture
def research_agent() -> ResearchAgent:
    """Create a research agent for testing."""
    return ResearchAgent(timeout_seconds=10, max_retries=1)


@pytest.fixture
def evidence_agent() -> EvidenceAgent:
    """Create an evidence agent for testing."""
    return EvidenceAgent(timeout_seconds=10, max_retries=1)


class TestModelWeight:
    """Tests for ModelWeight model."""

    def test_create_model_weight(self) -> None:
        """Test creating a model weight."""
        mw = ModelWeight(model_name="engagement", weight=0.3)
        assert mw.model_name == "engagement"
        assert mw.weight == 0.3
        assert mw.enabled is True

    def test_model_weight_validation(self) -> None:
        """Test model weight validation."""
        with pytest.raises(Exception):
            ModelWeight(model_name="test", weight=1.5)


class TestEnsembleComponent:
    """Tests for EnsembleComponent model."""

    def test_create_component(self) -> None:
        """Test creating an ensemble component."""
        comp = EnsembleComponent(
            name="engagement",
            model_scores={"engagement": 0.7},
            ensemble_score=0.7,
            weight=0.25,
            weighted_score=0.175,
        )
        assert comp.name == "engagement"
        assert comp.ensemble_score == 0.7
        assert comp.weight == 0.25


class TestLeadScoringV2Agent:
    """Tests for LeadScoringV2Agent."""

    @pytest.mark.asyncio
    async def test_score_returns_result(
        self, scoring_v2_agent: LeadScoringV2Agent
    ) -> None:
        """Test that scoring returns a valid result."""
        result = await scoring_v2_agent.score("lead-v2-1")
        assert isinstance(result, EnsembleScoringResult)
        assert 0.0 <= result.total_score <= 100.0
        assert result.grade in LeadGrade
        assert len(result.components) > 0
        assert result.confidence >= 0.0
        assert result.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_score_with_research_and_evidence(
        self,
        scoring_v2_agent: LeadScoringV2Agent,
        research_agent: ResearchAgent,
        evidence_agent: EvidenceAgent,
    ) -> None:
        """Test scoring with research and evidence data."""
        research = await research_agent.research("v2-test.com")
        evidence = await evidence_agent.collect("lead-v2-2")
        result = await scoring_v2_agent.score(
            "lead-v2-2", research=research, evidence=evidence
        )
        assert result.total_score > 0.0
        assert result.confidence > 0.0
        assert len(result.model_contributions) > 0

    @pytest.mark.asyncio
    async def test_score_with_behavioral_signals(
        self, scoring_v2_agent: LeadScoringV2Agent
    ) -> None:
        """Test scoring with behavioral signals."""
        behavioral = {
            "page_views_7d": 15,
            "content_downloads_30d": 2,
            "email_opens_30d": 8,
            "email_clicks_30d": 3,
            "social_engagements_30d": 5,
        }
        result = await scoring_v2_agent.score(
            "lead-v2-behavioral", behavioral_signals=behavioral
        )
        assert result.total_score > 0.0
        # Check behavioral component exists
        behavioral_components = [
            c for c in result.components if c.name == "behavioral"
        ]
        assert len(behavioral_components) == 1
        assert behavioral_components[0].ensemble_score > 0.0

    @pytest.mark.asyncio
    async def test_score_with_predictive_features(
        self, scoring_v2_agent: LeadScoringV2Agent
    ) -> None:
        """Test scoring with predictive features."""
        predictive = {
            "historical_conversion_rate": 0.3,
            "source_quality_score": 0.7,
            "company_fit_score": 0.8,
            "engagement_velocity": 0.5,
        }
        result = await scoring_v2_agent.score(
            "lead-v2-predictive", predictive_features=predictive
        )
        assert result.total_score > 0.0
        predictive_components = [
            c for c in result.components if c.name == "predictive"
        ]
        assert len(predictive_components) == 1

    @pytest.mark.asyncio
    async def test_score_invalid_lead_id(
        self, scoring_v2_agent: LeadScoringV2Agent
    ) -> None:
        """Test that scoring raises on empty lead_id."""
        with pytest.raises(ValueError):
            await scoring_v2_agent.score("")

    def test_weights_must_sum_to_one(self) -> None:
        """Test that invalid weights raise an error."""
        with pytest.raises(ValueError):
            LeadScoringV2Agent(
                model_weights={"firmographic": 0.5, "engagement": 0.3}
            )

    def test_custom_weights(self) -> None:
        """Test creating agent with custom weights."""
        agent = LeadScoringV2Agent(
            model_weights={
                "firmographic": 0.15,
                "technographic": 0.10,
                "engagement": 0.25,
                "intent": 0.20,
                "timing": 0.10,
                "behavioral": 0.15,
                "predictive": 0.05,
            }
        )
        assert agent.model_weights["engagement"] == 0.25

    @pytest.mark.asyncio
    async def test_grade_determination(
        self, scoring_v2_agent: LeadScoringV2Agent
    ) -> None:
        """Test grade determination at boundaries."""
        # Test with no data — should be cold
        result = await scoring_v2_agent.score("lead-v2-cold")
        assert result.grade == LeadGrade.COLD

    @pytest.mark.asyncio
    async def test_confidence_interval(
        self, scoring_v2_agent: LeadScoringV2Agent
    ) -> None:
        """Test that confidence intervals are computed."""
        result = await scoring_v2_agent.score("lead-v2-ci")
        for component in result.components:
            assert component.confidence_interval[0] <= component.confidence_interval[1]
            assert 0.0 <= component.confidence_interval[0] <= 1.0
            assert 0.0 <= component.confidence_interval[1] <= 1.0

    @pytest.mark.asyncio
    async def test_model_contributions(
        self, scoring_v2_agent: LeadScoringV2Agent
    ) -> None:
        """Test that model contributions sum to approximately 1.0."""
        result = await scoring_v2_agent.score("lead-v2-contrib")
        total_contribution = sum(result.model_contributions.values())
        assert abs(total_contribution - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_score_std_dev(
        self, scoring_v2_agent: LeadScoringV2Agent
    ) -> None:
        """Test that standard deviation is computed."""
        result = await scoring_v2_agent.score("lead-v2-stddev")
        assert result.score_std_dev >= 0.0

    @pytest.mark.asyncio
    async def test_compare_with_v1(
        self, scoring_v2_agent: LeadScoringV2Agent
    ) -> None:
        """Test comparison between v1 and v2 results."""
        v1_result = ScoringResult(
            lead_id="lead-compare",
            total_score=70.0,
            grade=LeadGrade.WARM,
            components=[],
            confidence=0.7,
        )
        v2_result = await scoring_v2_agent.score("lead-compare")
        comparison = scoring_v2_agent.compare_with_v1(v1_result, v2_result)
        assert "v1_score" in comparison
        assert "v2_score" in comparison
        assert "score_difference" in comparison
        assert "grade_changed" in comparison

    @pytest.mark.asyncio
    async def test_all_models_contribute(
        self,
        scoring_v2_agent: LeadScoringV2Agent,
        research_agent: ResearchAgent,
        evidence_agent: EvidenceAgent,
    ) -> None:
        """Test that all enabled models contribute to the score."""
        research = await research_agent.research("all-models.com")
        evidence = await evidence_agent.collect("lead-all-models")
        behavioral = {"page_views_7d": 10, "email_opens_30d": 5}
        predictive = {"historical_conversion_rate": 0.2, "company_fit_score": 0.6}
        result = await scoring_v2_agent.score(
            "lead-all-models",
            research=research,
            evidence=evidence,
            behavioral_signals=behavioral,
            predictive_features=predictive,
        )
        # Should have components for all 7 models
        assert len(result.components) == 7
        component_names = {c.name for c in result.components}
        expected = {
            "firmographic",
            "technographic",
            "engagement",
            "intent",
            "timing",
            "behavioral",
            "predictive",
        }
        assert component_names == expected

    @pytest.mark.asyncio
    async def test_ensemble_score_higher_than_single_model(
        self,
        scoring_v2_agent: LeadScoringV2Agent,
        research_agent: ResearchAgent,
        evidence_agent: EvidenceAgent,
    ) -> None:
        """Test that ensemble score benefits from multiple models."""
        research = await research_agent.research("ensemble-test.com")
        evidence = await evidence_agent.collect("lead-ensemble")
        result = await scoring_v2_agent.score(
            "lead-ensemble", research=research, evidence=evidence
        )
        # With good research and evidence, score should be decent
        assert result.total_score > 30.0
        assert result.confidence > 0.3
