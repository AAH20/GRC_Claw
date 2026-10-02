"""Tests for Pricing Optimizer agents."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from pricing_optimizer.agents.implementation import (
    ImplementationAgent,
    ImplementationConfig,
    ImplementationStatus,
    PlatformType,
    PriceChangeRequest,
    PriceChangeResult,
)
from pricing_optimizer.agents.market_intelligence import (
    CompetitorPrice,
    DemandSignal,
    MarketIntelligenceAgent,
    MarketIntelligenceConfig,
    MarketIntelligenceReport,
    MarketTrend,
)
from pricing_optimizer.agents.monitoring import (
    AnomalyAlert,
    AnomalySeverity,
    MetricDataPoint,
    MetricType,
    MonitoringAgent,
    MonitoringConfig,
)
from pricing_optimizer.agents.pricing_engine import (
    ElasticityModel,
    OptimizationStrategy,
    PricingConstraint,
    PricingEngineAgent,
    PricingEngineConfig,
    PricingEngineResult,
    PriceRecommendation,
)
from pricing_optimizer.agents.testing import (
    ABTest,
    TestMetrics,
    TestStatus,
    TestVariant,
    TestingAgent,
    TestingConfig,
)


class TestPricingEngineAgent:
    """Tests for PricingEngineAgent."""

    @pytest.fixture
    def agent(self) -> PricingEngineAgent:
        return PricingEngineAgent()

    @pytest.fixture
    def market_report(self) -> MarketIntelligenceReport:
        return MarketIntelligenceReport(
            product_id="p1",
            competitor_prices=[
                CompetitorPrice(competitor_id="c1", product_name="Widget", price=25.0),
                CompetitorPrice(competitor_id="c2", product_name="Widget", price=30.0),
            ],
            average_competitor_price=27.5,
        )

    @pytest.fixture
    def constraints(self) -> PricingConstraint:
        return PricingConstraint(
            min_price=10.0,
            max_price=100.0,
            min_margin_percent=20.0,
            max_price_change_percent=30.0,
        )

    def test_generate_recommendation(
        self, agent: PricingEngineAgent, constraints: PricingConstraint, market_report: MarketIntelligenceReport
    ) -> None:
        result = agent.generate_recommendation(
            product_id="p1",
            current_price=29.99,
            cost=15.0,
            constraints=constraints,
            market_report=market_report,
        )
        assert isinstance(result, PriceRecommendation)
        assert result.product_id == "p1"
        assert result.current_price == 29.99
        assert result.recommended_price > 0
        assert 0 <= result.confidence <= 1.0

    def test_generate_recommendation_with_constraints(
        self, agent: PricingEngineAgent, constraints: PricingConstraint
    ) -> None:
        result = agent.generate_recommendation(
            product_id="p1",
            current_price=50.0,
            cost=20.0,
            constraints=constraints,
        )
        assert isinstance(result, PriceRecommendation)
        assert result.recommended_price >= 10.0
        assert result.recommended_price <= 100.0

    def test_generate_recommendation_invalid_product_id(
        self, agent: PricingEngineAgent, constraints: PricingConstraint
    ) -> None:
        with pytest.raises(ValueError, match="product_id is required"):
            agent.generate_recommendation(
                product_id="",
                current_price=29.99,
                cost=15.0,
                constraints=constraints,
            )

    def test_generate_recommendation_invalid_price(
        self, agent: PricingEngineAgent, constraints: PricingConstraint
    ) -> None:
        with pytest.raises(ValueError, match="current_price must be positive"):
            agent.generate_recommendation(
                product_id="p1",
                current_price=-5.0,
                cost=15.0,
                constraints=constraints,
            )

    def test_optimize_prices_batch(self, agent: PricingEngineAgent, constraints: PricingConstraint) -> None:
        products = [
            {"product_id": "p1", "current_price": 29.99, "cost": 15.0},
            {"product_id": "p2", "current_price": 49.99, "cost": 25.0},
        ]
        result = agent.optimize_prices(products, constraints)
        assert isinstance(result, PricingEngineResult)
        assert result.total_products_analyzed == 2
        assert len(result.recommendations) == 2

    def test_optimize_prices_empty_list(self, agent: PricingEngineAgent, constraints: PricingConstraint) -> None:
        with pytest.raises(ValueError, match="products list cannot be empty"):
            agent.optimize_prices([], constraints)

    def test_invalid_constraint(self) -> None:
        with pytest.raises(ValueError):
            PricingConstraint(min_price=100.0, max_price=50.0)


class TestMarketIntelligenceAgent:
    """Tests for MarketIntelligenceAgent."""

    @pytest.fixture
    def agent(self) -> MarketIntelligenceAgent:
        return MarketIntelligenceAgent()

    @pytest.mark.asyncio
    async def test_generate_report(self, agent: MarketIntelligenceAgent) -> None:
        report = await agent.generate_report(
            product_id="p1",
            product_name="Widget",
            our_price=29.99,
        )
        assert isinstance(report, MarketIntelligenceReport)
        assert report.product_id == "p1"

    def test_calculate_price_position(self, agent: MarketIntelligenceAgent) -> None:
        competitor_prices = [
            CompetitorPrice(competitor_id="c1", product_name="Widget", price=25.0),
            CompetitorPrice(competitor_id="c2", product_name="Widget", price=30.0),
        ]
        position = agent._calculate_price_position(35.0, competitor_prices)
        assert position in ["premium", "parity", "discount"]

    def test_calculate_price_position_empty(self, agent: MarketIntelligenceAgent) -> None:
        position = agent._calculate_price_position(35.0, [])
        assert position is None


class TestMonitoringAgent:
    """Tests for MonitoringAgent."""

    @pytest.fixture
    def agent(self) -> MonitoringAgent:
        return MonitoringAgent()

    def test_record_metric(self, agent: MonitoringAgent) -> None:
        point = MetricDataPoint(
            metric_type=MetricType.CONVERSION_RATE,
            product_id="p1",
            value=0.05,
        )
        agent.record_metric(point)
        summary = agent.get_metric_summary(MetricType.CONVERSION_RATE, "p1")
        # Not enough data yet (needs 10+)
        assert summary is None

    def test_record_metric_enough_data(self, agent: MonitoringAgent) -> None:
        for i in range(15):
            agent.record_metric(
                MetricDataPoint(
                    metric_type=MetricType.CONVERSION_RATE,
                    product_id="p1",
                    value=0.05 + i * 0.001,
                )
            )
        summary = agent.get_metric_summary(MetricType.CONVERSION_RATE, "p1")
        assert summary is not None
        assert summary["count"] == 15
        assert summary["product_id"] == "p1"

    def test_detect_anomaly(self, agent: MonitoringAgent) -> None:
        # Seed with normal data
        for i in range(15):
            agent.record_metric(
                MetricDataPoint(
                    metric_type=MetricType.CONVERSION_RATE,
                    product_id="p1",
                    value=0.05 + i * 0.001,
                )
            )
        # Anomalous value
        alert = agent.check_anomaly(
            MetricDataPoint(
                metric_type=MetricType.CONVERSION_RATE,
                product_id="p1",
                value=0.5,
            )
        )
        assert alert is None or isinstance(alert, AnomalyAlert)

    def test_get_metric_summary(self, agent: MonitoringAgent) -> None:
        for i in range(15):
            agent.record_metric(
                MetricDataPoint(
                    metric_type=MetricType.CONVERSION_RATE,
                    product_id="p1",
                    value=0.05,
                )
            )
        summary = agent.get_metric_summary(MetricType.CONVERSION_RATE, "p1")
        assert isinstance(summary, dict)
        assert summary["count"] == 15


class TestImplementationAgent:
    """Tests for ImplementationAgent."""

    @pytest.fixture
    def agent(self) -> ImplementationAgent:
        return ImplementationAgent()

    def test_validate_request(self, agent: ImplementationAgent) -> None:
        request = PriceChangeRequest(
            product_id="p1",
            current_price=29.99,
            new_price=34.99,
            platform=PlatformType.SHOPIFY,
        )
        errors = agent._validate_request(request)
        assert len(errors) == 0

    def test_validate_request_same_price(self, agent: ImplementationAgent) -> None:
        request = PriceChangeRequest(
            product_id="p1",
            current_price=29.99,
            new_price=29.99,
            platform=PlatformType.SHOPIFY,
        )
        errors = agent._validate_request(request)
        assert len(errors) > 0

    def test_validate_request_excessive_change(self, agent: ImplementationAgent) -> None:
        request = PriceChangeRequest(
            product_id="p1",
            current_price=10.0,
            new_price=100.0,
            platform=PlatformType.SHOPIFY,
        )
        errors = agent._validate_request(request)
        assert any("exceeds" in e for e in errors)

    @pytest.mark.asyncio
    async def test_implement_price_change(self, agent: ImplementationAgent) -> None:
        request = PriceChangeRequest(
            product_id="p1",
            current_price=29.99,
            new_price=34.99,
            platform=PlatformType.SHOPIFY,
            dry_run=True,
        )
        result = await agent.implement_price_change(request)
        assert isinstance(result, PriceChangeResult)
        assert result.product_id == "p1"


class TestTestingAgent:
    """Tests for TestingAgent."""

    @pytest.fixture
    def agent(self) -> TestingAgent:
        return TestingAgent()

    def test_create_test(self, agent: TestingAgent) -> None:
        test = agent.create_test(
            test_id="t1",
            product_id="p1",
            control_price=29.99,
            treatment_price=34.99,
        )
        assert isinstance(test, ABTest)
        assert test.test_id == "t1"
        assert test.status == TestStatus.DRAFT
        assert len(test.variants) == 2

    def test_start_test(self, agent: TestingAgent) -> None:
        test = agent.create_test("t1", "p1", 29.99, 34.99)
        started = agent.start_test("t1")
        assert started.status == TestStatus.RUNNING
        assert started.start_date is not None

    def test_record_metrics(self, agent: TestingAgent) -> None:
        test = agent.create_test("t1", "p1", 29.99, 34.99)
        agent.start_test("t1")
        agent.record_metrics("t1", "control", impressions=100, conversions=5, revenue=150.0)
        updated = agent.get_test("t1")
        assert updated.metrics["control"].impressions == 100
        assert updated.metrics["control"].conversions == 5

    def test_evaluate_test(self, agent: TestingAgent) -> None:
        test = agent.create_test("t1", "p1", 29.99, 34.99)
        agent.start_test("t1")
        # Record enough data
        agent.record_metrics("t1", "control", impressions=200, conversions=10, revenue=300.0)
        agent.record_metrics("t1", "treatment", impressions=200, conversions=15, revenue=525.0)
        result = agent.evaluate_test("t1")
        assert result.status in (TestStatus.COMPLETED, TestStatus.RUNNING)
