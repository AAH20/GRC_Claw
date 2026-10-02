"""Tests for Customer Segmentation agents."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from customer_segmentation.agents.analyst import AnalystAgent
from customer_segmentation.agents.data_collector import DataCollectorAgent
from customer_segmentation.agents.segment_builder import SegmentBuilderAgent
from customer_segmentation.config import Settings, get_settings
from customer_segmentation.models import (
    Customer,
    RFMProfile,
    Segment,
    SegmentStatus,
    SegmentType,
)


@pytest.fixture
def sample_customers() -> list[Customer]:
    base = datetime(2024, 1, 1)
    return [
        Customer(
            id="c1",
            email="c1@example.com",
            first_name="Alice",
            last_name="Smith",
            created_at=base,
            total_revenue=500.0,
            total_orders=5,
            last_order_date=base + timedelta(days=30),
        ),
        Customer(
            id="c2",
            email="c2@example.com",
            first_name="Bob",
            last_name="Jones",
            created_at=base,
            total_revenue=1500.0,
            total_orders=15,
            last_order_date=base + timedelta(days=10),
        ),
        Customer(
            id="c3",
            email="c3@example.com",
            first_name="Charlie",
            last_name="Brown",
            created_at=base,
            total_revenue=50.0,
            total_orders=1,
            last_order_date=base + timedelta(days=90),
        ),
    ]


class TestAnalystAgent:
    """Tests for AnalystAgent."""

    @pytest.fixture
    def agent(self) -> AnalystAgent:
        return AnalystAgent()

    def test_calculate_rfm_scores(self, agent: AnalystAgent, sample_customers: list[Customer]) -> None:
        rfm = agent.calculate_rfm_scores(sample_customers)
        assert isinstance(rfm, list)
        assert len(rfm) == len(sample_customers)
        assert all(isinstance(r, RFMProfile) for r in rfm)

    def test_perform_clustering(self, agent: AnalystAgent, sample_customers: list[Customer]) -> None:
        result = agent.perform_clustering(sample_customers)
        assert result is not None

    def test_detect_trends(self, agent: AnalystAgent, sample_customers: list[Customer]) -> None:
        trends = agent.detect_trends(sample_customers)
        assert isinstance(trends, dict)

    def test_detect_outliers(self, agent: AnalystAgent, sample_customers: list[Customer]) -> None:
        outliers = agent.detect_outliers(sample_customers)
        assert isinstance(outliers, list)


class TestSegmentBuilderAgent:
    """Tests for SegmentBuilderAgent."""

    @pytest.fixture
    def agent(self) -> SegmentBuilderAgent:
        return SegmentBuilderAgent()

    @pytest.mark.asyncio
    async def test_execute(self, agent: SegmentBuilderAgent, sample_customers: list[Customer]) -> None:
        result = await agent.execute(sample_customers)
        assert result is not None


class TestDataCollectorAgent:
    """Tests for DataCollectorAgent."""

    @pytest.fixture
    def agent(self) -> DataCollectorAgent:
        return DataCollectorAgent()

    def test_init(self, agent: DataCollectorAgent) -> None:
        assert agent is not None

    @pytest.mark.asyncio
    async def test_collect_all(self, agent: DataCollectorAgent) -> None:
        result = await agent.collect_all()
        assert result is not None


class TestSettings:
    """Tests for application settings."""

    def test_get_settings(self) -> None:
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_settings_defaults(self) -> None:
        settings = get_settings()
        assert settings.app_name is not None


class TestModels:
    """Tests for data models."""

    def test_customer_creation(self) -> None:
        customer = Customer(
            id="c1",
            email="test@example.com",
            first_name="Test",
            last_name="User",
        )
        assert customer.id == "c1"
        assert customer.total_revenue == 0.0

    def test_segment_creation(self) -> None:
        segment = Segment(
            id="seg1",
            name="Test Segment",
            segment_type=SegmentType.RFM,
        )
        assert segment.id == "seg1"
        assert segment.status == SegmentStatus.DRAFT
