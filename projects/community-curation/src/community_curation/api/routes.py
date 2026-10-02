"""API routes for the community curation service."""

from __future__ import annotations

import time
import uuid
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, status

from community_curation.agents import (
    ContentRankerAgent,
    CurationExplainerAgent,
    QualityFilterAgent,
    TopicClusterAgent,
    TrendSurferAgent,
)
from community_curation.config.settings import Settings, get_settings
from community_curation.integrations import ContentFetcher
from community_curation.models import (
    AgentInfo,
    CurationRequest,
    CurationResult,
    HealthResponse,
    QualityAssessment,
    RankedContent,
    TopicCluster,
    Trend,
)

logger = structlog.get_logger(__name__)

router = APIRouter()


def get_ranker_agent() -> ContentRankerAgent:
    """Dependency to get the content ranker agent."""
    return ContentRankerAgent()


def get_trend_agent() -> TrendSurferAgent:
    """Dependency to get the trend surfer agent."""
    return TrendSurferAgent()


def get_quality_agent() -> QualityFilterAgent:
    """Dependency to get the quality filter agent."""
    return QualityFilterAgent()


def get_cluster_agent() -> TopicClusterAgent:
    """Dependency to get the topic cluster agent."""
    return TopicClusterAgent()


def get_explainer_agent() -> CurationExplainerAgent:
    """Dependency to get the curation explainer agent."""
    return CurationExplainerAgent()


def get_content_fetcher() -> ContentFetcher:
    """Dependency to get the content fetcher."""
    return ContentFetcher()


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check(
    ranker: ContentRankerAgent = Depends(get_ranker_agent),  # noqa: B008
    trend: TrendSurferAgent = Depends(get_trend_agent),  # noqa: B008
    quality: QualityFilterAgent = Depends(get_quality_agent),  # noqa: B008
    cluster: TopicClusterAgent = Depends(get_cluster_agent),  # noqa: B008
    explainer: CurationExplainerAgent = Depends(get_explainer_agent),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> HealthResponse:
    """Health check endpoint.

    Returns:
        Health status of the service and its agents.
    """
    agents = [
        AgentInfo(
            name=agent.name,
            description=agent.description,
            status="available" if agent.is_available else "unavailable",
            capabilities=[agent.description],
        )
        for agent in [ranker, trend, quality, cluster, explainer]
    ]
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        agents=agents,
    )


@router.get("/agents", response_model=list[AgentInfo], tags=["agents"])
async def list_agents(
    ranker: ContentRankerAgent = Depends(get_ranker_agent),  # noqa: B008
    trend: TrendSurferAgent = Depends(get_trend_agent),  # noqa: B008
    quality: QualityFilterAgent = Depends(get_quality_agent),  # noqa: B008
    cluster: TopicClusterAgent = Depends(get_cluster_agent),  # noqa: B008
    explainer: CurationExplainerAgent = Depends(get_explainer_agent),  # noqa: B008
) -> list[AgentInfo]:
    """List all available agents.

    Returns:
        List of agent information.
    """
    return [
        AgentInfo(
            name=agent.name,
            description=agent.description,
            status="available" if agent.is_available else "unavailable",
            capabilities=[agent.description],
        )
        for agent in [ranker, trend, quality, cluster, explainer]
    ]


@router.post("/curate", response_model=CurationResult, tags=["curation"])
async def curate_content(
    request: CurationRequest,
    ranker: ContentRankerAgent = Depends(get_ranker_agent),  # noqa: B008
    trend: TrendSurferAgent = Depends(get_trend_agent),  # noqa: B008
    quality: QualityFilterAgent = Depends(get_quality_agent),  # noqa: B008
    cluster: TopicClusterAgent = Depends(get_cluster_agent),  # noqa: B008
    explainer: CurationExplainerAgent = Depends(get_explainer_agent),  # noqa: B008
    fetcher: ContentFetcher = Depends(get_content_fetcher),  # noqa: B008
) -> CurationResult:
    """Run the full curation pipeline.

    Args:
        request: Curation request parameters.

    Returns:
        Complete curation result with ranked content, trends, clusters, and explanation.
    """
    start_time = time.monotonic()
    request_id = str(uuid.uuid4())

    try:
        # Fetch content from sources
        content = await fetcher.fetch(
            query=request.query,
            sources=request.sources,
            limit=request.limit,
            time_range=request.time_range,
        )

        total_candidates = len(content)

        # Quality filter
        quality_results = await quality.run(content)

        # Filter out spam and low quality
        valid_ids = {
            q.content_id
            for q in quality_results
            if (
                not q.is_spam
                and not q.is_low_quality
                and q.quality_score >= request.min_quality_score
            )
        }
        filtered_content = [c for c in content if c.id in valid_ids]

        # Rank content
        ranked = await ranker.run(filtered_content, query=request.query)

        # Limit results
        ranked = ranked[: request.limit]

        # Surface trends
        trends: list[Trend] = []
        if request.include_trends:
            trends = await trend.run(filtered_content)

        # Cluster topics
        clusters: list[TopicCluster] = []
        if request.include_clusters:
            clusters = await cluster.run(filtered_content)

        # Generate explanation
        explanation = await explainer.run((ranked, trends, clusters, quality_results))

        processing_time = (time.monotonic() - start_time) * 1000

        return CurationResult(
            request_id=request_id,
            query=request.query,
            ranked_content=ranked,
            trends=trends,
            clusters=clusters,
            quality_filtered=quality_results,
            explanation=explanation,
            total_candidates=total_candidates,
            processing_time_ms=round(processing_time, 2),
        )

    except Exception as exc:
        logger.error("curation_failed", request_id=request_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Curation failed: {str(exc)}",
        ) from exc


