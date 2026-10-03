"""Candidate service for recruitment platform."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from recruitment_platform.models.candidate import Candidate
from recruitment_platform.schemas.candidate import CandidateCreate, CandidateFilters, PaginationParams


class CandidateServiceError(Exception):
    """Base exception for candidate service errors."""


class CandidateNotFoundError(CandidateServiceError):
    """Raised when a candidate is not found."""


class CandidateValidationError(CandidateServiceError):
    """Raised when candidate data fails validation."""


def create_candidate(data: Dict[str, Any], db: Session) -> Candidate:
    """Create a new candidate with validation.

    Args:
        data: Candidate data dictionary.
        db: Database session.

    Returns:
        The created Candidate instance.

    Raises:
        CandidateValidationError: If data validation fails.
        CandidateServiceError: If database operation fails.
    """
    try:
        candidate_data = CandidateCreate(**data)
    except Exception as exc:
        raise CandidateValidationError(f"Invalid candidate data: {exc}") from exc

    try:
        candidate = Candidate(**candidate_data.model_dump())
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        return candidate
    except SQLAlchemyError as exc:
        db.rollback()
        raise CandidateServiceError(f"Failed to create candidate: {exc}") from exc


def get_candidate(candidate_id: int, db: Session) -> Candidate:
    """Get a candidate by ID.

    Args:
        candidate_id: The candidate's unique identifier.
        db: Database session.

    Returns:
        The Candidate instance.

    Raises:
        CandidateNotFoundError: If candidate is not found.
        CandidateServiceError: If database operation fails.
    """
    try:
        candidate = db.execute(
            select(Candidate).where(Candidate.id == candidate_id)
        ).scalar_one_or_none()
    except SQLAlchemyError as exc:
        raise CandidateServiceError(f"Failed to fetch candidate: {exc}") from exc

    if candidate is None:
        raise CandidateNotFoundError(f"Candidate with id {candidate_id} not found")

    return candidate


def list_candidates(
    filters: Optional[Dict[str, Any]] = None,
    pagination: Optional[Dict[str, Any]] = None,
    db: Session = None,
) -> Dict[str, Any]:
    """List candidates with filtering and pagination.

    Args:
        filters: Optional filter criteria (e.g., {"status": "active", "skill": "python"}).
        pagination: Optional pagination params (e.g., {"page": 1, "page_size": 20}).
        db: Database session.

    Returns:
        Dictionary with 'items' (list of candidates), 'total', 'page', 'page_size'.

    Raises:
        CandidateServiceError: If database operation fails.
    """
    filters = filters or {}
    pagination = pagination or {}

    try:
        filter_params = CandidateFilters(**filters)
        page_params = PaginationParams(**pagination)
    except Exception as exc:
        raise CandidateValidationError(f"Invalid filter or pagination data: {exc}") from exc

    try:
        query = select(Candidate)

        if filter_params.status is not None:
            query = query.where(Candidate.status == filter_params.status)
        if filter_params.skill is not None:
            query = query.where(Candidate.skills.contains([filter_params.skill]))
        if filter_params.location is not None:
            query = query.where(Candidate.location == filter_params.location)

        total = db.execute(
            select(Candidate.id).where(query.whereclause)
        ).scalars().all()
        total_count = len(total)

        offset = (page_params.page - 1) * page_params.page_size
        query = query.offset(offset).limit(page_params.page_size)

        items = db.execute(query).scalars().all()

        return {
            "items": list(items),
            "total": total_count,
            "page": page_params.page,
            "page_size": page_params.page_size,
        }
    except SQLAlchemyError as exc:
        raise CandidateServiceError(f"Failed to list candidates: {exc}") from exc
