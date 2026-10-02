"""License management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from licensing_engine.agents import AgentContext, LicenseGeneratorAgent
from licensing_engine.config.settings import Settings, get_settings
from licensing_engine.models import (
    License,
    LicenseCreate,
    LicenseListResponse,
    LicenseResponse,
    LicenseStatus,
    LicenseUpdate,
)

router = APIRouter()

# In-memory store for demo purposes
_licenses: dict[UUID, License] = {}


@router.post(
    "",
    response_model=LicenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new license",
)
async def create_license(
    data: LicenseCreate,
    settings: Settings = Depends(get_settings),
) -> LicenseResponse:
    """Create a new license using the LicenseGeneratorAgent.

    Args:
        data: The license creation data.
        settings: Application settings.

    Returns:
        The created license.
    """
    context = AgentContext(settings=settings)
    agent = LicenseGeneratorAgent(context)
    result = await agent.execute(data.model_dump(mode="json"))

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error or "Failed to generate license",
        )

    license_obj = License(
        content_id=data.content_id,
        content_type=data.content_type,
        license_type=data.license_type,
        licensor_id=data.licensor_id,
        licensee_id=data.licensee_id,
        terms=data.terms,
        status=LicenseStatus.DRAFT,
        metadata=result.data,
    )
    _licenses[license_obj.id] = license_obj
    return LicenseResponse(license=license_obj, message="License created successfully")


@router.get(
    "",
    response_model=LicenseListResponse,
    summary="List all licenses",
)
async def list_licenses(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Page size"),
    status_filter: LicenseStatus | None = Query(default=None, description="Filter by status"),
) -> LicenseListResponse:
    """List all licenses with optional filtering and pagination.

    Args:
        page: Page number.
        page_size: Number of items per page.
        status_filter: Optional status filter.

    Returns:
        Paginated list of licenses.
    """
    all_licenses = list(_licenses.values())
    if status_filter:
        all_licenses = [lic for lic in all_licenses if lic.status == status_filter]

    total = len(all_licenses)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = all_licenses[start:end]

    return LicenseListResponse(
        licenses=paginated, total=total, page=page, page_size=page_size
    )


@router.get(
    "/{license_id}",
    response_model=LicenseResponse,
    summary="Get a license by ID",
)
async def get_license(license_id: UUID) -> LicenseResponse:
    """Get a specific license by its ID.

    Args:
        license_id: The license ID.

    Returns:
        The requested license.

    Raises:
        HTTPException: If the license is not found.
    """
    license_obj = _licenses.get(license_id)
    if not license_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"License {license_id} not found",
        )
    return LicenseResponse(license=license_obj)


@router.patch(
    "/{license_id}",
    response_model=LicenseResponse,
    summary="Update a license",
)
async def update_license(
    license_id: UUID, data: LicenseUpdate
) -> LicenseResponse:
    """Update an existing license.

    Args:
        license_id: The license ID.
        data: The update data.

    Returns:
        The updated license.

    Raises:
        HTTPException: If the license is not found.
    """
    license_obj = _licenses.get(license_id)
    if not license_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"License {license_id} not found",
        )

    if data.terms is not None:
        license_obj.terms = data.terms
    if data.status is not None:
        license_obj.status = data.status
    if data.metadata is not None:
        license_obj.metadata.update(data.metadata)

    return LicenseResponse(license=license_obj, message="License updated successfully")


@router.delete(
    "/{license_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a license",
)
async def delete_license(license_id: UUID) -> None:
    """Delete a license.

    Args:
        license_id: The license ID.

    Raises:
        HTTPException: If the license is not found.
    """
    if license_id not in _licenses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"License {license_id} not found",
        )
    del _licenses[license_id]


@router.post(
    "/{license_id}/activate",
    response_model=LicenseResponse,
    summary="Activate a license",
)
async def activate_license(license_id: UUID) -> LicenseResponse:
    """Activate a draft license.

    Args:
        license_id: The license ID.

    Returns:
        The activated license.

    Raises:
        HTTPException: If the license is not found.
    """
    license_obj = _licenses.get(license_id)
    if not license_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"License {license_id} not found",
        )
    license_obj.status = LicenseStatus.ACTIVE
    return LicenseResponse(license=license_obj, message="License activated")


@router.post(
    "/{license_id}/revoke",
    response_model=LicenseResponse,
    summary="Revoke a license",
)
async def revoke_license(license_id: UUID) -> LicenseResponse:
    """Revoke an active license.

    Args:
        license_id: The license ID.

    Returns:
        The revoked license.

    Raises:
        HTTPException: If the license is not found.
    """
    license_obj = _licenses.get(license_id)
    if not license_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"License {license_id} not found",
        )
    license_obj.status = LicenseStatus.REVOKED
    return LicenseResponse(license=license_obj, message="License revoked")
