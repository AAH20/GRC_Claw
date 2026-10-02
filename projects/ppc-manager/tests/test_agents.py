"""Tests for PPC Manager AI agents."""

from __future__ import annotations

import pytest

from ppc_manager.agents.ad_creative import AdCreativeAgent
from ppc_manager.agents.bid_management import BidManagementAgent
from ppc_manager.agents.budget_allocation import BudgetAllocationAgent
from ppc_manager.agents.keyword_research import KeywordResearchAgent
from ppc_manager.agents.landing_page_optimization import LandingPageOptimizationAgent
from ppc_manager.agents.performance_analytics import PerformanceAnalyticsAgent


class TestKeywordResearchAgent:
    """Tests for the KeywordResearchAgent."""

    @pytest.fixture
    def agent(self) -> KeywordResearchAgent:
        """Create a KeywordResearchAgent instance."""
        return KeywordResearchAgent()

    @pytest.mark.asyncio
    async def test_research_returns_result(self, agent: KeywordResearchAgent) -> None:
        """Test that research returns a result with suggestions."""
        result = await agent.research("ppc software")
        assert result.seed_keyword == "ppc software"
        assert result.total_suggestions > 0
        assert len(result.suggestions) > 0

    @pytest.mark.asyncio
    async def test_research_empty_seed_raises(self, agent: KeywordResearchAgent) -> None:
        """Test that empty seed keyword raises ValueError."""
        with pytest.raises(ValueError, match="Seed keyword cannot be empty"):
            await agent.research("")

    @pytest.mark.asyncio
    async def test_research_whitespace_seed_raises(self, agent: KeywordResearchAgent) -> None:
        """Test that whitespace-only seed keyword raises ValueError."""
        with pytest.raises(ValueError, match="Seed keyword cannot be empty"):
            await agent.research("   ")

    @pytest.mark.asyncio
    async def test_research_suggestions_have_required_fields(self, agent: KeywordResearchAgent) -> None:
        """Test that suggestions have all required fields."""
        result = await agent.research("marketing automation")
        for suggestion in result.suggestions:
            assert suggestion.keyword
            assert suggestion.search_volume >= 0
            assert suggestion.competition in ("low", "medium", "high")
            assert suggestion.cpc_estimate >= 0
            assert 0 <= suggestion.relevance_score <= 1


class TestBidManagementAgent:
    """Tests for the BidManagementAgent."""

    @pytest.fixture
    def agent(self) -> BidManagementAgent:
        """Create a BidManagementAgent instance."""
        return BidManagementAgent()

    @pytest.mark.asyncio
    async def test_optimize_bids_returns_recommendations(self, agent: BidManagementAgent) -> None:
        """Test that bid optimization returns recommendations."""
        result = await agent.optimize_bids(["campaign_1", "campaign_2"])
        assert result.total_recommendations > 0
        assert len(result.recommendations) > 0

    @pytest.mark.asyncio
    async def test_optimize_bids_empty_campaigns_raises(self, agent: BidManagementAgent) -> None:
        """Test that empty campaign list raises ValueError."""
        with pytest.raises(ValueError, match="At least one campaign ID is required"):
            await agent.optimize_bids([])

    @pytest.mark.asyncio
    async def test_optimize_bids_with_performance_data(self, agent: BidManagementAgent) -> None:
        """Test bid optimization with performance data."""
        performance_data = {
            "campaign_1": {
                "current_bid": 2.0,
                "ctr": 0.03,
                "conversion_rate": 0.05,
                "cpa": 30.0,
                "target_cpa": 40.0,
            }
        }
        result = await agent.optimize_bids(["campaign_1"], performance_data)
        assert result.total_recommendations == 1
        rec = result.recommendations[0]
        assert rec.campaign_id == "campaign_1"
        assert rec.current_bid == 2.0
        assert rec.recommended_bid > 0


class TestAdCreativeAgent:
    """Tests for the AdCreativeAgent."""

    @pytest.fixture
    def agent(self) -> AdCreativeAgent:
        """Create an AdCreativeAgent instance."""
        return AdCreativeAgent()

    @pytest.mark.asyncio
    async def test_generate_creatives_returns_variants(self, agent: AdCreativeAgent) -> None:
        """Test that creative generation returns variants."""
        result = await agent.generate_creatives(
            campaign_id="camp_1",
            product_name="TestProduct",
            target_audience="Marketing managers",
            key_benefits=["Save time", "Increase ROI"],
            platform="google",
        )
        assert result.campaign_id == "camp_1"
        assert result.total_variants > 0
        for variant in result.variants:
            assert variant.headline
            assert variant.description
            assert variant.cta
            assert variant.platform == "google"

    @pytest.mark.asyncio
    async def test_generate_creatives_empty_product_raises(self, agent: AdCreativeAgent) -> None:
        """Test that empty product name raises ValueError."""
        with pytest.raises(ValueError, match="Product name cannot be empty"):
            await agent.generate_creatives(
                campaign_id="camp_1",
                product_name="",
                target_audience="test",
                key_benefits=["test"],
            )


