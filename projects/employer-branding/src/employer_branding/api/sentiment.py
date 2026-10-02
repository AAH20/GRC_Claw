"""Sentiment analysis endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from employer_branding.agents.sentiment_analyzer import SentimentAnalyzerAgent
from employer_branding.models import SentimentAnalysisRequest, SentimentReport

router = APIRouter(prefix="/api/v1/sentiment", tags=["sentiment"])

# In-memory store
_sentiment_store: dict[UUID, SentimentReport] = {}


def get_sentiment_agent() -> SentimentAnalyzerAgent:
    """Dependency to get sentiment analyzer agent."""
    return SentimentAnalyzerAgent()


@router.post("/analyze", response_model=SentimentReport, status_code=status.HTTP_201_CREATED)
async def analyze_sentiment(
    request: SentimentAnalysisRequest,
    agent: SentimentAnalyzerAgent = Depends(get_sentiment_agent),
) -> SentimentReport:
    """Analyze sentiment of text.

    Args:
        request: Sentiment analysis request.
        agent: Sentiment analyzer agent.

    Returns:
        SentimentReport with detailed analysis.

    Raises:
        HTTPException: If analysis fails.
    """
    try:
        report = await agent.run(request)
        _sentiment_store[report.id] = report
        return report
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sentiment analysis failed: {exc}",
        ) from exc


@router.get("/{report_id}", response_model=SentimentReport)
async def get_sentiment_report(report_id: UUID) -> SentimentReport:
    """Get a sentiment report by ID.

    Args:
        report_id: Report UUID.

    Returns:
        SentimentReport if found.

    Raises:
        HTTPException: If report not found.
    """
    if report_id not in _sentiment_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sentiment report {report_id} not found",
        )
    return _sentiment_store[report_id]


@router.post("/batch", response_model=list[SentimentReport], status_code=status.HTTP_201_CREATED)
async def batch_analyze(
    texts: list[str],
    agent: SentimentAnalyzerAgent = Depends(get_sentiment_agent),
) -> list[SentimentReport]:
    """Analyze sentiment of multiple texts.

    Args:
        texts: List of texts to analyze.
        agent: Sentiment analyzer agent.

    Returns:
        List of SentimentReport objects.

    Raises:
        HTTPException: If batch analysis fails.
    """
    try:
        results = []
        for text in texts:
            request = SentimentAnalysisRequest(
                text=text,
                analyze_aspects=True,
                detect_emotions=True,
            )
            report = await agent.run(request)
            _sentiment_store[report.id] = report
            results.append(report)
        return results
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch sentiment analysis failed: {exc}",
        ) from exc
