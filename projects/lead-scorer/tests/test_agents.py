"""Tests for lead scorer agents."""

from __future__ import annotations

import pytest

from lead_scorer.agents.research import ResearchAgent, ResearchResult
from lead_scorer.agents.evidence import EvidenceAgent, EvidenceResult
from lead_scorer.agents.scoring import ScoringAgent, ScoringResult, LeadGrade
from lead_scorer.agents.qualification import (
    QualificationAgent,
    QualificationResult,
    QualificationFramework,
    QualificationStatus,
)
from lead_scorer.agents.churn_prediction import (
    ChurnPredictionAgent,
    ChurnPredictionResult,
    ChurnRiskLevel,
)
from lead_scorer.agents.next_best_action import (
    NextBestActionAgent,
    NextBestActionResult,
    ActionType,
)
from lead_scorer.agents.insight_synthesis import (
    InsightSynthesisAgent,
    SynthesizedInsights,
)


@pytest.fixture
def research_agent() -> ResearchAgent:
    """Create a research agent for testing."""
    return ResearchAgent(timeout_seconds=10, max_retries=1)


@pytest.fixture
def evidence_agent() -> EvidenceAgent:
    """Create an evidence agent for testing."""
    return EvidenceAgent(timeout_seconds=10, max_retries=1)


@pytest.fixture
def scoring_agent() -> ScoringAgent:
    """Create a scoring agent for testing."""
    return ScoringAgent(timeout_seconds=10, max_retries=1)


@pytest.fixture
def qualification_agent() -> QualificationAgent:
    """Create a qualification agent for testing."""
    return QualificationAgent(timeout_seconds=10, max_retries=1)


@pytest.fixture
def churn_agent() -> ChurnPredictionAgent:
    """Create a churn prediction agent for testing."""
    return ChurnPredictionAgent(timeout_seconds=10, max_retries=1)


@pytest.fixture
def nba_agent() -> NextBestActionAgent:
    """Create a next best action agent for testing."""
    return NextBestActionAgent(timeout_seconds=10, max_retries=1)


@pytest.fixture
def synthesis_agent() -> InsightSynthesisAgent:
    """Create an insight synthesis agent for testing."""
    return InsightSynthesisAgent(timeout_seconds=10, max_retries=1)


class TestResearchAgent:
    """Tests for ResearchAgent."""

    @pytest.mark.asyncio
    async def test_research_returns_result(self, research_agent: ResearchAgent) -> None:
        """Test that research returns a valid result."""
        result = await research_agent.research("example.com", "Example Corp")
        assert isinstance(result, ResearchResult)
        assert result.firmographic.domain if hasattr(result.firmographic, 'domain') else True
        assert result.confidence >= 0.0
        assert result.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_research_caches_results(self, research_agent: ResearchAgent) -> None:
        """Test that research results are cached."""
        result1 = await research_agent.research("cached.com")
        result2 = await research_agent.research("cached.com")
        assert result1 == result2

    @pytest.mark.asyncio
    async def test_research_invalid_domain(self, research_agent: ResearchAgent) -> None:
        """Test that research raises on invalid domain."""
        with pytest.raises(ValueError):
            await research_agent.research("")

    @pytest.mark.asyncio
    async def test_clear_cache(self, research_agent: ResearchAgent) -> None:
        """Test cache clearing."""
        await research_agent.research("clearcache.com")
        research_agent.clear_cache()
        assert len(research_agent._cache) == 0


class TestEvidenceAgent:
    """Tests for EvidenceAgent."""

    @pytest.mark.asyncio
    async def test_collect_returns_result(self, evidence_agent: EvidenceAgent) -> None:
        """Test that evidence collection returns a valid result."""
        result = await evidence_agent.collect("lead-123")
        assert isinstance(result, EvidenceResult)
        assert result.total_engagements >= 0
        assert 0.0 <= result.engagement_score <= 1.0
        assert 0.0 <= result.intent_score <= 1.0

    @pytest.mark.asyncio
    async def test_collect_invalid_lead_id(self, evidence_agent: EvidenceAgent) -> None:
        """Test that evidence collection raises on empty lead_id."""
        with pytest.raises(ValueError):
            await evidence_agent.collect("")


