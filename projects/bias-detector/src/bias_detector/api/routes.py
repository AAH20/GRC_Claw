"""FastAPI routes for bias-detector API."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

from bias_detector.api.dependencies import (
    DemographicAnalyzerDep,
    FairnessScorerDep,
    LanguageBiasDetectorDep,
    PatternDetectorDep,
    RecommendationAgentDep,
)
from bias_detector.config import get_settings
from bias_detector.models import (
    AnalyzeDemographicsRequest,
    AnalyzeFairnessRequest,
    AnalyzeLanguageRequest,
    AnalyzePatternsRequest,
    BiasReport,
    CreateReportRequest,
    FullAnalysisRequest,
    GetRecommendationsRequest,
    HealthResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory report store (replace with database in production)
_reports: dict[str, BiasReport] = {}

# Prometheus metrics
REQUEST_COUNT = Counter(
    "bias_detector_requests_total",
    "Total requests",
    ["method", "endpoint", "status"],
)
REQUEST_DURATION = Histogram(
    "bias_detector_request_duration_seconds",
    "Request duration in seconds",
    ["method", "endpoint"],
)


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        HealthResponse with service status.
    """
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow(),
    )


@router.get("/api/v1/reports", response_model=list[BiasReport], tags=["reports"])
async def list_reports() -> list[BiasReport]:
    """List all bias reports.

    Returns:
        List of all bias reports.
    """
    return list(_reports.values())


@router.post(
    "/api/v1/reports",
    response_model=BiasReport,
    status_code=status.HTTP_201_CREATED,
    tags=["reports"],
)
async def create_report(request: CreateReportRequest) -> BiasReport:
    """Create a new bias report.

    Args:
        request: Report creation request.

    Returns:
        Created BiasReport.
    """
    report_id = str(uuid.uuid4())
    report = BiasReport(
        report_id=report_id,
        title=request.title,
        description=request.description,
        status="pending",
        metadata=request.metadata,
    )
    _reports[report_id] = report
    logger.info("Created report %s", report_id)
    return report


@router.get("/api/v1/reports/{report_id}", response_model=BiasReport, tags=["reports"])
async def get_report(report_id: str) -> BiasReport:
    """Get a specific bias report.

    Args:
        report_id: Report identifier.

    Returns:
        BiasReport if found.

    Raises:
        HTTPException: If report not found.
    """
    if report_id not in _reports:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )
    return _reports[report_id]


@router.delete(
    "/api/v1/reports/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["reports"],
)
async def delete_report(report_id: str) -> None:
    """Delete a bias report.

    Args:
        report_id: Report identifier.

    Raises:
        HTTPException: If report not found.
    """
    if report_id not in _reports:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )
    del _reports[report_id]
    logger.info("Deleted report %s", report_id)


@router.post(
    "/api/v1/analyze/demographics",
    tags=["analysis"],
)
async def analyze_demographics(
    request: AnalyzeDemographicsRequest,
    agent: DemographicAnalyzerDep,
) -> Any:
    """Run demographic analysis.

    Args:
        request: Demographic analysis request.
        agent: Demographic analyzer agent.

    Returns:
        Demographic analysis result.
    """
    logger.info("Running demographic analysis")
    result = await agent.analyze(request.demographic_data)
    return result


@router.post(
    "/api/v1/analyze/language",
    tags=["analysis"],
)
async def analyze_language(
    request: AnalyzeLanguageRequest,
    agent: LanguageBiasDetectorDep,
) -> Any:
    """Run language bias detection.

    Args:
        request: Language analysis request.
        agent: Language bias detector agent.

    Returns:
        Language bias detection result.
    """
    logger.info("Running language bias detection")
    result = await agent.analyze(request.text)
    return result


@router.post(
    "/api/v1/analyze/fairness",
    tags=["analysis"],
)
async def analyze_fairness(
    request: AnalyzeFairnessRequest,
    agent: FairnessScorerDep,
) -> Any:
    """Run fairness scoring.

    Args:
        request: Fairness analysis request.
        agent: Fairness scorer agent.

    Returns:
        Fairness score result.
    """
    logger.info("Running fairness scoring")
    data = {
        "demographic_data": request.demographic_data,
        "language_patterns": request.language_patterns,
        "hiring_decisions": request.hiring_decisions,
    }
    result = await agent.analyze(data)
    return result


