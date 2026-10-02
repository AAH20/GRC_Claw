"""Attribution API routes."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter

from analytics.agents.attribution_engine import (
    AttributionEngine,
    AttributionModel,
)
from analytics.agents.data_collection import DataSource, RawEvent

router = APIRouter()

_engine = AttributionEngine()


@router.get("/models")
async def list_attribution_models() -> dict[str, Any]:
    """List all available attribution models."""
    return {
        "models": [
            {
                "id": model.value,
                "name": model.value.replace("_", " ").title(),
                "description": _get_model_description(model),
            }
            for model in AttributionModel
        ],
        "default": AttributionModel.DATA_DRIVEN.value,
    }


@router.post("/run")
async def run_attribution(
    model: AttributionModel = AttributionModel.DATA_DRIVEN,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict[str, Any]:
    """Run attribution analysis on collected data."""
    if end_date is None:
        end_date = datetime.utcnow()
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    sample_events = _generate_sample_events(start_date, end_date)
    journeys = _engine.build_journeys(sample_events)
    results = _engine.run_attribution(journeys, model)
    aggregated = _engine.aggregate_results(results)

    return {
        "model": aggregated.model.value,
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "summary": {
            "total_revenue": aggregated.total_revenue,
            "journey_count": aggregated.journey_count,
            "converted_journeys": aggregated.converted_journeys,
        },
        "channel_attributions": aggregated.channel_totals,
        "channel_percentages": aggregated.channel_percentages,
    }


@router.post("/compare")
async def compare_models(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict[str, Any]:
    """Compare all attribution models."""
    if end_date is None:
        end_date = datetime.utcnow()
    if start_date is None:
        start_date = end_date - timedelta(days=30)

    sample_events = _generate_sample_events(start_date, end_date)
    journeys = _engine.build_journeys(sample_events)
    comparison = _engine.compare_models(journeys)

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "models": {
            model_name: {
                "channel_totals": result.channel_totals,
                "channel_percentages": result.channel_percentages,
                "total_revenue": result.total_revenue,
            }
            for model_name, result in comparison.items()
        },
    }


def _get_model_description(model: AttributionModel) -> str:
    """Get a human-readable description of an attribution model."""
    descriptions = {
        AttributionModel.FIRST_TOUCH: "100% credit to the first touchpoint in the journey.",
        AttributionModel.LAST_TOUCH: "100% credit to the last touchpoint before conversion.",
        AttributionModel.LINEAR: "Equal credit distributed across all touchpoints.",
        AttributionModel.TIME_DECAY: (
            "More credit to touchpoints closer to conversion (exponential decay)."
        ),
        AttributionModel.DATA_DRIVEN: "Shapley value approximation for fair credit distribution.",
    }
    return descriptions.get(model, "")


def _generate_sample_events(
    start_date: datetime,
    end_date: datetime,
) -> list[RawEvent]:
    """Generate sample events for demonstration purposes."""
    events: list[RawEvent] = []
    channels = ["organic", "paid_search", "social", "email", "referral"]
    current = start_date

    for i in range(50):
        current = current + timedelta(hours=12)
        if current > end_date:
            break

        user_id = f"user_{i % 10}"
        channel = channels[i % len(channels)]
        revenue = 100.0 if i % 5 == 0 else 0.0

        events.append(
            RawEvent(
                event_id=f"evt_{i}",
                source=DataSource.GOOGLE_ANALYTICS,
                event_type="page_view" if revenue == 0 else "purchase",
                timestamp=current,
                user_id=user_id,
                campaign_id=f"campaign_{i % 3}" if channel != "organic" else None,
                channel=channel,
                revenue=revenue,
            )
        )

    return events
