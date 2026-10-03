"""Candidate matcher API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/match")
async def match_candidates(data: dict[str, Any]) -> dict[str, Any]:
    """Match candidates to a job description.

    Args:
        data: Dictionary with 'candidates' and 'job_requirements'.

    Returns:
        Ranked candidate matches.
    """
    try:
        from recruitment_platform.agents.candidate_matcher.bias_aware_ranker import \
            BiasAwareRanker

        agent = BiasAwareRanker()
        result = await agent.process(data)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/explain")
async def explain_match(data: dict[str, Any]) -> dict[str, Any]:
    """Explain a candidate match.

    Args:
        data: Dictionary with 'candidate', 'job', and 'match_result'.

    Returns:
        Match explanation.
    """
    from recruitment_platform.agents.candidate_matcher.match_explainer import \
        MatchExplainer

    agent = MatchExplainer()
    result = await agent.process(data)
    return {"success": True, "data": result}


@router.post("/gap-analysis")
async def analyze_gap(data: dict[str, Any]) -> dict[str, Any]:
    """Analyze skills gap.

    Args:
        data: Dictionary with 'candidate_skills' and 'required_skills'.

    Returns:
        Gap analysis results.
    """
    from recruitment_platform.agents.candidate_matcher.skills_gap_analyzer import \
        SkillsGapAnalyzer

    agent = SkillsGapAnalyzer()
    result = await agent.process(data)
    return {"success": True, "data": result}
