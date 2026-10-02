"""Tests for agent implementations."""

from __future__ import annotations

from datetime import date

import pytest

from recruitment_analytics.agents.cost_analyzer import CostAnalyzerAgent
from recruitment_analytics.agents.diversity_analyzer import DiversityAnalyzerAgent
from recruitment_analytics.agents.funnel_analyzer import FunnelAnalyzerAgent
from recruitment_analytics.agents.predictive_hiring import PredictiveHiringAgent
from recruitment_analytics.agents.source_tracker import SourceTrackerAgent
from recruitment_analytics.models.schemas import (
    CostAnalysisRequest,
    DiversityAnalysisRequest,
    FunnelAnalysisRequest,
    PredictiveHiringRequest,
    CandidateFeatures,
    SourceTrackingRequest,
)


class TestFunnelAnalyzerAgent:
    """Test FunnelAnalyzerAgent."""

    @pytest.mark.asyncio
    async def test_run(self) -> None:
        """Test funnel analyzer execution."""
        agent = FunnelAnalyzerAgent()
        request = FunnelAnalysisRequest(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
        )
        response = await agent.run(request)
        assert response.funnel is not None
        assert len(response.funnel.stages) > 0
        assert response.funnel.total_applicants > 0


class TestSourceTrackerAgent:
    """Test SourceTrackerAgent."""

    @pytest.mark.asyncio
    async def test_run(self) -> None:
        """Test source tracker execution."""
        agent = SourceTrackerAgent()
        request = SourceTrackingRequest(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
        )
        response = await agent.run(request)
        assert len(response.sources) > 0
        assert len(response.top_performing) > 0


class TestPredictiveHiringAgent:
    """Test PredictiveHiringAgent."""

    @pytest.mark.asyncio
    async def test_run(self) -> None:
        """Test predictive hiring execution."""
        agent = PredictiveHiringAgent()
        request = PredictiveHiringRequest(
            candidate_id="cand-123",
            role="Software Engineer",
            features=CandidateFeatures(
                years_experience=5.0,
                education_level="bachelor",
                skills_match_score=0.85,
                interview_scores=[0.8, 0.9],
                cultural_fit_score=0.9,
                referral_boost=True,
            ),
        )
        response = await agent.run(request)
        assert response.prediction is not None
        assert response.prediction.candidate_id == "cand-123"
        assert response.prediction.score > 0


class TestDiversityAnalyzerAgent:
    """Test DiversityAnalyzerAgent."""

    @pytest.mark.asyncio
    async def test_run(self) -> None:
        """Test diversity analyzer execution."""
        agent = DiversityAnalyzerAgent()
        request = DiversityAnalysisRequest(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
        )
        response = await agent.run(request)
        assert response.report is not None
        assert response.report.gender is not None
        assert response.report.ethnicity is not None


class TestCostAnalyzerAgent:
    """Test CostAnalyzerAgent."""

    @pytest.mark.asyncio
    async def test_run(self) -> None:
        """Test cost analyzer execution."""
        agent = CostAnalyzerAgent()
        request = CostAnalysisRequest(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
        )
        response = await agent.run(request)
        assert response.report is not None
        assert response.report.total_cost > 0
        assert len(response.report.breakdown) > 0