class TestScoringAgent:
    """Tests for ScoringAgent."""

    @pytest.mark.asyncio
    async def test_score_returns_result(self, scoring_agent: ScoringAgent) -> None:
        """Test that scoring returns a valid result."""
        result = await scoring_agent.score("lead-123")
        assert isinstance(result, ScoringResult)
        assert 0.0 <= result.total_score <= 100.0
        assert result.grade in LeadGrade
        assert len(result.components) > 0

    @pytest.mark.asyncio
    async def test_score_with_research_and_evidence(
        self, scoring_agent: ScoringAgent, research_agent: ResearchAgent, evidence_agent: EvidenceAgent
    ) -> None:
        """Test scoring with research and evidence data."""
        research = await research_agent.research("scored.com")
        evidence = await evidence_agent.collect("lead-456")
        result = await scoring_agent.score("lead-456", research=research, evidence=evidence)
        assert result.total_score > 0.0
        assert result.confidence > 0.0

    @pytest.mark.asyncio
    async def test_score_invalid_lead_id(self, scoring_agent: ScoringAgent) -> None:
        """Test that scoring raises on empty lead_id."""
        with pytest.raises(ValueError):
            await scoring_agent.score("")

    def test_weights_must_sum_to_one(self) -> None:
        """Test that invalid weights raise an error."""
        with pytest.raises(ValueError):
            ScoringAgent(weights={"firmographic": 0.5, "engagement": 0.3})


class TestQualificationAgent:
    """Tests for QualificationAgent."""

    @pytest.mark.asyncio
    async def test_qualify_qualified_lead(
        self, qualification_agent: QualificationAgent
    ) -> None:
        """Test qualifying a fully qualified lead."""
        result = await qualification_agent.qualify(
            "lead-123",
            budget=50000,
            authority=True,
            need=True,
            timeline_days=30,
        )
        assert isinstance(result, QualificationResult)
        assert result.status == QualificationStatus.QUALIFIED
        assert result.total_score >= 0.7

    @pytest.mark.asyncio
    async def test_qualify_disqualified_lead(
        self, qualification_agent: QualificationAgent
    ) -> None:
        """Test qualifying a disqualified lead."""
        result = await qualification_agent.qualify(
            "lead-456",
            budget=None,
            authority=None,
            need=None,
            timeline_days=None,
        )
        assert result.status == QualificationStatus.DISQUALIFIED

    @pytest.mark.asyncio
    async def test_qualify_meddic_framework(self) -> None:
        """Test MEDDIC qualification framework."""
        agent = QualificationAgent(framework=QualificationFramework.MEDDIC)
        result = await agent.qualify(
            "lead-789",
            budget=100000,
            authority=True,
            need=True,
            timeline_days=14,
            metrics_score=0.8,
            champion_score=0.7,
        )
        assert result.framework == QualificationFramework.MEDDIC
        assert len(result.criteria) >= 5

    @pytest.mark.asyncio
    async def test_qualify_invalid_lead_id(
        self, qualification_agent: QualificationAgent
    ) -> None:
        """Test that qualification raises on empty lead_id."""
        with pytest.raises(ValueError):
            await qualification_agent.qualify("")


