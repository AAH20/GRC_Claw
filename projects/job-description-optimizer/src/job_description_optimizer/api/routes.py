"""FastAPI routes for the job description optimizer."""

import time
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI

from job_description_optimizer.agents.ats_compatibility import ATSCompatibilityAgent
from job_description_optimizer.agents.bias_remover import BiasRemoverAgent
from job_description_optimizer.agents.keyword_optimizer import KeywordOptimizerAgent
from job_description_optimizer.agents.seo_optimizer import SEOOptimizerAgent
from job_description_optimizer.agents.tone_analyzer import ToneAnalyzerAgent
from job_description_optimizer.config import Settings, get_settings
from job_description_optimizer.models import (
    ATSReport,
    AgentInfo,
    AnalysisRequest,
    BiasReport,
    ErrorResponse,
    HealthResponse,
    JobDescription,
    KeywordReport,
    OptimizationRequest,
    OptimizedDescription,
    SEOReport,
    ToneReport,
)

router = APIRouter()


def get_llm(settings: Settings = Depends(get_settings)) -> BaseLanguageModel:
    """Get or create the language model instance.

    Args:
        settings: Application settings.

    Returns:
        Language model instance.
    """
    return ChatOpenAI(
        model=settings.openai_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        api_key=settings.openai_api_key,
    )


