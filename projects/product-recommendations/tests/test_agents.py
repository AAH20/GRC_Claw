"""Tests for Product Recommendations agents."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from product_recommendations.agents.analysis import (
    AnalysisAgent,
    AnalysisResult,
    CustomerSegment,
    PurchasePattern,
    Trend,
)
from product_recommendations.agents.cross_sell import (
    CrossSellAgent,
    CrossSellResult,
    CrossSellSuggestion,
)
from product_recommendations.agents.data_collection import (
    CustomerBehavior,
    DataCollectionAgent,
    Order,
    Platform,
    Product,
)
from product_recommendations.agents.recommendation import (
    RecommendationAgent,
    RecommendationResult,
    ScoredProduct,
)


@pytest.fixture
def sample_products() -> list[Product]:
    return [
        Product(
            id="p1",
            title="Widget A",
            price=29.99,
            category="widgets",
            tags=["popular", "sale"],
            inventory_quantity=100,
            platform=Platform.SHOPIFY,
        ),
        Product(
            id="p2",
            title="Widget B",
            price=49.99,
            category="widgets",
            tags=["premium"],
            inventory_quantity=50,
            platform=Platform.SHOPIFY,
        ),
        Product(
            id="p3",
            title="Gadget X",
            price=99.99,
            category="gadgets",
            tags=["new"],
            inventory_quantity=200,
            platform=Platform.SHOPIFY,
        ),
    ]


@pytest.fixture
def sample_behaviors() -> list[CustomerBehavior]:
    base = datetime(2024, 1, 15)
    return [
        CustomerBehavior(
            customer_id="c1",
            event_type="view",
            product_id="p1",
            timestamp=base,
        ),
        CustomerBehavior(
            customer_id="c1",
            event_type="add_to_cart",
            product_id="p1",
            timestamp=base + timedelta(hours=1),
        ),
        CustomerBehavior(
            customer_id="c1",
            event_type="view",
            product_id="p2",
            timestamp=base + timedelta(hours=2),
        ),
    ]


@pytest.fixture
def sample_orders() -> list[Order]:
    return [
        Order(
            id="o1",
            customer_id="c1",
            items=[{"product_id": "p1", "quantity": 1, "price": 29.99}],
            total=29.99,
            status="completed",
        ),
        Order(
            id="o2",
            customer_id="c2",
            items=[{"product_id": "p2", "quantity": 1, "price": 49.99}],
            total=49.99,
            status="completed",
        ),
    ]


class TestAnalysisAgent:
    """Tests for AnalysisAgent."""

    @pytest.fixture
    def agent(self) -> AnalysisAgent:
        return AnalysisAgent()

    def test_analyze(
        self,
        agent: AnalysisAgent,
        sample_products: list[Product],
        sample_behaviors: list[CustomerBehavior],
        sample_orders: list[Order],
    ) -> None:
        result = agent.analyze(sample_products, sample_behaviors, sample_orders)
        assert isinstance(result, AnalysisResult)
        assert result.analyzed_at is not None

    def test_detect_trends(
        self,
        agent: AnalysisAgent,
        sample_products: list[Product],
        sample_behaviors: list[CustomerBehavior],
    ) -> None:
        trends = agent.detect_trends(sample_products, sample_behaviors)
        assert isinstance(trends, list)

    def test_analyze_empty_data(self, agent: AnalysisAgent) -> None:
        result = agent.analyze([], [], [])
        assert isinstance(result, AnalysisResult)
        assert len(result.segments) == 0


class TestCrossSellAgent:
    """Tests for CrossSellAgent."""

    @pytest.fixture
    def agent(self) -> CrossSellAgent:
        return CrossSellAgent()

    def test_find_cross_sell(
        self,
        agent: CrossSellAgent,
        sample_products: list[Product],
        sample_orders: list[Order],
    ) -> None:
        result = agent.find_cross_sell("p1", sample_products, sample_orders)
        assert isinstance(result, CrossSellResult)

    def test_find_cross_sell_invalid_product(
        self,
        agent: CrossSellAgent,
        sample_products: list[Product],
        sample_orders: list[Order],
    ) -> None:
        result = agent.find_cross_sell("nonexistent", sample_products, sample_orders)
        assert isinstance(result, CrossSellResult)
        assert "error" in result.context


class TestRecommendationAgent:
    """Tests for RecommendationAgent."""

    @pytest.fixture
    def agent(self) -> RecommendationAgent:
        return RecommendationAgent()

    def test_recommend(
        self,
        agent: RecommendationAgent,
        sample_products: list[Product],
        sample_behaviors: list[CustomerBehavior],
        sample_orders: list[Order],
    ) -> None:
        result = agent.recommend(
            "c1",
            sample_products,
            sample_behaviors,
            sample_orders,
        )
        assert isinstance(result, RecommendationResult)
        assert result.customer_id == "c1"
        assert isinstance(result.recommendations, list)

    def test_recommend_with_context(
        self,
        agent: RecommendationAgent,
        sample_products: list[Product],
        sample_behaviors: list[CustomerBehavior],
        sample_orders: list[Order],
    ) -> None:
        result = agent.recommend(
            "c1",
            sample_products,
            sample_behaviors,
            sample_orders,
            context={"device": "mobile"},
        )
        assert isinstance(result, RecommendationResult)


class TestDataCollectionAgent:
    """Tests for DataCollectionAgent."""

    @pytest.fixture
    def agent(self) -> DataCollectionAgent:
        return DataCollectionAgent()

    def test_init(self, agent: DataCollectionAgent) -> None:
        assert agent is not None

    @pytest.mark.asyncio
    async def test_collect_from_platform(self, agent: DataCollectionAgent) -> None:
        result = await agent.collect_from_platform(Platform.SHOPIFY)
        assert hasattr(result, "products")
        assert hasattr(result, "behaviors")
        assert hasattr(result, "orders")
