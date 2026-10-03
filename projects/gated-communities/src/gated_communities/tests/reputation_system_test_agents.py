"""Tests for agent implementations."""

import pytest

from reputation_system.agents.badge_manager import BadgeEvaluationInput, BadgeManagerAgent
from reputation_system.agents.reputation_explainer import (
    ExplanationInput,
    ReputationExplainerAgent,
)
from reputation_system.agents.reputation_history import (
    HistoryAnalysisInput,
    ReputationHistoryAgent,
)
from reputation_system.agents.reputation_scorer import ReputationScorerAgent, ScoringInput
from reputation_system.agents.trust_tier import TrustTierAgent, TrustTierInput
from reputation_system.config.settings import Settings
from reputation_system.models.schemas import TrustTierLevel


@pytest.fixture
def settings() -> Settings:
    """Create test settings."""
    return Settings(APP_ENV="testing", OPENAI_API_KEY="")


@pytest.mark.asyncio
async def test_reputation_scorer_agent(settings: Settings) -> None:
    """Test reputation scorer agent."""
    agent = ReputationScorerAgent(settings=settings)
    input_data = ScoringInput(
        member_id="user-123",
        contributions=50,
        positive_feedback=30,
        negative_feedback=5,
        account_age_days=180,
        badge_count=3,
        recent_activity_score=0.8,
        quality_score=0.9,
    )
    result = await agent.run(input_data)
    assert result.member_id == "user-123"
    assert 0 <= result.score <= 1000
    assert result.trust_tier in TrustTierLevel
    assert len(result.factors) > 0
    assert 0 <= result.confidence <= 1


@pytest.mark.asyncio
async def test_badge_manager_agent(settings: Settings) -> None:
    """Test badge manager agent."""
    agent = BadgeManagerAgent(settings=settings)
    input_data = BadgeEvaluationInput(
        member_id="user-123",
        badge_criteria={
            "contributor": {
                "metric": "contributions",
                "threshold": 10,
                "category": "contribution",
                "points": 20,
            },
        },
        member_stats={"contributions": 15},
        current_badges=[],
    )
    result = await agent.run(input_data)
    assert result.member_id == "user-123"
    assert len(result.eligible_badges) > 0


@pytest.mark.asyncio
async def test_trust_tier_agent(settings: Settings) -> None:
    """Test trust tier agent."""
    agent = TrustTierAgent(settings=settings)
    input_data = TrustTierInput(
        member_id="user-123",
        current_score=600,
        current_tier=TrustTierLevel.SILVER,
        account_age_days=120,
        violation_count=0,
        verification_status=True,
    )
    result = await agent.run(input_data)
    assert result.member_id == "user-123"
    assert result.recommended_tier in TrustTierLevel
    assert isinstance(result.can_upgrade, bool)
    assert len(result.benefits) > 0


@pytest.mark.asyncio
async def test_reputation_history_agent(settings: Settings) -> None:
    """Test reputation history agent."""
    agent = ReputationHistoryAgent(settings=settings)
    input_data = HistoryAnalysisInput(
        member_id="user-123",
        history_entries=[
            {"action": "contribution", "score_change": 50},
            {"action": "contribution", "score_change": 30},
            {"action": "badge_earned", "score_change": 20},
        ],
    )
    result = await agent.run(input_data)
    assert result.member_id == "user-123"
    assert result.total_entries == 3
    assert result.net_change == 100
    assert result.trend in ["improving", "declining", "stable", "insufficient_data"]


@pytest.mark.asyncio
async def test_reputation_explainer_agent(settings: Settings) -> None:
    """Test reputation explainer agent."""
    agent = ReputationExplainerAgent(settings=settings)
    input_data = ExplanationInput(
        member_id="user-123",
        current_score=450,
        trust_tier=TrustTierLevel.SILVER,
        factors=[{"name": "contributions", "value": 50, "impact": 100}],
        recent_actions=[{"action": "contribution", "score_change": 50}],
        badge_count=2,
        account_age_days=90,
    )
    result = await agent.run(input_data)
    assert result.member_id == "user-123"
    assert len(result.explanation) > 0
    assert len(result.recommendations) > 0
    assert 0 <= result.confidence <= 1
