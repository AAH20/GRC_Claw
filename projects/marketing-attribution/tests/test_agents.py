"""Tests for attribution agent implementations."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from attribution.agents.attribution_engine import (
    AttributionEngine,
    AttributionModel,
    AttributionResult,
    CampaignAttribution,
    CustomerJourney,
    Touchpoint,
)
from attribution.agents.data_collection import (
    CollectionResult,
    DataCollectionAgent,
    DataSource,
    RawDataPoint,
)


class TestAttributionEngine:
    """Tests for AttributionEngine."""

    @pytest.fixture
    def engine(self) -> AttributionEngine:
        return AttributionEngine()

    @pytest.fixture
    def sample_journey(self) -> CustomerJourney:
        now = datetime.now(tz=timezone.utc)
        return CustomerJourney(
            journey_id="journey_1",
            touchpoints=[
                Touchpoint(
                    timestamp=now - timedelta(days=5),
                    source="google_ads",
                    campaign_id="camp_1",
                    campaign_name="Test Campaign",
                    interaction_type="impression",
                ),
                Touchpoint(
                    timestamp=now - timedelta(days=2),
                    source="email",
                    campaign_id="camp_2",
                    campaign_name="Email Campaign",
                    interaction_type="click",
                ),
                Touchpoint(
                    timestamp=now,
                    source="direct",
                    campaign_id="camp_3",
                    campaign_name="Direct",
                    interaction_type="click",
                ),
            ],
            conversion_value=1000.0,
            converted=True,
        )

    def test_first_touch(self, engine: AttributionEngine, sample_journey: CustomerJourney) -> None:
        result = engine.calculate_attribution(
            [sample_journey], AttributionModel.FIRST_TOUCH
        )
        assert len(result) == 1
        assert result[0].credited_touchpoints == {"0": 1.0}

    def test_last_touch(self, engine: AttributionEngine, sample_journey: CustomerJourney) -> None:
        result = engine.calculate_attribution(
            [sample_journey], AttributionModel.LAST_TOUCH
        )
        assert len(result) == 1
        assert result[0].credited_touchpoints == {"2": 1.0}

    def test_linear(self, engine: AttributionEngine, sample_journey: CustomerJourney) -> None:
        result = engine.calculate_attribution(
            [sample_journey], AttributionModel.LINEAR
        )
        assert len(result) == 1
        assert len(result[0].credited_touchpoints) == 3
        assert all(abs(v - 1 / 3) < 0.01 for v in result[0].credited_touchpoints.values())

    def test_time_decay(self, engine: AttributionEngine, sample_journey: CustomerJourney) -> None:
        result = engine.calculate_attribution(
            [sample_journey], AttributionModel.TIME_DECAY
        )
        assert len(result) == 1
        assert len(result[0].credited_touchpoints) == 3

    def test_data_driven(self, engine: AttributionEngine, sample_journey: CustomerJourney) -> None:
        result = engine.calculate_attribution(
            [sample_journey], AttributionModel.DATA_DRIVEN
        )
        assert len(result) == 1
        assert len(result[0].credited_touchpoints) == 3

    def test_unconverted_journey_skipped(
        self, engine: AttributionEngine, sample_journey: CustomerJourney
    ) -> None:
        sample_journey.converted = False
        result = engine.calculate_attribution(
            [sample_journey], AttributionModel.LAST_TOUCH
        )
        assert len(result) == 0

    def test_compare_models(self, engine: AttributionEngine, sample_journey: CustomerJourney) -> None:
        results = engine.compare_models([sample_journey])
        assert len(results) == len(AttributionModel)
        for model_results in results.values():
            assert len(model_results) == 1


class TestDataCollectionAgent:
    """Tests for DataCollectionAgent."""

    def test_register_collector(self) -> None:
        agent = DataCollectionAgent()
        assert len(agent.collectors) == 0

    async def test_collect_all_empty(self) -> None:
        agent = DataCollectionAgent()
        results = await agent.collect_all(
            datetime(2024, 1, 1), datetime(2024, 1, 31)
        )
        assert len(results) == 0

    async def test_health_check_all_empty(self) -> None:
        agent = DataCollectionAgent()
        health = await agent.health_check_all()
        assert len(health) == 0
