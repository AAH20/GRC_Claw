"""Review analysis endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from employer_branding.agents.review_analyzer import ReviewAnalyzerAgent
from employer_branding.models import Review, ReviewFetchRequest

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])

# In-memory store
_review_store: dict[UUID, Review] = {}


def get_review_agent() -> ReviewAnalyzerAgent:
    """Dependency to get review analyzer agent."""
    return ReviewAnalyzerAgent()


@router.post("/fetch", response_model=list[Review], status_code=status.HTTP_201_CREATED)
async def fetch_reviews(
    request: ReviewFetchRequest,
    agent: ReviewAnalyzerAgent = Depends(get_review_agent),
) -> list[Review]:
    """Fetch and analyze reviews for a company.

    Args:
        request: Review fetch request.
        agent: Review analyzer agent.

    Returns:
        List of analyzed Review objects.

    Raises:
        HTTPException: If fetching fails.
    """
    try:
        reviews = await agent.run(request)
        for review in reviews:
            _review_store[review.id] = review
        return reviews
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Review fetching failed: {exc}",
        ) from exc


@router.get("/{review_id}", response_model=Review)
async def get_review(review_id: UUID) -> Review:
    """Get a review by ID.

    Args:
        review_id: Review UUID.

    Returns:
        Review if found.

    Raises:
        HTTPException: If review not found.
    """
    if review_id not in _review_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review {review_id} not found",
        )
    return _review_store[review_id]


@router.get("/", response_model=list[Review])
async def list_reviews(
    company_name: str | None = None,
    source: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Review]:
    """List reviews with optional filtering.

    Args:
        company_name: Filter by company name.
        source: Filter by review source.
        skip: Number of items to skip.
        limit: Maximum items to return.

    Returns:
        List of Review objects.
    """
    reviews = list(_review_store.values())

    if company_name:
        reviews = [
            r for r in reviews
            if r.metadata.get("company_name", "").lower() == company_name.lower()
        ]
    if source:
        reviews = [r for r in reviews if r.source.value == source]

    return reviews[skip : skip + limit]


@router.get("/summary/{company_name}")
async def get_review_summary(company_name: str) -> dict:
    """Get summary statistics for a company's reviews.

    Args:
        company_name: Company name.

    Returns:
        Dictionary with summary statistics.
    """
    reviews = [
        r for r in _review_store.values()
        if r.metadata.get("company_name", "").lower() == company_name.lower()
    ]

    if not reviews:
        return {
            "company_name": company_name,
            "total_reviews": 0,
            "average_rating": 0.0,
            "recommendation_rate": 0.0,
        }

    total = len(reviews)
    avg_rating = sum(r.rating for r in reviews) / total
    recommended = sum(1 for r in reviews if r.is_recommended)

    return {
        "company_name": company_name,
        "total_reviews": total,
        "average_rating": round(avg_rating, 2),
        "recommendation_rate": round(recommended / total * 100, 1),
    }
