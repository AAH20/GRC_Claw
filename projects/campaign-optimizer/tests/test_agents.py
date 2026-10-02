"""Tests for the Campaign Optimizer agents."""

from __future__ import annotations

import pytest

from campaign_optimizer.agents import (
    AudienceAgent,
    BiddingAgent,
    CreativeAgent,
    CriticAgent,
    ResearchAgent,
    StrategyAgent,
)


# ─── Strategy Agent Tests ───────────────────────────────────────────


class TestStrategyAgent:
    """Tests for the Strategy Agent."""

    @pytest.fixture
    def agent(self) -> StrategyAgent:
        """Create a Strategy Agent instance."""
        return StrategyAgent()

    @pytest.mark.asyncio
    async def test_create_plan_basic(self, agent: StrategyAgent) -> None:
        """Test basic campaign plan creation."""
        plan = await agent.create_plan(
            business_goal="Increase online sales",
            total_budget=10000.0,
            duration_days=30,
        )
        assert plan.total_budget == 10000.0
        assert plan.duration_days == 30
        assert len(plan.platforms) > 0
        assert len(plan.budget_allocation) > 0
        assert plan.objective.value == "sales"

    @pytest.mark.asyncio
    async def test_create_plan_budget_allocation(self, agent: StrategyAgent) -> None:
        """Test that budget is allocated across platforms."""
        plan = await agent.create_plan(
            business_goal="Generate leads",
            total_budget=5000.0,
            duration_days=14,
            platforms=["meta", "google"],
        )
        total_allocated = sum(plan.budget_allocation.values())
        assert abs(total_allocated - 5000.0) < 0.01

    @pytest.mark.asyncio
    async def test_create_plan_invalid_budget(self, agent: StrategyAgent) -> None:
        """Test that invalid budget raises ValueError."""
        with pytest.raises(ValueError, match="Budget must be positive"):
            await agent.create_plan(
                business_goal="Test",
                total_budget=-100.0,
                duration_days=30,
            )

    @pytest.mark.asyncio
    async def test_create_plan_invalid_duration(self, agent: StrategyAgent) -> None:
        """Test that invalid duration raises ValueError."""
        with pytest.raises(ValueError, match="Duration must be positive"):
            await agent.create_plan(
                business_goal="Test",
                total_budget=1000.0,
                duration_days=0,
            )

    @pytest.mark.asyncio
    async def test_adjust_strategy(self, agent: StrategyAgent) -> None:
        """Test strategy adjustment based on performance data."""
        await agent.create_plan(
            business_goal="Increase sales",
            total_budget=10000.0,
            duration_days=30,
        )
        performance = {
            "meta": {"roas": 0.8},
            "google": {"roas": 4.0},
        }
        adjustments = await agent.adjust_strategy(performance)
        assert "budget_reallocation" in adjustments
        assert "meta" in adjustments["budget_reallocation"]
        assert "google" in adjustments["budget_reallocation"]


# ─── Research Agent Tests ───────────────────────────────────────────


class TestResearchAgent:
    """Tests for the Research Agent."""

    @pytest.fixture
    def agent(self) -> ResearchAgent:
        """Create a Research Agent instance."""
        return ResearchAgent()

    @pytest.mark.asyncio
    async def test_conduct_research(self, agent: ResearchAgent) -> None:
        """Test basic research report generation."""
        report = await agent.conduct_research(
            industry="e-commerce",
            target_audience="online shoppers aged 25-45",
            competitors=["competitor_a", "competitor_b"],
        )
        assert len(report.market_insights) > 0
        assert len(report.competitor_analyses) == 2
        assert len(report.audience_segments) > 0
        assert len(report.recommendations) > 0

    @pytest.mark.asyncio
    async def test_research_insights_confidence(self, agent: ResearchAgent) -> None:
        """Test that research insights have valid confidence scores."""
        report = await agent.conduct_research(
            industry="saas",
            target_audience="B2B decision makers",
        )
        for insight in report.market_insights:
            assert 0.0 <= insight.confidence <= 1.0


# ─── Creative Agent Tests ──────────────────────────────────────────


