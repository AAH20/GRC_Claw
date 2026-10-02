"""Violation management API endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/violations", tags=["violations"])


class Severity(StrEnum):
    """Violation severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ViolationStatus(StrEnum):
    """Lifecycle status of a violation."""

    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ViolationCreate(BaseModel):
    """Payload for reporting a violation."""

    content_id: str
    source: str
    rule: str
    severity: Severity = Severity.MEDIUM
    description: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    excerpt: str = ""


class Violation(ViolationCreate):
    """A persisted compliance violation."""

    id: str
    status: ViolationStatus = ViolationStatus.OPEN
    detected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = None
    resolution: str | None = None


class ResolvePayload(BaseModel):
    """Payload for resolving a violation."""

    resolution: str = Field(..., min_length=1, max_length=2048)
    status: ViolationStatus = ViolationStatus.RESOLVED


_VIOLATIONS: dict[str, Violation] = {}


@router.get("", response_model=list[Violation])
async def list_violations(
    severity: Severity | None = None,
    violation_status: ViolationStatus | None = None,
    source: str | None = None,
) -> list[Violation]:
    """List violations with optional filters."""
    violations = list(_VIOLATIONS.values())
    if severity is not None:
        violations = [v for v in violations if v.severity is severity]
    if violation_status is not None:
        violations = [v for v in violations if v.status is violation_status]
    if source is not None:
        violations = [v for v in violations if v.source == source]
    return violations


@router.post("", response_model=Violation, status_code=status.HTTP_201_CREATED)
async def create_violation(payload: ViolationCreate) -> Violation:
    """Report a new violation."""
    violation_id = f"vio_{len(_VIOLATIONS) + 1:04d}"
    violation = Violation(id=violation_id, **payload.model_dump())
    _VIOLATIONS[violation_id] = violation
    return violation


@router.get("/{violation_id}", response_model=Violation)
async def get_violation(violation_id: str) -> Violation:
    """Fetch a single violation by id."""
    violation = _VIOLATIONS.get(violation_id)
    if violation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="violation not found")
    return violation


async def _resolve(violation_id: str, payload: ResolvePayload) -> Violation:
    """Shared resolution logic for the PUT/POST aliases."""
    violation = _VIOLATIONS.get(violation_id)
    if violation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="violation not found")
    violation.status = payload.status
    violation.resolution = payload.resolution
    violation.resolved_at = datetime.now(UTC)
    return violation


@router.put("/{violation_id}/resolve", response_model=Violation)
async def resolve_violation(violation_id: str, payload: ResolvePayload) -> Violation:
    """Resolve a violation via PUT."""
    return await _resolve(violation_id, payload)


@router.post("/{violation_id}/resolve", response_model=Violation)
async def resolve_violation_post(violation_id: str, payload: ResolvePayload) -> Violation:
    """Resolve a violation via POST."""
    return await _resolve(violation_id, payload)


def reset_store() -> None:
    """Clear the in-memory violation store (used by tests)."""
    _VIOLATIONS.clear()


def seed_violations(entries: list[dict[str, Any]]) -> None:
    """Seed the in-memory store with violations."""
    for entry in entries:
        violation_id = entry.get("id") or f"vio_{len(_VIOLATIONS) + 1:04d}"
        _VIOLATIONS[violation_id] = Violation(id=violation_id, **entry)