@router.post("/rank", response_model=list[RankedContent], tags=["curation"])
async def rank_content(
    request: CurationRequest,
    ranker: ContentRankerAgent = Depends(get_ranker_agent),  # noqa: B008
    fetcher: ContentFetcher = Depends(get_content_fetcher),  # noqa: B008
) -> list[RankedContent]:
    """Rank content without full curation pipeline.

    Args:
        request: Curation request parameters.

    Returns:
        List of ranked content items.
    """
    try:
        content = await fetcher.fetch(
            query=request.query,
            sources=request.sources,
            limit=request.limit,
            time_range=request.time_range,
        )
        return await ranker.run(content, query=request.query)
    except Exception as exc:
        logger.error("ranking_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ranking failed: {str(exc)}",
        ) from exc


@router.post("/trends", response_model=list[Trend], tags=["curation"])
async def surface_trends(
    request: CurationRequest,
    trend: TrendSurferAgent = Depends(get_trend_agent),  # noqa: B008
    fetcher: ContentFetcher = Depends(get_content_fetcher),  # noqa: B008
) -> list[Trend]:
    """Surface trends from community content.

    Args:
        request: Curation request parameters.

    Returns:
        List of detected trends.
    """
    try:
        content = await fetcher.fetch(
            query=request.query,
            sources=request.sources,
            limit=request.limit,
            time_range=request.time_range,
        )
        return await trend.run(content)
    except Exception as exc:
        logger.error("trend_surfacing_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trend surfacing failed: {str(exc)}",
        ) from exc


@router.post("/filter", response_model=list[QualityAssessment], tags=["curation"])
async def filter_quality(
    request: CurationRequest,
    quality: QualityFilterAgent = Depends(get_quality_agent),  # noqa: B008
    fetcher: ContentFetcher = Depends(get_content_fetcher),  # noqa: B008
) -> list[QualityAssessment]:
    """Filter content by quality.

    Args:
        request: Curation request parameters.

    Returns:
        List of quality assessments.
    """
    try:
        content = await fetcher.fetch(
            query=request.query,
            sources=request.sources,
            limit=request.limit,
            time_range=request.time_range,
        )
        return await quality.run(content)
    except Exception as exc:
        logger.error("quality_filter_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quality filtering failed: {str(exc)}",
        ) from exc


@router.post("/cluster", response_model=list[TopicCluster], tags=["curation"])
async def cluster_topics(
    request: CurationRequest,
    cluster: TopicClusterAgent = Depends(get_cluster_agent),  # noqa: B008
    fetcher: ContentFetcher = Depends(get_content_fetcher),  # noqa: B008
) -> list[TopicCluster]:
    """Cluster content into topic groups.

    Args:
        request: Curation request parameters.

    Returns:
        List of topic clusters.
    """
    try:
        content = await fetcher.fetch(
            query=request.query,
            sources=request.sources,
            limit=request.limit,
            time_range=request.time_range,
        )
        return await cluster.run(content)
    except Exception as exc:
        logger.error("clustering_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clustering failed: {str(exc)}",
        ) from exc


@router.post("/explain", response_model=dict[str, str], tags=["curation"])
async def explain_curation(
    result: CurationResult,
    explainer: CurationExplainerAgent = Depends(get_explainer_agent),  # noqa: B008
) -> dict[str, str]:
    """Explain a curation result.

    Args:
        result: Curation result to explain.

    Returns:
        Explanation dictionary.
    """
    try:
        explanation = await explainer.run(
            (result.ranked_content, result.trends, result.clusters, result.quality_filtered)
        )
        return {"explanation": explanation}
    except Exception as exc:
        logger.error("explanation_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Explanation failed: {str(exc)}",
        ) from exc


@router.get("/metrics", tags=["monitoring"])
async def get_metrics(
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> dict[str, Any]:
    """Get service metrics.

    Returns:
        Service metrics dictionary.
    """
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "environment": settings.environment,
        "agents_count": 5,
        "endpoints_count": 10,
    }
