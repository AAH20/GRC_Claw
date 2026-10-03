"""Job description optimizer API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/check-ats")
async def check_ats(data: dict[str, Any]) -> dict[str, Any]:
    """Check ATS compatibility.

    Args:
        data: Dictionary with 'job_description' text.

    Returns:
        Compatibility results.
    """
    try:
        from recruitment_platform.agents.job_description_optimizer.ats_compatibility import ATSCompatibility

        agent = ATSCompatibility()
        result = await agent.process(data)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/remove-bias")
async def remove_bias(data: dict[str, Any]) -> dict[str, Any]:
    """Remove biased language.

    Args:
        data: Dictionary with 'job_description' text.

    Returns:
        Cleaned text with bias report.
    """
    from recruitment_platform.agents.job_description_optimizer.bias_remover import BiasRemover

    agent = BiasRemover()
    result = await agent.process(data)
    return {"success": True, "data": result}


@router.post("/optimize-keywords")
async def optimize_keywords(data: dict[str, Any]) -> dict[str, Any]:
    """Optimize keywords.

    Args:
        data: Dictionary with 'job_description' and 'target_role'.

    Returns:
        Optimized text with keyword suggestions.
    """
    from recruitment_platform.agents.job_description_optimizer.keyword_optimizer import KeywordOptimizer

    agent = KeywordOptimizer()
    result = await agent.process(data)
    return {"success": True, "data": result}


@router.post("/optimize-seo")
async def optimize_seo(data: dict[str, Any]) -> dict[str, Any]:
    """Optimize for SEO.

    Args:
        data: Dictionary with 'job_description' and 'platform'.

    Returns:
        SEO recommendations.
    """
    from recruitment_platform.agents.job_description_optimizer.seo_optimizer import SEOOptimizer

    agent = SEOOptimizer()
    result = await agent.process(data)
    return {"success": True, "data": result}


@router.post("/analyze-tone")
async def analyze_tone(data: dict[str, Any]) -> dict[str, Any]:
    """Analyze tone.

    Args:
        data: Dictionary with 'job_description' and 'brand_voice'.

    Returns:
        Tone analysis.
    """
    from recruitment_platform.agents.job_description_optimizer.tone_analyzer import ToneAnalyzer

    agent = ToneAnalyzer()
    result = await agent.process(data)
    return {"success": True, "data": result}