class TestCreativeAgent:
    """Tests for the Creative Agent."""

    @pytest.fixture
    def agent(self) -> CreativeAgent:
        """Create a Creative Agent instance."""
        return CreativeAgent()

    @pytest.mark.asyncio
    async def test_generate_ad_copy(self, agent: CreativeAgent) -> None:
        """Test ad copy generation."""
        variants = await agent.generate_ad_copy(
            product_description="Premium project management software",
            target_audience="Engineering managers",
            key_benefits=["efficiency", "collaboration", "visibility"],
            num_variants=3,
        )
        assert len(variants) == 3
        for variant in variants:
            assert len(variant.headline) > 0
            assert len(variant.primary_text) > 0

    @pytest.mark.asyncio
    async def test_generate_ad_copy_invalid_count(self, agent: CreativeAgent) -> None:
        """Test that invalid variant count raises ValueError."""
        with pytest.raises(ValueError, match="Number of variants must be positive"):
            await agent.generate_ad_copy(
                product_description="Test product",
                target_audience="Test audience",
                key_benefits=["quality"],
                num_variants=0,
            )

    @pytest.mark.asyncio
    async def test_create_creative_campaign(self, agent: CreativeAgent) -> None:
        """Test creative campaign creation."""
        campaign = await agent.create_creative_campaign(
            campaign_id="camp_001",
            product_description="AI-powered analytics platform",
            target_audience="Data scientists",
            key_benefits=["speed", "accuracy", "insights"],
        )
        assert campaign.campaign_id == "camp_001"
        assert len(campaign.variants) > 0
        assert campaign.ab_test_config["confidence_level"] == 0.95


# ─── Bidding Agent Tests ────────────────────────────────────────────


class TestBiddingAgent:
    """Tests for the Bidding Agent."""

    @pytest.fixture
    def agent(self) -> BiddingAgent:
        """Create a Bidding Agent instance."""
        return BiddingAgent()

    @pytest.mark.asyncio
    async def test_optimize_bids_underperforming(self, agent: BiddingAgent) -> None:
        """Test bid optimization for underperforming campaign."""
        performance = {"roas": 0.5, "cpc": 2.0, "ctr": 0.008}
        recommendations = await agent.optimize_bids(
            campaign_id="camp_001",
            platform="meta",
            performance_data=performance,
            target_roas=3.0,
        )
        assert len(recommendations) > 0
        assert recommendations[0].recommended_bid < recommendations[0].current_bid

    @pytest.mark.asyncio
    async def test_optimize_bids_overperforming(self, agent: BiddingAgent) -> None:
        """Test bid optimization for overperforming campaign."""
        performance = {"roas": 5.0, "cpc": 1.0, "ctr": 0.03}
        recommendations = await agent.optimize_bids(
            campaign_id="camp_001",
            platform="google",
            performance_data=performance,
            target_roas=3.0,
        )
        assert len(recommendations) > 0
        assert recommendations[0].recommended_bid > recommendations[0].current_bid

    @pytest.mark.asyncio
    async def test_check_pacing_on_track(self, agent: BiddingAgent) -> None:
        """Test pacing check when spending is on track."""
        status = await agent.check_pacing(
            campaign_id="camp_001",
            daily_budget=100.0,
            spent_today=50.0,
            hours_elapsed=12,
        )
        assert status.pacing_ratio == pytest.approx(1.0, rel=0.1)
        assert status.mode.value == "standard"

    @pytest.mark.asyncio
    async def test_check_pacing_over_spending(self, agent: BiddingAgent) -> None:
        """Test pacing check when over-spending."""
        status = await agent.check_pacing(
            campaign_id="camp_001",
            daily_budget=100.0,
            spent_today=80.0,
            hours_elapsed=8,
        )
        assert status.pacing_ratio > 1.2
        assert status.mode.value == "throttle"

    @pytest.mark.asyncio
    async def test_check_pacing_invalid_budget(self, agent: BiddingAgent) -> None:
        """Test that invalid budget raises ValueError."""
        with pytest.raises(ValueError, match="Daily budget must be positive"):
            await agent.check_pacing(
                campaign_id="camp_001",
                daily_budget=0.0,
                spent_today=0.0,
                hours_elapsed=12,
            )


