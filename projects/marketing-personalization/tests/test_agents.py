"""Tests for personalization agent implementations."""
from __future__ import annotations

import pytest

from personalization.agents.analysis import AnalysisAgent
from personalization.agents.data_collection import DataCollectionAgent
from personalization.agents.governance import GovernanceAgent
from personalization.agents.optimization import OptimizationAgent
from personalization.agents.performance_analytics import PerformanceAnalyticsAgent
from personalization.agents.personalization import PersonalizationAgent


class TestPersonalizationAgent:
    """Tests for PersonalizationAgent."""

    @pytest.fixture
    def agent(self) -> PersonalizationAgent:
        return PersonalizationAgent()

    async def test_generate_content(self, agent: PersonalizationAgent) -> None:
        content = await agent.generate_content("cust_1", "email")
        assert content.customer_id == "cust_1"
        assert content.content_type == "email"
        assert content.body is not None

    async def test_generate_recommendations(self, agent: PersonalizationAgent) -> None:
        recs = await agent.generate_recommendations("cust_1", 5)
        assert isinstance(recs, list)

    async def test_personalize_campaign(self, agent: PersonalizationAgent) -> None:
        result = await agent.personalize_campaign("camp_1", "seg_1")
        assert result["campaign_id"] == "camp_1"
        assert result["segment_id"] == "seg_1"

    async def test_optimize_send_time(self, agent: PersonalizationAgent) -> None:
        result = await agent.optimize_send_time("cust_1")
        assert isinstance(result, str)


class TestAnalysisAgent:
    """Tests for AnalysisAgent."""

    @pytest.fixture
    def agent(self) -> AnalysisAgent:
        return AnalysisAgent()

    async def test_analyze_customer_segments(self, agent: AnalysisAgent) -> None:
        results = await agent.analyze_customer_segments([])
        assert isinstance(results, list)

    async def test_analyze_behavior(self, agent: AnalysisAgent) -> None:
        metrics = await agent.analyze_behavior("cust_1", [])
        assert metrics.customer_id == "cust_1"

    async def test_detect_trends(self, agent: AnalysisAgent) -> None:
        result = await agent.detect_trends([])
        assert isinstance(result, dict)

    async def test_generate_insights(self, agent: AnalysisAgent) -> None:
        result = await agent.generate_insights([])
        assert isinstance(result, list)


class TestOptimizationAgent:
    """Tests for OptimizationAgent."""

    @pytest.fixture
    def agent(self) -> OptimizationAgent:
        return OptimizationAgent()

    async def test_create_ab_test(self, agent: OptimizationAgent) -> None:
        variants = [{"name": "A"}, {"name": "B"}]
        result = await agent.create_ab_test("camp_1", variants)
        assert result.campaign_id == "camp_1"
        assert len(result.variants) == 2

    async def test_analyze_ab_test(self, agent: OptimizationAgent) -> None:
        result = await agent.analyze_ab_test("test_1", {})
        assert result.campaign_id == "test_1"

    async def test_optimize_budget(self, agent: OptimizationAgent) -> None:
        result = await agent.optimize_budget("camp_1", 10000.0, {"email": 0.5})
        assert result.campaign_id == "camp_1"
        assert result.total_budget == 10000.0

    async def test_optimize_campaign(self, agent: OptimizationAgent) -> None:
        result = await agent.optimize_campaign("camp_1", {})
        assert result.campaign_id == "camp_1"


class TestGovernanceAgent:
    """Tests for GovernanceAgent."""

    @pytest.fixture
    def agent(self) -> GovernanceAgent:
        return GovernanceAgent()

    async def test_check_compliance(self, agent: GovernanceAgent) -> None:
        result = await agent.check_compliance("camp_1", {})
        assert result.campaign_id == "camp_1"
        assert result.passed is True

    async def test_validate_data_privacy(self, agent: GovernanceAgent) -> None:
        result = await agent.validate_data_privacy({})
        assert result is True

    async def test_create_approval_request(self, agent: GovernanceAgent) -> None:
        result = await agent.create_approval_request("camp_1", "user_1", ["approver_1"])
        assert result.campaign_id == "camp_1"
        assert result.status == "pending"

    async def test_enforce_retention_policy(self, agent: GovernanceAgent) -> None:
        result = await agent.enforce_retention_policy("customer_data", 30)
        assert result["data_type"] == "customer_data"


class TestDataCollectionAgent:
    """Tests for DataCollectionAgent."""

    @pytest.fixture
    def agent(self) -> DataCollectionAgent:
        return DataCollectionAgent()

    async def test_collect_customer_data(self, agent: DataCollectionAgent) -> None:
        result = await agent.collect_customer_data()
        assert isinstance(result, list)

    async def test_collect_campaign_data(self, agent: DataCollectionAgent) -> None:
        result = await agent.collect_campaign_data()
        assert isinstance(result, list)


class TestPerformanceAnalyticsAgent:
    """Tests for PerformanceAnalyticsAgent."""

    @pytest.fixture
    def agent(self) -> PerformanceAnalyticsAgent:
        return PerformanceAnalyticsAgent()

    async def test_calculate_campaign_metrics(self, agent: PerformanceAnalyticsAgent) -> None:
        result = await agent.calculate_campaign_metrics("camp_1", {})
        assert result.campaign_id == "camp_1"

    async def test_generate_report(self, agent: PerformanceAnalyticsAgent) -> None:
        result = await agent.generate_report("weekly", "2024-01-01", "2024-01-07")
        assert result.report_type == "weekly"

    async def test_calculate_roi(self, agent: PerformanceAnalyticsAgent) -> None:
        roi = await agent.calculate_roi("camp_1", 1000.0, 500.0)
        assert roi == 100.0

    async def test_calculate_roi_zero_cost(self, agent: PerformanceAnalyticsAgent) -> None:
        roi = await agent.calculate_roi("camp_1", 1000.0, 0.0)
        assert roi == 0.0
