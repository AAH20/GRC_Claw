"""Attribution Engine Agent - Multi-touch attribution modeling."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class AttributionModel(str, Enum):
    """Supported attribution models."""

    FIRST_TOUCH = "first_touch"
    LAST_TOUCH = "last_touch"
    LINEAR = "linear"
    TIME_DECAY = "time_decay"
    DATA_DRIVEN = "data_driven"


@dataclass
class Touchpoint:
    """A single touchpoint in a customer journey."""

    timestamp: datetime
    source: str
    campaign_id: str
    campaign_name: str
    interaction_type: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CustomerJourney:
    """A complete customer journey with multiple touchpoints."""

    journey_id: str
    touchpoints: list[Touchpoint]
    conversion_value: float = 0.0
    converted: bool = False


@dataclass
class AttributionResult:
    """Result of attribution calculation for a single journey."""

    journey_id: str
    model: AttributionModel
    credited_touchpoints: dict[str, float]
    total_credit: float = 1.0


@dataclass
class CampaignAttribution:
    """Aggregated attribution results for a campaign."""

    campaign_id: str
    campaign_name: str
    source: str
    attributed_conversions: float
    attributed_revenue: float
    attributed_spend: float
    roas: float = 0.0
    model: AttributionModel = AttributionModel.LAST_TOUCH


class AttributionEngine:
    """Multi-touch attribution engine supporting multiple models."""

    def __init__(self, time_decay_half_life_days: float = 7.0) -> None:
        self.time_decay_half_life_days = time_decay_half_life_days
        self.logger = structlog.get_logger(__name__).bind(agent="attribution_engine")

    def calculate_attribution(
        self, journeys: list[CustomerJourney], model: AttributionModel
    ) -> list[AttributionResult]:
        """Calculate attribution for all journeys using the specified model."""
        results: list[AttributionResult] = []
        for journey in journeys:
            if not journey.converted or not journey.touchpoints:
                continue
            if model == AttributionModel.FIRST_TOUCH:
                result = self._first_touch(journey)
            elif model == AttributionModel.LAST_TOUCH:
                result = self._last_touch(journey)
            elif model == AttributionModel.LINEAR:
                result = self._linear(journey)
            elif model == AttributionModel.TIME_DECAY:
                result = self._time_decay(journey)
            elif model == AttributionModel.DATA_DRIVEN:
                result = self._data_driven(journey)
            else:
                raise ValueError(f"Unsupported attribution model: {model}")
            results.append(result)
        self.logger.info("Attribution complete", model=model.value, count=len(results))
        return results

    def _first_touch(self, journey: CustomerJourney) -> AttributionResult:
        """First-touch: 100% credit to the first touchpoint."""
        return AttributionResult(
            journey_id=journey.journey_id,
            model=AttributionModel.FIRST_TOUCH,
            credited_touchpoints={"0": 1.0},
        )

    def _last_touch(self, journey: CustomerJourney) -> AttributionResult:
        """Last-touch: 100% credit to the last touchpoint."""
        return AttributionResult(
            journey_id=journey.journey_id,
            model=AttributionModel.LAST_TOUCH,
            credited_touchpoints={str(len(journey.touchpoints) - 1): 1.0},
        )

    def _linear(self, journey: CustomerJourney) -> AttributionResult:
        """Linear: equal credit to all touchpoints."""
        n = len(journey.touchpoints)
        credit = 1.0 / n if n > 0 else 0.0
        return AttributionResult(
            journey_id=journey.journey_id,
            model=AttributionModel.LINEAR,
            credited_touchpoints={str(i): credit for i in range(n)},
        )

    def _time_decay(self, journey: CustomerJourney) -> AttributionResult:
        """Time-decay: more credit to touchpoints closer to conversion."""
        if not journey.touchpoints:
            return AttributionResult(
                journey_id=journey.journey_id,
                model=AttributionModel.TIME_DECAY,
                credited_touchpoints={},
            )
        conversion_time = journey.touchpoints[-1].timestamp
        half_life_secs = timedelta(days=self.time_decay_half_life_days).total_seconds()
        weights = []
        for tp in journey.touchpoints:
            diff = max(0.0, (conversion_time - tp.timestamp).total_seconds())
            weights.append(0.5 ** (diff / half_life_secs))
        total = sum(weights)
        if total == 0:
            return AttributionResult(
                journey_id=journey.journey_id,
                model=AttributionModel.TIME_DECAY,
                credited_touchpoints={},
            )
        return AttributionResult(
            journey_id=journey.journey_id,
            model=AttributionModel.TIME_DECAY,
            credited_touchpoints={str(i): w / total for i, w in enumerate(weights)},
        )

    def _data_driven(self, journey: CustomerJourney) -> AttributionResult:
        """Data-driven attribution using a Shapley-value-inspired weighting."""
        n = len(journey.touchpoints)
        if n == 0:
            return AttributionResult(
                journey_id=journey.journey_id,
                model=AttributionModel.DATA_DRIVEN,
                credited_touchpoints={},
            )
        if n == 1:
            return AttributionResult(
                journey_id=journey.journey_id,
                model=AttributionModel.DATA_DRIVEN,
                credited_touchpoints={"0": 1.0},
            )
        weights = []
        for i, tp in enumerate(journey.touchpoints):
            position_weight = (i + 1) / n
            type_weight = 2.0 if tp.interaction_type == "click" else 1.0
            weights.append(position_weight * type_weight)
        total = sum(weights)
        return AttributionResult(
            journey_id=journey.journey_id,
            model=AttributionModel.DATA_DRIVEN,
            credited_touchpoints={str(i): w / total for i, w in enumerate(weights)},
        )

    def aggregate_by_campaign(
        self,
        journeys: list[CustomerJourney],
        attribution_results: list[AttributionResult],
        spend_lookup: dict[str, float] | None = None,
    ) -> list[CampaignAttribution]:
        """Aggregate attribution results by campaign."""
        spend_lookup = spend_lookup or {}
        campaign_data: dict[str, dict[str, Any]] = {}
        for journey, result in zip(journeys, attribution_results, strict=False):
            for idx_str, credit in result.credited_touchpoints.items():
                idx = int(idx_str)
                if idx >= len(journey.touchpoints):
                    continue
                tp = journey.touchpoints[idx]
                key = f"{tp.source}:{tp.campaign_id}"
                if key not in campaign_data:
                    campaign_data[key] = {
                        "campaign_id": tp.campaign_id,
                        "campaign_name": tp.campaign_name,
                        "source": tp.source,
                        "attributed_conversions": 0.0,
                        "attributed_revenue": 0.0,
                        "attributed_spend": spend_lookup.get(key, 0.0),
                        "model": result.model,
                    }
                campaign_data[key]["attributed_conversions"] += credit
                campaign_data[key]["attributed_revenue"] += credit * journey.conversion_value
        results = []
        for d in campaign_data.values():
            roas = (
                d["attributed_revenue"] / d["attributed_spend"]
                if d["attributed_spend"] > 0
                else 0.0
            )
            results.append(
                CampaignAttribution(
                    campaign_id=d["campaign_id"],
                    campaign_name=d["campaign_name"],
                    source=d["source"],
                    attributed_conversions=d["attributed_conversions"],
                    attributed_revenue=d["attributed_revenue"],
                    attributed_spend=d["attributed_spend"],
                    roas=roas,
                    model=d["model"],
                )
            )
        return sorted(results, key=lambda x: x.attributed_revenue, reverse=True)

    def compare_models(
        self, journeys: list[CustomerJourney]
    ) -> dict[str, list[AttributionResult]]:
        """Run all attribution models and return comparison."""
        return {m.value: self.calculate_attribution(journeys, m) for m in AttributionModel}
