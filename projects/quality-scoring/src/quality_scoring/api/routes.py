"""API routes for quality scoring service."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from quality_scoring.config.settings import Settings, get_settings
from quality_scoring.models.schemas import (
    BatchScoreRequest,
    BatchScoreResponse,
    BenchmarkComparison,
    ContentInput,
    ContentType,
    DimensionScore,
    HealthResponse,
    ImprovementPlan,
    QualityScore,
    ScoreDimension,
    ScoreRequest,
    ScoreResponse,
)
from quality_scoring.services import BenchmarkService, ScoringService

logger = logging.getLogger(__name__)

# Service instances (singleton pattern)
_scoring_service: ScoringService | None = None
_benchmark_service: BenchmarkService | None = None
_start_time: float = time.time()


def get_scoring_service() -> ScoringService:
    """Get or create the scoring service singleton.

    Returns:
        ScoringService instance.
    """
    global _scoring_service
    if _scoring_service is None:
        _scoring_service = ScoringService()
    return _scoring_service


def get_benchmark_service() -> BenchmarkService:
    """Get or create the benchmark service singleton.

    Returns:
        BenchmarkService instance.
    """
    global _benchmark_service
    if _benchmark_service is None:
        _benchmark_service = BenchmarkService()
    return _benchmark_service


router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    """Health check endpoint.

    Returns:
        HealthResponse with service status.
    """
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        uptime_seconds=round(time.time() - _start_time, 2),
    )


@router.get("/metrics", tags=["Monitoring"])
async def metrics(
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """Prometheus metrics endpoint.

    Returns:
        JSONResponse with metrics data.
    """
    if not settings.enable_metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metrics disabled",
        )

    # Basic metrics (in production, use prometheus_client)
    metrics_data = {
        "uptime_seconds": time.time() - _start_time,
        "requests_total": 0,  # Would be tracked by middleware
        "requests_failed": 0,
    }
    return JSONResponse(content=metrics_data)


@router.post(
    "/api/v1/score",
    response_model=ScoreResponse,
    tags=["Scoring"],
    status_code=status.HTTP_200_OK,
)
async def score_content(
    request: ScoreRequest,
    scoring_service: ScoringService = Depends(get_scoring_service),
    benchmark_service: BenchmarkService = Depends(get_benchmark_service),
) -> ScoreResponse:
    """Score content quality across all or specified dimensions.

    Args:
        request: ScoreRequest with content and options.
        scoring_service: Scoring service instance.
        benchmark_service: Benchmark service instance.

    Returns:
        ScoreResponse with quality score and optional benchmark/improvements.
    """
    try:
        # Validate content length
        content_length = len(request.content.content)
        settings = get_settings()
        if content_length < settings.min_content_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Content too short. Minimum {settings.min_content_length} "
                    "characters required."
                ),
            )
        if content_length > settings.max_content_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Content too long. Maximum {settings.max_content_length} "
                    "characters allowed."
                ),
            )

        # Score content
        quality_score = await scoring_service.score_content(
            request.content,
            dimensions=request.dimensions,
        )

        # Optional benchmark comparison
        benchmark = None
        if request.include_benchmark:
            benchmark = benchmark_service.compare(
                quality_score.id,
                request.content.content_type,
                quality_score.dimensions,
            )

        # Optional improvement suggestions
        improvements = None
        if request.include_improvements:
            improvements = await scoring_service.get_improvements(
                request.content.content,
                quality_score.id,
                quality_score.dimensions,
            )

        return ScoreResponse(
            score=quality_score,
            benchmark=benchmark,
            improvements=improvements,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Scoring failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scoring failed: {str(exc)}",
        )


@router.post(
    "/api/v1/score/readability",
    response_model=DimensionScore,
    tags=["Scoring"],
)
async def score_readability(
    content: ContentInput,
    scoring_service: ScoringService = Depends(get_scoring_service),
) -> DimensionScore:
    """Score content readability only.

    Args:
        content: ContentInput with content to score.
        scoring_service: Scoring service instance.

    Returns:
        DimensionScore for readability.
    """
    result = await scoring_service.agents[ScoreDimension.READABILITY].score(content.content)
    if not result.success or not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error or "Readability scoring failed",
        )
    return result.data


@router.post(
    "/api/v1/score/originality",
    response_model=DimensionScore,
    tags=["Scoring"],
)
async def score_originality(
    content: ContentInput,
    scoring_service: ScoringService = Depends(get_scoring_service),
) -> DimensionScore:
    """Score content originality only.

    Args:
        content: ContentInput with content to score.
        scoring_service: Scoring service instance.

    Returns:
        DimensionScore for originality.
    """
    result = await scoring_service.agents[ScoreDimension.ORIGINALITY].score(content.content)
    if not result.success or not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error or "Originality scoring failed",
        )
    return result.data


@router.post(
    "/api/v1/score/engagement",
    response_model=DimensionScore,
    tags=["Scoring"],
)
async def score_engagement(
    content: ContentInput,
    scoring_service: ScoringService = Depends(get_scoring_service),
) -> DimensionScore:
    """Score content engagement only.

    Args:
        content: ContentInput with content to score.
        scoring_service: Scoring service instance.

    Returns:
        DimensionScore for engagement.
    """
    result = await scoring_service.agents[ScoreDimension.ENGAGEMENT].score(content.content)
    if not result.success or not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error or "Engagement scoring failed",
        )
    return result.data


@router.post(
    "/api/v1/score/seo",
    response_model=DimensionScore,
    tags=["Scoring"],
)
async def score_seo(
    content: ContentInput,
    scoring_service: ScoringService = Depends(get_scoring_service),
) -> DimensionScore:
    """Score content SEO only.

    Args:
        content: ContentInput with content to score.
        scoring_service: Scoring service instance.

    Returns:
        DimensionScore for SEO.
    """
    result = await scoring_service.agents[ScoreDimension.SEO].score(content.content)
    if not result.success or not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error or "SEO scoring failed",
        )
    return result.data


@router.post(
    "/api/v1/improvements",
    response_model=ImprovementPlan,
    tags=["Improvements"],
)
async def get_improvements(
    content: ContentInput,
    dimension_scores: list[DimensionScore],
    scoring_service: ScoringService = Depends(get_scoring_service),
) -> ImprovementPlan:
    """Get improvement suggestions for content.

    Args:
        content: ContentInput with content to analyze.
        dimension_scores: List of dimension scores to base suggestions on.
        scoring_service: Scoring service instance.

    Returns:
        ImprovementPlan with actionable suggestions.
    """
    try:
        plan = await scoring_service.get_improvements(
            content.content,
            str(uuid.uuid4()),
            dimension_scores,
        )
        return plan
    except Exception as exc:
        logger.exception("Improvement generation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Improvement generation failed: {str(exc)}",
        )


@router.post(
    "/api/v1/benchmark",
    response_model=BenchmarkComparison,
    tags=["Benchmark"],
)
async def compare_benchmark(
    content_type: ContentType,
    score_id: str,
    dimension_scores: list[DimensionScore],
    benchmark_service: BenchmarkService = Depends(get_benchmark_service),
) -> BenchmarkComparison:
    """Compare content scores against benchmarks.

    Args:
        content_type: Type of content.
        score_id: Quality score identifier.
        dimension_scores: Dimension scores to compare.
        benchmark_service: Benchmark service instance.

    Returns:
        BenchmarkComparison with percentile rankings.
    """
    try:
        return benchmark_service.compare(score_id, content_type, dimension_scores)
    except Exception as exc:
        logger.exception("Benchmark comparison failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Benchmark comparison failed: {str(exc)}",
        )


@router.post(
    "/api/v1/batch/score",
    response_model=BatchScoreResponse,
    tags=["Scoring"],
)
async def batch_score(
    request: BatchScoreRequest,
    scoring_service: ScoringService = Depends(get_scoring_service),
) -> BatchScoreResponse:
    """Score multiple content items in batch.

    Args:
        request: BatchScoreRequest with items to score.
        scoring_service: Scoring service instance.

    Returns:
        BatchScoreResponse with all scores.
    """
    import asyncio

    start_time = time.time()
    batch_id = str(uuid.uuid4())

    tasks = [
        scoring_service.score_content(item, dimensions=request.dimensions)
        for item in request.items
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    scores: list[QualityScore] = []
    failed = 0
    for result in results:
        if isinstance(result, Exception):
            failed += 1
            logger.error("Batch item failed: %s", str(result))
        else:
            scores.append(result)

    processing_time = (time.time() - start_time) * 1000

    return BatchScoreResponse(
        id=batch_id,
        results=scores,
        total_items=len(request.items),
        successful=len(scores),
        failed=failed,
        processing_time_ms=round(processing_time, 2),
    )


@router.get(
    "/api/v1/dimensions",
    tags=["Info"],
)
async def list_dimensions() -> dict[str, Any]:
    """List available scoring dimensions.

    Returns:
        Dictionary with dimension information.
    """
    return {
        "dimensions": [
            {
                "id": dim.value,
                "name": dim.value.replace("_", " ").title(),
                "description": _get_dimension_description(dim),
            }
            for dim in ScoreDimension
        ]
    }


@router.get(
    "/api/v1/benchmarks",
    tags=["Info"],
)
async def list_benchmarks() -> dict[str, Any]:
    """List available benchmark content types.

    Returns:
        Dictionary with benchmark information.
    """
    return {
        "benchmarks": [
            {
                "content_type": ct.value,
                "description": _get_content_type_description(ct),
            }
            for ct in ContentType
        ]
    }


def _get_dimension_description(dimension: ScoreDimension) -> str:
    """Get description for a scoring dimension.

    Args:
        dimension: The scoring dimension.

    Returns:
        Description string.
    """
    descriptions = {
        ScoreDimension.READABILITY: "Measures how easy the content is to read and understand",
        ScoreDimension.ORIGINALITY: "Measures the uniqueness and freshness of the content",
        ScoreDimension.ENGAGEMENT: "Measures how engaging and compelling the content is",
        ScoreDimension.SEO: "Measures search engine optimization factors",
    }
    return descriptions.get(dimension, "Unknown dimension")


def _get_content_type_description(content_type: ContentType) -> str:
    """Get description for a content type.

    Args:
        content_type: The content type.

    Returns:
        Description string.
    """
    descriptions = {
        ContentType.ARTICLE: "Long-form journalistic or informational content",
        ContentType.BLOG_POST: "Blog articles and posts",
        ContentType.PRODUCT_DESCRIPTION: "Product or service descriptions",
        ContentType.LANDING_PAGE: "Landing page copy",
        ContentType.SOCIAL_MEDIA: "Social media posts and updates",
        ContentType.EMAIL: "Email marketing content",
        ContentType.TECHNICAL_DOC: "Technical documentation",
        ContentType.GENERAL: "General content",
    }
    return descriptions.get(content_type, "Unknown content type")