@router.post(
    "/api/v1/analyze/patterns",
    tags=["analysis"],
)
async def analyze_patterns(
    request: AnalyzePatternsRequest,
    agent: PatternDetectorDep,
) -> Any:
    """Run pattern detection.

    Args:
        request: Pattern detection request.
        agent: Pattern detector agent.

    Returns:
        List of detected patterns.
    """
    logger.info("Running pattern detection")
    data = {
        "hiring_decisions": request.hiring_decisions,
        "demographic_data": request.demographic_data,
    }
    result = await agent.analyze(data)
    return result


@router.post(
    "/api/v1/analyze/recommendations",
    tags=["analysis"],
)
async def get_recommendations(
    request: GetRecommendationsRequest,
    agent: RecommendationAgentDep,
) -> Any:
    """Get recommendations from analysis results.

    Args:
        request: Recommendations request.
        agent: Recommendation agent.

    Returns:
        List of recommendations.
    """
    logger.info("Generating recommendations")
    data = {
        "demographic_analysis": request.demographic_analysis,
        "language_bias": request.language_bias,
        "fairness_score": request.fairness_score,
        "patterns": request.patterns,
    }
    result = await agent.analyze(data)
    return result


@router.post(
    "/api/v1/analyze/full",
    response_model=BiasReport,
    tags=["analysis"],
)
async def run_full_analysis(
    request: FullAnalysisRequest,
    demo_agent: DemographicAnalyzerDep,
    lang_agent: LanguageBiasDetectorDep,
    fairness_agent: FairnessScorerDep,
    pattern_agent: PatternDetectorDep,
    rec_agent: RecommendationAgentDep,
) -> BiasReport:
    """Run full analysis pipeline.

    Args:
        request: Full analysis request.
        demo_agent: Demographic analyzer agent.
        lang_agent: Language bias detector agent.
        fairness_agent: Fairness scorer agent.
        pattern_agent: Pattern detector agent.
        rec_agent: Recommendation agent.

    Returns:
        Complete BiasReport.
    """
    logger.info("Running full analysis pipeline")

    # Run all analyses
    demo_result = await demo_agent.analyze(request.demographic_data)

    lang_result = None
    if request.job_descriptions:
        combined_text = " ".join(request.job_descriptions)
        lang_result = await lang_agent.analyze(combined_text)
    else:
        from bias_detector.models import LanguageBiasResult
        lang_result = LanguageBiasResult()

    fairness_data = {
        "demographic_data": request.demographic_data,
        "language_patterns": lang_result.patterns,
        "hiring_decisions": request.hiring_decisions,
    }
    fairness_result = await fairness_agent.analyze(fairness_data)

    pattern_data = {
        "hiring_decisions": request.hiring_decisions,
        "demographic_data": request.demographic_data,
    }
    patterns = await pattern_agent.analyze(pattern_data)

    rec_data = {
        "demographic_analysis": demo_result,
        "language_bias": lang_result,
        "fairness_score": fairness_result,
        "patterns": patterns,
    }
    recommendations = await rec_agent.analyze(rec_data)

    report_id = str(uuid.uuid4())
    report = BiasReport(
        report_id=report_id,
        title="Full Analysis Report",
        description="Comprehensive bias analysis report",
        demographic_analysis=demo_result,
        language_bias=lang_result,
        fairness_score=fairness_result,
        patterns=patterns,
        recommendations=recommendations,
        status="completed",
    )
    _reports[report_id] = report
    logger.info("Full analysis complete: report %s", report_id)
    return report


@router.get("/api/v1/metrics", tags=["monitoring"])
async def metrics() -> Response:
    """Prometheus metrics endpoint.

    Returns:
        Prometheus metrics in text format.
    """
    return Response(
        content=generate_latest(),
        media_type="text/plain",
    )


@router.get("/api/v1/config", tags=["monitoring"])
async def get_config() -> dict[str, Any]:
    """Get current configuration.

    Returns:
        Current application configuration.
    """
    settings = get_settings()
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "app_env": settings.app_env,
        "log_level": settings.log_level,
        "demographic_disparity_threshold": settings.demographic_disparity_threshold,
        "language_bias_threshold": settings.language_bias_threshold,
        "fairness_score_threshold": settings.fairness_score_threshold,
    }
