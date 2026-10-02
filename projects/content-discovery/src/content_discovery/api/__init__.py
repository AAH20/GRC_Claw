"""API route handlers for content discovery endpoints."""

from __future__ import annotations

import uuid
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status

from content_discovery.agents import (
    PersonalizationAgent,
    RecommendationAgent,
    SearchExplainerAgent,
    SemanticSearchAgent,
    TrendDetectorAgent,
)
from content_discovery.config import Settings, get_settings
from content_discovery.integrations import (
    AnalyticsClient,
    ContentClient,
    UserProfileClient,
    VectorStoreClient,
)
from content_discovery.models import (
    HealthResponse,
    RecommendationRequest,
    RecommendationResponse,
    SearchExplanation,
    SearchRequest,
    SearchResponse,
    TrendRequest,
    TrendResponse,
)

logger = structlog.get_logger()

router = APIRouter()


# Dependency injection helpers


def get_vector_store(
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> VectorStoreClient:
    """Get vector store client.

    Args:
        settings: Application settings.

    Returns:
        VectorStoreClient: Vector store client.
    """
    return VectorStoreClient(base_url=settings.vector_store_url)


def get_user_profile(
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> UserProfileClient:
    """Get user profile client.

    Args:
        settings: Application settings.

    Returns:
        UserProfileClient: User profile client.
    """
    return UserProfileClient(redis_url=settings.redis_url)


def get_analytics(
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> AnalyticsClient:
    """Get analytics client.

    Args:
        settings: Application settings.

    Returns:
        AnalyticsClient: Analytics client.
    """
    return AnalyticsClient(base_url=settings.vector_store_url)


def get_content_client(
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> ContentClient:
    """Get content client.

    Args:
        settings: Application settings.

    Returns:
        ContentClient: Content client.
    """
    return ContentClient(base_url=settings.vector_store_url)


def get_semantic_search_agent(
    vector_store: VectorStoreClient = Depends(get_vector_store),  # noqa: B008
) -> SemanticSearchAgent:
    """Get semantic search agent.

    Args:
        vector_store: Vector store client.

    Returns:
        SemanticSearchAgent: Semantic search agent.
    """
    return SemanticSearchAgent(vector_store=vector_store)


def get_personalization_agent(
    user_profile: UserProfileClient = Depends(get_user_profile),  # noqa: B008
) -> PersonalizationAgent:
    """Get personalization agent.

    Args:
        user_profile: User profile client.

    Returns:
        PersonalizationAgent: Personalization agent.
    """
    return PersonalizationAgent(user_profile=user_profile)


def get_recommendation_agent(
    content_client: ContentClient = Depends(get_content_client),  # noqa: B008
    user_profile: UserProfileClient = Depends(get_user_profile),  # noqa: B008
) -> RecommendationAgent:
    """Get recommendation agent.

    Args:
        content_client: Content client.
        user_profile: User profile client.

    Returns:
        RecommendationAgent: Recommendation agent.
    """
    return RecommendationAgent(
        content_client=content_client,
        user_profile=user_profile,
    )


def get_trend_detector_agent(
    analytics: AnalyticsClient = Depends(get_analytics),  # noqa: B008
) -> TrendDetectorAgent:
    """Get trend detector agent.

    Args:
        analytics: Analytics client.

    Returns:
        TrendDetectorAgent: Trend detector agent.
    """
    return TrendDetectorAgent(analytics=analytics)


def get_search_explainer_agent() -> SearchExplainerAgent:
    """Get search explainer agent.

    Returns:
        SearchExplainerAgent: Search explainer agent.
    """
    return SearchExplainerAgent()


# Health endpoints


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check(
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> HealthResponse:
    """Health check endpoint.

    Args:
        settings: Application settings.

    Returns:
        HealthResponse: Service health status.
    """
    from datetime import datetime

    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        checks={
            "api": True,
            "redis": True,  # Simplified - would check actual connection
            "vector_store": True,
        },
    )


@router.get("/ready", tags=["health"])
async def readiness_check() -> dict[str, str]:
    """Readiness probe endpoint.

    Returns:
        dict[str, str]: Readiness status.
    """
    return {"status": "ready" }


# Search endpoints


@router.post("/api/v1/search", response_model=SearchResponse, tags=["search"])
async def search(
    request: SearchRequest,
    agent: SemanticSearchAgent = Depends(get_semantic_search_agent),  # noqa: B008
) -> SearchResponse:
    """Perform semantic search.

    Args:
        request: Search request.
        agent: Semantic search agent.

    Returns:
        SearchResponse: Search results.

    Raises:
        HTTPException: If search fails.
    """
    request_id = str(uuid.uuid4())
    logger.info(
        "search_request",
        request_id=request_id,
        query=request.query,
        user_id=request.user_id,
    )

    try:
        response = await agent.run(request)
        logger.info(
            "search_completed",
            request_id=request_id,
            results_count=len(response.results),
            took_ms=response.took_ms,
        )
        return response
    except Exception as exc:
        logger.error("search_failed", request_id=request_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {exc}",
        ) from exc


@router.post("/api/v1/search/explain", response_model=SearchExplanation, tags=["search"])
async def search_with_explanation(
    request: SearchRequest,
    search_agent: SemanticSearchAgent = Depends(get_semantic_search_agent),  # noqa: B008
    explainer_agent: SearchExplainerAgent = Depends(get_search_explainer_agent),  # noqa: B008
) -> SearchExplanation:
    """Perform search and return AI explanation.

    Args:
        request: Search request.
        search_agent: Semantic search agent.
        explainer_agent: Search explainer agent.

    Returns:
        SearchExplanation: Search results with explanation.
    """
    request_id = str(uuid.uuid4())
    logger.info(
        "search_explain_request",
        request_id=request_id,
        query=request.query,
    )

    try:
        search_response = await search_agent.run(request)
        explanation = await explainer_agent.run((request, search_response))
        return explanation
    except Exception as exc:
        logger.error("search_explain_failed", request_id=request_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search explanation failed: {exc}",
        ) from exc


@router.get("/api/v1/search/suggest", tags=["search"])
async def search_suggestions(
    q: str = Query(..., min_length=1, max_length=200, description="Search query prefix"),
    limit: int = Query(default=5, ge=1, le=20),
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> dict[str, Any]:
    """Get search suggestions for autocomplete.

    Args:
        q: Search query prefix.
        limit: Maximum suggestions.
        settings: Application settings.

    Returns:
        dict[str, Any]: Search suggestions.
    """
    # Simplified implementation - would integrate with search analytics
    suggestions = [
        f"{q} tutorial",
        f"{q} examples",
        f"{q} best practices",
        f"{q} guide",
        f"{q} overview",
    ][:limit]

    return {"query": q, "suggestions": suggestions}


# Recommendation endpoints


@router.post(
    "/api/v1/recommendations",
    response_model=RecommendationResponse,
    tags=["recommendations"],
)
async def get_recommendations(
    request: RecommendationRequest,
    agent: RecommendationAgent = Depends(get_recommendation_agent),  # noqa: B008
) -> RecommendationResponse:
    """Get personalized content recommendations.

    Args:
        request: Recommendation request.
        agent: Recommendation agent.

    Returns:
        RecommendationResponse: Content recommendations.

    Raises:
        HTTPException: If recommendation generation fails.
    """
    request_id = str(uuid.uuid4())
    logger.info(
        "recommendation_request",
        request_id=request_id,
        user_id=request.user_id,
    )

    try:
        response = await agent.run(request)
        logger.info(
            "recommendation_completed",
            request_id=request_id,
            recs_count=len(response.recommendations),
        )
        return response
    except Exception as exc:
        logger.error("recommendation_failed", request_id=request_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation failed: {exc}",
        ) from exc


@router.get(
    "/api/v1/recommendations/{user_id}",
    response_model=RecommendationResponse,
    tags=["recommendations"],
)
async def get_user_recommendations(
    user_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    context: str | None = Query(None),
    agent: RecommendationAgent = Depends(get_recommendation_agent),  # noqa: B008
) -> RecommendationResponse:
    """Get recommendations for a specific user.

    Args:
        user_id: User identifier.
        limit: Maximum recommendations.
        context: Optional context.
        agent: Recommendation agent.

    Returns:
        RecommendationResponse: User recommendations.
    """
    request = RecommendationRequest(
        user_id=user_id,
        context=context,
        limit=limit,
    )
    return await agent.run(request)


# Trend endpoints


@router.post("/api/v1/trends", response_model=TrendResponse, tags=["trends"])
async def detect_trends(
    request: TrendRequest,
    agent: TrendDetectorAgent = Depends(get_trend_detector_agent),  # noqa: B008
) -> TrendResponse:
    """Detect trends from analytics data.

    Args:
        request: Trend detection request.
        agent: Trend detector agent.

    Returns:
        TrendResponse: Detected trends.

    Raises:
        HTTPException: If trend detection fails.
    """
    request_id = str(uuid.uuid4())
    logger.info("trend_request", request_id=request_id, topics=request.topics)

    try:
        response = await agent.run(request)
        logger.info(
            "trend_detection_completed",
            request_id=request_id,
            trends_count=len(response.trends),
        )
        return response
    except Exception as exc:
        logger.error("trend_detection_failed", request_id=request_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trend detection failed: {exc}",
        ) from exc


@router.get("/api/v1/trends", response_model=TrendResponse, tags=["trends"])
async def get_trends(
    window_days: int = Query(default=7, ge=1, le=30),
    limit: int = Query(default=10, ge=1, le=50),
    agent: TrendDetectorAgent = Depends(get_trend_detector_agent),  # noqa: B008
) -> TrendResponse:
    """Get current trends.

    Args:
        window_days: Analysis window in days.
        limit: Maximum trends.
        agent: Trend detector agent.

    Returns:
        TrendResponse: Current trends.
    """
    request = TrendRequest(
        topics=[],
        window_days=window_days,
        limit=limit,
    )
    return await agent.run(request)


# Personalization endpoints


@router.get("/api/v1/users/{user_id}/profile", tags=["personalization"])
async def get_user_profile(
    user_id: str,
    user_profile: UserProfileClient = Depends(get_user_profile),  # noqa: B008
) -> dict[str, Any]:
    """Get user profile and preferences.

    Args:
        user_id: User identifier.
        user_profile: User profile client.

    Returns:
        dict[str, Any]: User profile data.
    """
    try:
        history = await user_profile.get_history(user_id=user_id, limit=50)
        return {
            "user_id": user_id,
            "history_count": len(history),
            "preferences": {
                "topics": list(set(tag for item in history for tag in item.get("tags", [])))[:10],
                "content_types": list(
                    set(item.get("content_type", "article") for item in history)
                )[:5],
            },
        }
    except Exception as exc:
        logger.error("get_profile_failed", user_id=user_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user profile: {exc}",
        ) from exc


@router.post("/api/v1/users/{user_id}/history", tags=["personalization"])
async def add_user_history(
    user_id: str,
    item: dict[str, Any],
    user_profile: UserProfileClient = Depends(get_user_profile),  # noqa: B008
) -> dict[str, str]:
    """Add an item to user's history.

    Args:
        user_id: User identifier.
        item: History item.
        user_profile: User profile client.

    Returns:
        dict[str, str]: Status message.
    """
    try:
        success = await user_profile.add_history(user_id=user_id, item=item)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add history item",
            )
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("add_history_failed", user_id=user_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add history: {exc}",
        ) from exc


# Metrics endpoint


@router.get("/metrics", tags=["metrics"])
async def metrics(
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> dict[str, Any]:
    """Get service metrics.

    Args:
        settings: Application settings.

    Returns:
        dict[str, Any]: Service metrics.
    """
    if not settings.enable_metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metrics disabled",
        )

    # Simplified metrics - would integrate with prometheus_client
    return {
        "requests_total": 0,
        "request_duration_seconds": 0.0,
        "search_requests_total": 0,
        "recommendation_requests_total": 0,
        "trend_requests_total": 0,
    }
