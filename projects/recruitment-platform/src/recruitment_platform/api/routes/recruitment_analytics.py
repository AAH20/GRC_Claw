"""Recruitment analytics API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/cost-analysis")
async def analyze_cost(data: dict[str, Any]) -> dict[str, Any]:
    """Analyze recruitment costs.

    Args:
        data: Dictionary with 'hiring_data' and 'cost_data'.

    Returns:
        Cost analysis results.
    """
    try:
        from recruitment_platform.agents.recruitment_analytics.cost_analyzer import (
            CostAnalyzer,
        )

        agent = CostAnalyzer()
        result = await agent.process(data)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/funnel-analysis")
async def analyze_funnel(data: dict[str, Any]) -> dict[str, Any]:
    """Analyze recruitment funnel.

    Args:
        data: Dictionary with 'funnel_data'.

    Returns:
        Funnel analysis results.
    """
    from recruitment_platform.agents.recruitment_analytics.funnel_analyzer import (
        FunnelAnalyzer,
    )

    agent = FunnelAnalyzer()
    result = await agent.process(data)
    return {"success": True, "data": result}


@router.post("/diversity-metrics")
async def diversity_metrics(data: dict[str, Any]) -> dict[str, Any]:
    """Get diversity metrics.

    Args:
        data: Dictionary with 'pipeline_data' and 'demographics'.

    Returns:
        Diversity metrics.
    """
    from recruitment_platform.agents.recruitment_analytics.diversity_analyzer import (
        DiversityAnalyzer,
    )

    agent = DiversityAnalyzer()
    result = await agent.process(data)
    return {"success": True, "data": result}


@router.post("/predict")
async def predict_hiring(data: dict[str, Any]) -> dict[str, Any]:
    """Generate hiring predictions.

    Args:
        data: Dictionary with 'historical_data' and 'current_pipeline'.

    Returns:
        Predictive metrics.
    """
    from recruitment_platform.agents.recruitment_analytics.predictive_hiring import (
        PredictiveHiring,
    )

    agent = PredictiveHiring()
    result = await agent.process(data)
    return {"success": True, "data": result}


@router.post("/source-effectiveness")
async def source_effectiveness(data: dict[str, Any]) -> dict[str, Any]:
    """Analyze source effectiveness.

    Args:
        data: Dictionary with 'source_data' and 'outcomes'.

    Returns:
        Source effectiveness metrics.
    """
    from recruitment_platform.agents.recruitment_analytics.source_tracker import (
        SourceTracker,
    )

    agent = SourceTracker()
    result = await agent.process(data)
    return {"success": True, "data": result}