class TestChurnPredictionAgent:
    """Tests for ChurnPredictionAgent."""

    @pytest.mark.asyncio
    async def test_predict_low_risk(self, churn_agent: ChurnPredictionAgent) -> None:
        """Test predicting low churn risk."""
        result = await churn_agent.predict(
            "cust-123",
            usage_decline_pct=5,
            support_tickets_90d=1,
            nps_score=80,
            days_since_last_login=2,
            contract_renewal_days=365,
        )
        assert isinstance(result, ChurnPredictionResult)
        assert result.risk_level == ChurnRiskLevel.LOW
        assert result.churn_probability < 0.3

    @pytest.mark.asyncio
    async def test_predict_high_risk(self, churn_agent: ChurnPredictionAgent) -> None:
        """Test predicting high churn risk."""
        result = await churn_agent.predict(
            "cust-456",
            usage_decline_pct=60,
            support_tickets_90d=8,
            nps_score=-20,
            days_since_last_login=25,
            contract_renewal_days=14,
        )
        assert result.risk_level in (ChurnRiskLevel.HIGH, ChurnRiskLevel.CRITICAL)
        assert result.churn_probability >= 0.6
        assert len(result.recommended_actions) > 0

    @pytest.mark.asyncio
    async def test_predict_invalid_customer_id(
        self, churn_agent: ChurnPredictionAgent
    ) -> None:
        """Test that prediction raises on empty customer_id."""
        with pytest.raises(ValueError):
            await churn_agent.predict("")


class TestNextBestActionAgent:
    """Tests for NextBestActionAgent."""

    @pytest.mark.asyncio
    async def test_recommend_hot_qualified_lead(
        self, nba_agent: NextBestActionAgent, scoring_agent: ScoringAgent
    ) -> None:
        """Test recommendation for hot qualified lead."""
        scoring = ScoringResult(
            lead_id="lead-123",
            total_score=85.0,
            grade=LeadGrade.HOT,
            components=[],
            confidence=0.9,
        )
        result = await nba_agent.recommend("lead-123", scoring_result=scoring)
        assert isinstance(result, NextBestActionResult)
        assert result.primary_action.action_type == ActionType.DEMO
        assert len(result.alternative_actions) > 0

    @pytest.mark.asyncio
    async def test_recommend_cold_lead(
        self, nba_agent: NextBestActionAgent, scoring_agent: ScoringAgent
    ) -> None:
        """Test recommendation for cold lead."""
        scoring = ScoringResult(
            lead_id="lead-456",
            total_score=20.0,
            grade=LeadGrade.COLD,
            components=[],
            confidence=0.5,
        )
        result = await nba_agent.recommend("lead-456", scoring_result=scoring)
        assert result.primary_action.action_type == ActionType.WAIT

    @pytest.mark.asyncio
    async def test_recommend_invalid_lead_id(
        self, nba_agent: NextBestActionAgent
    ) -> None:
        """Test that recommendation raises on empty lead_id."""
        with pytest.raises(ValueError):
            await nba_agent.recommend("")


class TestInsightSynthesisAgent:
    """Tests for InsightSynthesisAgent."""

    @pytest.mark.asyncio
    async def test_synthesize_with_all_agents(
        self,
        synthesis_agent: InsightSynthesisAgent,
        research_agent: ResearchAgent,
        evidence_agent: EvidenceAgent,
        scoring_agent: ScoringAgent,
    ) -> None:
        """Test synthesis with all agent results."""
        research = await research_agent.research("synthesize.com")
        evidence = await evidence_agent.collect("lead-789")
        scoring = await scoring_agent.score(
            "lead-789", research=research, evidence=evidence
        )
        result = await synthesis_agent.synthesize(
            "lead-789",
            research=research,
            evidence=evidence,
            scoring=scoring,
        )
        assert isinstance(result, SynthesizedInsights)
        assert len(result.insights) > 0
        assert result.overall_assessment != ""

    @pytest.mark.asyncio
    async def test_synthesize_minimal_data(
        self, synthesis_agent: InsightSynthesisAgent
    ) -> None:
        """Test synthesis with minimal data."""
        result = await synthesis_agent.synthesize("lead-minimal")
        assert isinstance(result, SynthesizedInsights)
        assert result.lead_id == "lead-minimal"

    @pytest.mark.asyncio
    async def test_synthesize_invalid_lead_id(
        self, synthesis_agent: InsightSynthesisAgent
    ) -> None:
        """Test that synthesis raises on empty lead_id."""
        with pytest.raises(ValueError):
            await synthesis_agent.synthesize("")