class TestLandingPageOptimizationAgent:
    """Tests for the LandingPageOptimizationAgent."""

    @pytest.fixture
    def agent(self) -> LandingPageOptimizationAgent:
        """Create a LandingPageOptimizationAgent instance."""
        return LandingPageOptimizationAgent()

    @pytest.mark.asyncio
    async def test_analyze_returns_result(self, agent: LandingPageOptimizationAgent) -> None:
        """Test that analysis returns a result."""
        result = await agent.analyze(
            url="https://example.com",
            page_content="<html><body><h1>Test</h1></body></html>",
        )
        assert result.url == "https://example.com"
        assert 0 <= result.overall_score <= 100

    @pytest.mark.asyncio
    async def test_analyze_empty_url_raises(self, agent: LandingPageOptimizationAgent) -> None:
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            await agent.analyze(url="")


class TestBudgetAllocationAgent:
    """Tests for the BudgetAllocationAgent."""

    @pytest.fixture
    def agent(self) -> BudgetAllocationAgent:
        """Create a BudgetAllocationAgent instance."""
        return BudgetAllocationAgent()

    @pytest.mark.asyncio
    async def test_allocate_returns_allocations(self, agent: BudgetAllocationAgent) -> None:
        """Test that budget allocation returns allocations."""
        result = await agent.allocate(
            total_budget=1000.0,
            campaign_ids=["camp_1", "camp_2", "camp_3"],
        )
        assert result.total_budget == 1000.0
        assert len(result.allocations) == 3
        assert result.total_allocated <= 1000.0

    @pytest.mark.asyncio
    async def test_allocate_negative_budget_raises(self, agent: BudgetAllocationAgent) -> None:
        """Test that negative budget raises ValueError."""
        with pytest.raises(ValueError, match="Total budget cannot be negative"):
            await agent.allocate(total_budget=-100, campaign_ids=["camp_1"])

    @pytest.mark.asyncio
    async def test_allocate_empty_campaigns_raises(self, agent: BudgetAllocationAgent) -> None:
        """Test that empty campaign list raises ValueError."""
        with pytest.raises(ValueError, match="At least one campaign ID is required"):
            await agent.allocate(total_budget=100, campaign_ids=[])

    @pytest.mark.asyncio
    async def test_allocate_respects_total_budget(self, agent: BudgetAllocationAgent) -> None:
        """Test that total allocated does not exceed total budget."""
        result = await agent.allocate(
            total_budget=500.0,
            campaign_ids=["camp_1", "camp_2", "camp_3", "camp_4"],
        )
        assert result.total_allocated <= 500.0


class TestPerformanceAnalyticsAgent:
    """Tests for the PerformanceAnalyticsAgent."""

    @pytest.fixture
    def agent(self) -> PerformanceAnalyticsAgent:
        """Create a PerformanceAnalyticsAgent instance."""
        return PerformanceAnalyticsAgent()

    @pytest.mark.asyncio
    async def test_generate_report_returns_report(self, agent: PerformanceAnalyticsAgent) -> None:
        """Test that report generation returns a report."""
        campaign_data = {
            "camp_1": {
                "spend": 1000.0,
                "revenue": 3000.0,
                "clicks": 500,
                "impressions": 10000,
                "conversions": 20,
                "ctr": 0.05,
                "cpa": 50.0,
            },
            "camp_2": {
                "spend": 800.0,
                "revenue": 2400.0,
                "clicks": 400,
                "impressions": 8000,
                "conversions": 15,
                "ctr": 0.05,
                "cpa": 53.3,
            },
        }
        report = await agent.generate_report(
            period_start="2024-01-01",
            period_end="2024-01-31",
            campaign_data=campaign_data,
        )
        assert report.period_start == "2024-01-01"
        assert report.period_end == "2024-01-31"
        assert report.total_spend == 1800.0
        assert report.total_revenue == 5400.0
        assert report.total_clicks == 900
        assert report.total_impressions == 18000
        assert report.campaign_count == 2

    @pytest.mark.asyncio
    async def test_generate_report_empty_period_raises(self, agent: PerformanceAnalyticsAgent) -> None:
        """Test that empty period raises ValueError."""
        with pytest.raises(ValueError, match="Period start and end are required"):
            await agent.generate_report(
                period_start="",
                period_end="2024-01-31",
                campaign_data={},
            )

    @pytest.mark.asyncio
    async def test_detect_anomalies_finds_outliers(self, agent: PerformanceAnalyticsAgent) -> None:
        """Test that anomaly detection finds statistical outliers."""
        campaign_data = {
            "camp_1": {"ctr": 0.05, "cpa": 50.0, "spend": 1000.0},
            "camp_2": {"ctr": 0.04, "cpa": 52.0, "spend": 1100.0},
            "camp_3": {"ctr": 0.06, "cpa": 48.0, "spend": 900.0},
            "camp_4": {"ctr": 0.05, "cpa": 51.0, "spend": 1050.0},
            "camp_5": {"ctr": 0.50, "cpa": 500.0, "spend": 10000.0},  # outlier
        }
        report = await agent.generate_report(
            period_start="2024-01-01",
            period_end="2024-01-31",
            campaign_data=campaign_data,
        )
        assert len(report.anomalies) > 0
        outlier_found = any(a.campaign_id == "camp_5" for a in report.anomalies)
        assert outlier_found
