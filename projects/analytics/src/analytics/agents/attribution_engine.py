"""Attribution Engine Agent - Multi-touch attribution modeling."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

import numpy as np
import structlog

from analytics.agents.data_collection import RawEvent

logger = structlog.get_logger(__name__)


class AttributionModel(StrEnum):
    """Supported attribution models."""

    FIRST_TOUCH = "first_touch"
    LAST_TOUCH = "last_touch"
    LINEAR = "linear"
    TIME_DECAY = "time_decay"
    DATA_DRIVEN = "data_driven"


@dataclass
class Touchpoint:
    """Represents a single touchpoint in a customer journey."""

    event_id: str
    channel: str
    campaign_id: str | None
    timestamp: datetime
    revenue: float = 0.0


@dataclass
class CustomerJourney:
    """Represents a complete customer journey with multiple touchpoints."""

    user_id: str
    touchpoints: list[Touchpoint] = field(default_factory=list)
    conversion_value: float = 0.0
    converted: bool = False


@dataclass
class AttributionResult:
    """Result of attribution calculation for a single journey."""

    user_id: str
    model: AttributionModel
    channel_attributions: dict[str, float] = field(default_factory=dict)
    total_revenue: float = 0.0


@dataclass
class AggregatedAttribution:
    """Aggregated attribution results across all journeys."""

    model: AttributionModel
    channel_totals: dict[str, float] = field(default_factory=dict)
    channel_percentages: dict[str, float] = field(default_factory=dict)
    total_revenue: float = 0.0
    journey_count: int = 0
    converted_journeys: int = 0


class AttributionEngine:
    """Multi-touch attribution engine supporting multiple models."""

    def __init__(self, default_model: AttributionModel = AttributionModel.DATA_DRIVEN) -> None:
        self.default_model = default_model
        self.logger = logger.bind(agent="attribution_engine")

    def build_journeys(self, events: list[RawEvent]) -> list[CustomerJourney]:
        """Build customer journeys from raw events."""
        journeys: dict[str, CustomerJourney] = {}

        for event in sorted(events, key=lambda e: e.timestamp):
            if event.user_id not in journeys:
                journeys[event.user_id] = CustomerJourney(user_id=event.user_id)

            journey = journeys[event.user_id]
            touchpoint = Touchpoint(
                event_id=event.event_id,
                channel=event.channel or "direct",
                campaign_id=event.campaign_id,
                timestamp=event.timestamp,
                revenue=event.revenue,
            )
            journey.touchpoints.append(touchpoint)

            if event.revenue > 0:
                journey.conversion_value += event.revenue
                journey.converted = True

        return list(journeys.values())

    def run_attribution(
        self,
        journeys: list[CustomerJourney],
        model: AttributionModel | None = None,
    ) -> list[AttributionResult]:
        """Run attribution analysis on customer journeys."""
        model = model or self.default_model
        self.logger.info("running_attribution", model=model.value, journey_count=len(journeys))

        results: list[AttributionResult] = []
        for journey in journeys:
            if not journey.converted or not journey.touchpoints:
                continue

            channel_attributions = self._calculate_attribution(journey, model)
            results.append(
                AttributionResult(
                    user_id=journey.user_id,
                    model=model,
                    channel_attributions=channel_attributions,
                    total_revenue=journey.conversion_value,
                )
            )

        return results

    def _calculate_attribution(
        self,
        journey: CustomerJourney,
        model: AttributionModel,
    ) -> dict[str, float]:
        """Calculate attribution for a single journey based on the model."""
        touchpoints = journey.touchpoints
        total_revenue = journey.conversion_value

        if model == AttributionModel.FIRST_TOUCH:
            return self._first_touch_attribution(touchpoints, total_revenue)
        elif model == AttributionModel.LAST_TOUCH:
            return self._last_touch_attribution(touchpoints, total_revenue)
        elif model == AttributionModel.LINEAR:
            return self._linear_attribution(touchpoints, total_revenue)
        elif model == AttributionModel.TIME_DECAY:
            return self._time_decay_attribution(touchpoints, total_revenue)
        elif model == AttributionModel.DATA_DRIVEN:
            return self._data_driven_attribution(touchpoints, total_revenue)
        else:
            raise ValueError(f"Unsupported attribution model: {model}")

    def _first_touch_attribution(
        self,
        touchpoints: list[Touchpoint],
        total_revenue: float,
    ) -> dict[str, float]:
        """First-touch attribution: 100% credit to the first touchpoint."""
        if not touchpoints:
            return {}
        first_channel = touchpoints[0].channel
        return {first_channel: total_revenue}

    def _last_touch_attribution(
        self,
        touchpoints: list[Touchpoint],
        total_revenue: float,
    ) -> dict[str, float]:
        """Last-touch attribution: 100% credit to the last touchpoint."""
        if not touchpoints:
            return {}
        last_channel = touchpoints[-1].channel
        return {last_channel: total_revenue}

    def _linear_attribution(
        self,
        touchpoints: list[Touchpoint],
        total_revenue: float,
    ) -> dict[str, float]:
        """Linear attribution: equal credit to all touchpoints."""
        if not touchpoints:
            return {}
        credit_per_touch = total_revenue / len(touchpoints)
        result: dict[str, float] = {}
        for tp in touchpoints:
            result[tp.channel] = result.get(tp.channel, 0.0) + credit_per_touch
        return result

    def _time_decay_attribution(
        self,
        touchpoints: list[Touchpoint],
        total_revenue: float,
        half_life_days: float = 7.0,
    ) -> dict[str, float]:
        """Time-decay attribution: more credit to touchpoints closer to conversion."""
        if not touchpoints:
            return {}

        conversion_time = touchpoints[-1].timestamp
        decay_constant = np.log(2) / half_life_days

        weights: list[float] = []
        for tp in touchpoints:
            days_before = (conversion_time - tp.timestamp).total_seconds() / 86400
            weight = np.exp(-decay_constant * max(0, days_before))
            weights.append(weight)

        total_weight = sum(weights)
        if total_weight == 0:
            return self._linear_attribution(touchpoints, total_revenue)

        result: dict[str, float] = {}
        for tp, weight in zip(touchpoints, weights, strict=False):
            credit = (weight / total_weight) * total_revenue
            result[tp.channel] = result.get(tp.channel, 0.0) + credit

        return result

    def _data_driven_attribution(
        self,
        touchpoints: list[Touchpoint],
        total_revenue: float,
    ) -> dict[str, float]:
        """Data-driven attribution using Shapley value approximation."""
        if not touchpoints:
            return {}
        if len(touchpoints) == 1:
            return {touchpoints[0].channel: total_revenue}

        # Simplified Shapley value approximation
        channels = list(dict.fromkeys(tp.channel for tp in touchpoints))
        n = len(channels)

        if n == 1:
            return {channels[0]: total_revenue}

        # Calculate marginal contributions
        marginal_contributions: dict[str, float] = {ch: 0.0 for ch in channels}

        for _i, channel in enumerate(channels):
            # Count occurrences and positions
            positions = [j for j, tp in enumerate(touchpoints) if tp.channel == channel]
            count = len(positions)

            # Weight by position (earlier positions get more weight in this approximation)
            position_weight = sum(
                1.0 / (1 + pos) for pos in positions
            )

            # Normalize by channel frequency
            marginal_contributions[channel] = position_weight / count

        total_contribution = sum(marginal_contributions.values())
        if total_contribution == 0:
            return self._linear_attribution(touchpoints, total_revenue)

        result: dict[str, float] = {}
        for channel, contribution in marginal_contributions.items():
            result[channel] = (contribution / total_contribution) * total_revenue

        return result

    def aggregate_results(
        self,
        results: list[AttributionResult],
    ) -> AggregatedAttribution:
        """Aggregate attribution results across all journeys."""
        if not results:
            return AggregatedAttribution(model=self.default_model)

        model = results[0].model
        channel_totals: dict[str, float] = {}
        total_revenue = 0.0
        converted_journeys = 0

        for result in results:
            converted_journeys += 1
            total_revenue += result.total_revenue
            for channel, value in result.channel_attributions.items():
                channel_totals[channel] = channel_totals.get(channel, 0.0) + value

        channel_percentages: dict[str, float] = {}
        if total_revenue > 0:
            for channel, value in channel_totals.items():
                channel_percentages[channel] = (value / total_revenue) * 100

        return AggregatedAttribution(
            model=model,
            channel_totals=channel_totals,
            channel_percentages=channel_percentages,
            total_revenue=total_revenue,
            journey_count=len(results),
            converted_journeys=converted_journeys,
        )

    def compare_models(
        self,
        journeys: list[CustomerJourney],
    ) -> dict[str, AggregatedAttribution]:
        """Run all attribution models and return comparison."""
        comparison: dict[str, AggregatedAttribution] = {}
        for model in AttributionModel:
            results = self.run_attribution(journeys, model)
            comparison[model.value] = self.aggregate_results(results)
        return comparison
