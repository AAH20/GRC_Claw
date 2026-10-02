"""Tests for Customer Segmentation agents."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from customer_segmentation.agents.analyst import AnalystAgent, RFMProfile
from customer_segmentation.agents.data_collector import DataCollectorAgent
from customer_segmentation.agents.segment_builder import SegmentBuilderAgent
from customer_segmentation.config import Settings, get_settings
from customer_segmentation.models import (
    Customer,
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
            total_spent=500.0,
            order_count=5,
            last_order_at=base + timedelta(days=30),
        ),
        Customer(
            id="c2",
            email="c2@example.com",
            first_name="Bob",
            last_name="Jones",
            created_at=base,
            total_spent=1500.0,
            order_count=15,
            last_order_at=base + timedelta(days=10),
        ),
        Customer(
            id="c3",
            email="c3@example.com",
            first_name="Charlie",
            last_name="Brown",
            created_at=base,
            total_spent=50.0,
            order_count=1,
            last_order_at=base + timedelta(days=90),
        ),
    ]


class TestAnalystAgent:
    """Tests for AnalystAgent."""

    @pytest.fixture
    def agent(self) -> AnalystAgent:
        return AnalystAgent()

    def test_calculate_rfm(self, agent: AnalystAgent, sample_customers: list[Customer]) -> None:
        rfm = agent.calculate_rfm(sample_customers)
        assert isinstance(rfm, list)
        assert len(rfm) == len(sample_customers)
        assert all(isinstance(r, RFMProfile) for r in rfm)

    def test_segment_customers(self, agent: AnalystAgent, sample_customers: list[Customer]) -> None:
        segments = agent.segment_customers(sample_customers)
        assert isinstance(segments, list)

    def test_identify_at_risk(self, agent: AnalystAgent, sample_customers: list[Customer]) -> None:
        at_risk = agent.identify_at_risk(sample_customers)
        assert isinstance(at_risk, list)


class TestSegmentBuilderAgent:
    """Tests for SegmentBuilderAgent."""

    @pytest.fixture
    def agent(self) -> SegmentBuilderAgent:
        return SegmentBuilderAgent()

    def test_create_segment(self, agent: SegmentBuilderAgent) -> None:
        segment = agent.create_segment(
            name="VIP Customers",
            segment_type=SegmentType.RFM,
            criteria={"min_spent": 1000},
        )
        assert isinstance(segment, Segment)
        assert segment.name == "VIP Customers"
        assert segment.status == SegmentStatus.ACTIVE

    def test_assign_customers(self, agent: SegmentBuilderAgent, sample_customers: list[Customer]) -> None:
        segment = agent.create_segment(
            name="Test Segment",
            segment_type=SegmentType.BEHAVIORAL,
            criteria={},
        )
        assigned = agent.assign_customers(segment.id, sample_customers)
        assert isinstance(assigned, int)
        assert assigned >= 0

    def test_get_segment_size(self, agent: SegmentBuilderAgent) -> None:
        segment = agent.create_segment(
            name="Empty Segment",
            segment_type=SegmentType.CUSTOM,
            criteria={},
        )
        size = agent.get_segment_size(segment.id)
        assert isinstance(size, int)


class TestDataCollectorAgent:
    """Tests for DataCollectorAgent."""

    @pytest.fixture
    def agent(self) -> DataCollectorAgent:
        return DataCollectorAgent()

    def test_init(self, agent: DataCollectorAgent) -> None:
        assert agent is not None

    @pytest.mark.asyncio
    async def test_collect_customers(self, agent: DataCollectorAgent) -> None:
        customers = await agent.collect_customers()
        assert isinstance(customers, list)


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
        assert customer.total_spent == 0.0

    def test_segment_creation(self) -> None:
        segment = Segment(
            id="seg1",
            name="Test Segment",
            segment_type=SegmentType.RFM,
        )
        assert segment.id == "seg1"
        assert segment.status == SegmentStatus.ACTIVE