# ─── Audience Agent Tests ───────────────────────────────────────────


class TestAudienceAgent:
    """Tests for the Audience Agent."""

    @pytest.fixture
    def agent(self) -> AudienceAgent:
        """Create an Audience Agent instance."""
        return AudienceAgent()

    @pytest.mark.asyncio
    async def test_build_audience_plan(self, agent: AudienceAgent) -> None:
        """Test audience plan creation."""
        plan = await agent.build_audience_plan(
            campaign_id="camp_001",
            product_category="fitness",
            target_demographics={"age": "25-45", "gender": "all"},
        )
        assert plan.campaign_id == "camp_001"
        assert len(plan.segments) > 0
        assert len(plan.exclusions) > 0

    @pytest.mark.asyncio
    async def test_build_audience_plan_with_customer_data(self, agent: AudienceAgent) -> None:
        """Test audience plan with customer data for lookalikes."""
        plan = await agent.build_audience_plan(
            campaign_id="camp_001",
            product_category="e-commerce",
            target_demographics={"age": "25-54"},
            customer_data={"customer_count": 50000, "top_segment": "frequent_buyers"},
        )
        lookalike_segments = [
            s for s in plan.segments if s.audience_type.value == "lookalike"
        ]
        assert len(lookalike_segments) > 0

    @pytest.mark.asyncio
    async def test_optimize_targeting(self, agent: AudienceAgent) -> None:
        """Test targeting optimization."""
        performance = {
            "seg_001": {"roas": 4.0, "cpa": 20.0},
            "seg_002": {"roas": 0.5, "cpa": 100.0},
            "seg_003": {"roas": 1.2, "cpa": 50.0},
        }
        optimizations = await agent.optimize_targeting(
            campaign_id="camp_001",
            performance_by_segment=performance,
        )
        assert "seg_001" in optimizations["increase_budget"]
        assert "seg_002" in optimizations["pause"]


# ─── Critic Agent Tests ─────────────────────────────────────────────


class TestCriticAgent:
    """Tests for the Critic Agent."""

    @pytest.fixture
    def agent(self) -> CriticAgent:
        """Create a Critic Agent instance."""
        return CriticAgent()

    @pytest.mark.asyncio
    async def test_evaluate_performance_excellent(self, agent: CriticAgent) -> None:
        """Test performance evaluation for excellent campaign."""
        metrics = {"roas": 4.5, "ctr": 0.03, "cpa": 20.0}
        targets = {"roas": 3.0, "ctr": 0.015, "cpa": 50.0}
        evaluation = await agent.evaluate_performance(
            campaign_id="camp_001",
            metrics=metrics,
            targets=targets,
        )
        assert evaluation.grade.value in ["excellent", "good"]
        assert evaluation.overall_score > 75.0

    @pytest.mark.asyncio
    async def test_evaluate_performance_poor(self, agent: CriticAgent) -> None:
        """Test performance evaluation for poor campaign."""
        metrics = {"roas": 0.3, "ctr": 0.003, "cpa": 200.0}
        targets = {"roas": 3.0, "ctr": 0.015, "cpa": 50.0}
        evaluation = await agent.evaluate_performance(
            campaign_id="camp_001",
            metrics=metrics,
            targets=targets,
        )
        assert evaluation.grade.value in ["poor", "critical"]
        assert len(evaluation.recommendations) > 0

    @pytest.mark.asyncio
    async def test_review_action_approved(self, agent: CriticAgent) -> None:
        """Test governance review for compliant action."""
        decision = await agent.review_action(
            action="Increase daily budget",
            proposed_changes={"budget_change_pct": 10, "budget_amount": 500},
        )
        assert decision.status.value == "approved"

    @pytest.mark.asyncio
    async def test_review_action_requires_review(self, agent: CriticAgent) -> None:
        """Test governance review for non-compliant action."""
        decision = await agent.review_action(
            action="Large budget increase",
            proposed_changes={"budget_change_pct": 50, "budget_amount": 5000},
        )
        assert decision.status.value == "requires_review"
        assert len(decision.required_changes) > 0
