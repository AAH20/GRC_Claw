"""Bias detector API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/analyze-language")
async def analyze_language(data: dict[str, Any]) -> dict[str, Any]:
    """Detect biased language in text.

    Args:
        data: Dictionary with 'text' to analyze.

    Returns:
        Detected biased phrases with suggestions.
    """
    try:
        from recruitment_platform.agents.bias_detector.language_bias_detector import (
            LanguageBiasDetector,
        )

        agent = LanguageBiasDetector()
        result = await agent.process(data)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/fairness-score")
async def compute_fairness(data: dict[str, Any]) -> dict[str, Any]:
    """Compute fairness metrics.

    Args:
        data: Dictionary with 'decisions' and 'protected_attributes'.

    Returns:
        Fairness metric scores.
    """
    from recruitment_platform.agents.bias_detector.fairness_scorer import FairnessScorer

    agent = FairnessScorer()
    result = await agent.process(data)
    return {"success": True, "data": result}


@router.post("/demographic-analysis")
async def analyze_demographics(data: dict[str, Any]) -> dict[str, Any]:
    """Analyze demographic patterns.

    Args:
        data: Dictionary with 'hiring_data' and 'demographics'.

    Returns:
        Demographic analysis results.
    """
    from recruitment_platform.agents.bias_detector.demographic_analyzer import (
        DemographicAnalyzer,
    )

    agent = DemographicAnalyzer()
    result = await agent.process(data)
    return {"success": True, "data": result}


@router.post("/recommendations")
async def get_recommendations(data: dict[str, Any]) -> dict[str, Any]:
    """Get bias mitigation recommendations.

    Args:
        data: Dictionary with 'bias_analysis' results.

    Returns:
        Actionable recommendations.
    """
    from recruitment_platform.agents.bias_detector.recommendation import Recommendation

    agent = Recommendation()
    result = await agent.process(data)
    return {"success": True, "data": result}