def get_agents(
    llm: BaseLanguageModel = Depends(get_llm),
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    """Get all agent instances.

    Args:
        llm: Language model instance.
        settings: Application settings.

    Returns:
        Dictionary of agent instances.
    """
    return {
        "bias_remover": BiasRemoverAgent(llm=llm, settings=settings),
        "seo_optimizer": SEOOptimizerAgent(llm=llm, settings=settings),
        "ats_compatibility": ATSCompatibilityAgent(llm=llm, settings=settings),
        "tone_analyzer": ToneAnalyzerAgent(llm=llm, settings=settings),
        "keyword_optimizer": KeywordOptimizerAgent(llm=llm, settings=settings),
    }


@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        HealthResponse with service status.
    """
    return HealthResponse(status="healthy")


@router.get("/", tags=["system"])
async def root() -> Dict[str, Any]:
    """Root endpoint with service information.

    Returns:
        Dictionary with service information.
    """
    return {
        "name": "Job Description Optimizer",
        "version": "1.0.0",
        "description": "Agentic AI-powered job description optimizer",
        "endpoints": [
            "/health",
            "/optimize",
            "/optimize/bias",
            "/optimize/seo",
            "/optimize/ats",
            "/optimize/tone",
            "/optimize/keywords",
            "/analyze",
            "/agents",
            "/agents/{name}",
        ],
    }


@router.get("/agents", response_model=List[AgentInfo], tags=["agents"])
async def list_agents(
    agents: Dict[str, Any] = Depends(get_agents),
) -> List[AgentInfo]:
    """List all available agents.

    Args:
        agents: Dictionary of agent instances.

    Returns:
        List of agent information.
    """
    return [
        AgentInfo(
            name=agent.name,
            description=agent.description,
            capabilities=agent.get_capabilities(),
            status="available",
        )
        for agent in agents.values()
    ]


@router.get("/agents/{name}", response_model=AgentInfo, tags=["agents"])
async def get_agent(
    name: str,
    agents: Dict[str, Any] = Depends(get_agents),
) -> AgentInfo:
    """Get information about a specific agent.

    Args:
        name: Agent name.
        agents: Dictionary of agent instances.

    Returns:
        Agent information.

    Raises:
        HTTPException: If agent not found.
    """
    if name not in agents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{name}' not found",
        )
    agent = agents[name]
    return AgentInfo(
        name=agent.name,
        description=agent.description,
        capabilities=agent.get_capabilities(),
        status="available",
    )


@router.post(
    "/optimize",
    response_model=OptimizedDescription,
    tags=["optimization"],
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def optimize(
    request: OptimizationRequest,
    agents: Dict[str, Any] = Depends(get_agents),
) -> OptimizedDescription:
    """Run full optimization pipeline on a job description.

    Args:
        request: Optimization request with job description.
        agents: Dictionary of agent instances.

    Returns:
        OptimizedDescription with all reports.

    Raises:
        HTTPException: If optimization fails.
    """
    start_time = time.time()
    jd = request.job_description
    options = request.options

    bias_report = None
    seo_report = None
    ats_report = None
    tone_report = None
    keyword_report = None

    try:
        if not options.get("skip_bias", False):
            bias_report = await agents["bias_remover"].analyze(jd)
        if not options.get("skip_seo", False):
            seo_report = await agents["seo_optimizer"].analyze(jd)
        if not options.get("skip_ats", False):
            ats_report = await agents["ats_compatibility"].analyze(jd)
        if not options.get("skip_tone", False):
            tone_report = await agents["tone_analyzer"].analyze(jd)
        if not options.get("skip_keywords", False):
            keyword_report = await agents["keyword_optimizer"].analyze(jd)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization failed: {str(e)}",
        )

    # Determine best optimized text
    optimized_text = jd.description
    if bias_report and bias_report.cleaned_text != jd.description:
        optimized_text = bias_report.cleaned_text
    if ats_report and ats_report.compatible_text != jd.description:
        optimized_text = ats_report.compatible_text

    # Calculate overall score
    scores = []
    if bias_report:
        scores.append(1.0 - bias_report.overall_score)
    if seo_report:
        scores.append(seo_report.seo_score)
    if ats_report:
        scores.append(ats_report.ats_score)
    if tone_report:
        scores.append(tone_report.inclusivity_score)
    if keyword_report:
        scores.append(keyword_report.industry_relevance)

    overall_score = sum(scores) / len(scores) if scores else 0.5
    processing_time = (time.time() - start_time) * 1000

    return OptimizedDescription(
        original=jd,
        optimized_text=optimized_text,
        bias_report=bias_report,
        seo_report=seo_report,
        ats_report=ats_report,
        tone_report=tone_report,
        keyword_report=keyword_report,
        overall_score=overall_score,
        processing_time_ms=processing_time,
    )


@router.post(
    "/optimize/bias",
    response_model=BiasReport,
    tags=["optimization"],
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def optimize_bias(
    job_description: JobDescription,
    agents: Dict[str, Any] = Depends(get_agents),
) -> BiasReport:
    """Run bias removal only.

    Args:
        job_description: Job description to analyze.
        agents: Dictionary of agent instances.

    Returns:
        BiasReport with bias analysis.

    Raises:
        HTTPException: If analysis fails.
    """
    try:
        return await agents["bias_remover"].analyze(job_description)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bias analysis failed: {str(e)}",
        )


@router.post(
    "/optimize/seo",
    response_model=SEOReport,
    tags=["optimization"],
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def optimize_seo(
    job_description: JobDescription,
    agents: Dict[str, Any] = Depends(get_agents),
) -> SEOReport:
    """Run SEO optimization only.

    Args:
        job_description: Job description to optimize.
        agents: Dictionary of agent instances.

    Returns:
        SEOReport with SEO analysis.

    Raises:
        HTTPException: If analysis fails.
    """
    try:
        return await agents["seo_optimizer"].analyze(job_description)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SEO optimization failed: {str(e)}",
        )


@router.post(
    "/optimize/ats",
    response_model=ATSReport,
    tags=["optimization"],
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def optimize_ats(
    job_description: JobDescription,
    agents: Dict[str, Any] = Depends(get_agents),
) -> ATSReport:
    """Run ATS compatibility check only.

    Args:
        job_description: Job description to check.
        agents: Dictionary of agent instances.

    Returns:
        ATSReport with compatibility analysis.

    Raises:
        HTTPException: If analysis fails.
    """
    try:
        return await agents["ats_compatibility"].analyze(job_description)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ATS compatibility check failed: {str(e)}",
        )


@router.post(
    "/optimize/tone",
    response_model=ToneReport,
    tags=["optimization"],
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def optimize_tone(
    job_description: JobDescription,
    agents: Dict[str, Any] = Depends(get_agents),
) -> ToneReport:
    """Run tone analysis only.

    Args:
        job_description: Job description to analyze.
        agents: Dictionary of agent instances.

    Returns:
        ToneReport with tone analysis.

    Raises:
        HTTPException: If analysis fails.
    """
    try:
        return await agents["tone_analyzer"].analyze(job_description)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tone analysis failed: {str(e)}",
        )


@router.post(
    "/optimize/keywords",
    response_model=KeywordReport,
    tags=["optimization"],
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def optimize_keywords(
    job_description: JobDescription,
    agents: Dict[str, Any] = Depends(get_agents),
) -> KeywordReport:
    """Run keyword optimization only.

    Args:
        job_description: Job description to optimize.
        agents: Dictionary of agent instances.

    Returns:
        KeywordReport with keyword analysis.

    Raises:
        HTTPException: If analysis fails.
    """
    try:
        return await agents["keyword_optimizer"].analyze(job_description)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Keyword optimization failed: {str(e)}",
        )


@router.post(
    "/analyze",
    response_model=Dict[str, Any],
    tags=["analysis"],
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def analyze(
    request: AnalysisRequest,
    agents: Dict[str, Any] = Depends(get_agents),
) -> Dict[str, Any]:
    """Run comprehensive analysis with selected agents.

    Args:
        request: Analysis request with job description and selected analyses.
        agents: Dictionary of agent instances.

    Returns:
        Dictionary with analysis results.

    Raises:
        HTTPException: If analysis fails.
    """
    jd = request.job_description
    analyses = request.analyses
    results: Dict[str, Any] = {}

    agent_map = {
        "bias": "bias_remover",
        "seo": "seo_optimizer",
        "ats": "ats_compatibility",
        "tone": "tone_analyzer",
        "keywords": "keyword_optimizer",
    }

    try:
        for analysis in analyses:
            agent_name = agent_map.get(analysis)
            if agent_name and agent_name in agents:
                results[analysis] = await agents[agent_name].analyze(jd)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )

    return results
