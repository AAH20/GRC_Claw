"""License API routes."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request

from rights_management.agents.license_detector import LicenseDetectorAgent
from rights_management.integrations.storage import InMemoryStorage
from rights_management.models import (
    License,
    LicenseCreate,
    LicenseDetectionRequest,
    LicenseDetectionResult,
    LicenseStatus,
)

router = APIRouter()


def get_storage(request: Request) -> InMemoryStorage:
    """Dependency to retrieve the storage backend from app state.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The InMemoryStorage instance.
    """
    return request.app.state.storage


def get_agent(request: Request) -> LicenseDetectorAgent:
    """Dependency to retrieve the license detector agent.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The LicenseDetectorAgent instance.
    """
    if not hasattr(request.app.state, "license_detector_agent"):
        request.app.state.license_detector_agent = LicenseDetectorAgent()
    return request.app.state.license_detector_agent


@router.post("", response_model=License, status_code=201)
async def create_license(
    payload: LicenseCreate,
    storage: InMemoryStorage = Depends(get_storage),  # noqa: B008
) -> License:
    """Create a new content license.

    Args:
        payload: The license creation data.
        storage: The storage backend.

    Returns:
        The newly created License.
    """
    license_obj = License(
        id=str(uuid.uuid4()),
        content_id=payload.content_id,
        license_type=payload.license_type,
        holder=payload.holder,
        status=LicenseStatus.ACTIVE,
        created_at=datetime.now(tz=UTC),
        expires_at=payload.expires_at,
        terms=payload.terms,
        metadata=payload.metadata,
    )
    await storage.save_license(license_obj)
    return license_obj


@router.get("", response_model=list[License])
async def list_licenses(
    content_id: str | None = None,
    status: LicenseStatus | None = None,
    storage: InMemoryStorage = Depends(get_storage),  # noqa: B008
) -> list[License]:
    """List all licenses, optionally filtered.

    Args:
        content_id: Filter by content identifier.
        status: Filter by license status.
        storage: The storage backend.

    Returns:
        List of matching licenses.
    """
    licenses = await storage.list_licenses(content_id=content_id, status=status)
    return licenses


@router.get("/{license_id}", response_model=License)
async def get_license(
    license_id: str,
    storage: InMemoryStorage = Depends(get_storage),  # noqa: B008
) -> License:
    """Retrieve a specific license by ID.

    Args:
        license_id: The license identifier.
        storage: The storage backend.

    Returns:
        The requested License.

    Raises:
        HTTPException: If the license is not found.
    """
    license_obj = await storage.get_license(license_id)
    if license_obj is None:
        raise HTTPException(status_code=404, detail="License not found")
    return license_obj


@router.post("/detect", response_model=LicenseDetectionResult)
async def detect_license(
    payload: LicenseDetectionRequest,
    agent: LicenseDetectorAgent = Depends(get_agent),  # noqa: B008
) -> LicenseDetectionResult:
    """Detect the license for a piece of content.

    Args:
        payload: The detection request.
        agent: The license detector agent.

    Returns:
        The detection result.
    """
    result = await agent.run(payload)
    return result


@router.delete("/{license_id}", status_code=204)
async def revoke_license(
    license_id: str,
    storage: InMemoryStorage = Depends(get_storage),  # noqa: B008
) -> None:
    """Revoke a license.

    Args:
        license_id: The license identifier.
        storage: The storage backend.

    Raises:
        HTTPException: If the license is not found.
    """
    license_obj = await storage.get_license(license_id)
    if license_obj is None:
        raise HTTPException(status_code=404, detail="License not found")
    license_obj.status = LicenseStatus.REVOKED
    await storage.save_license(license_obj)
