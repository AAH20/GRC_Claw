"""Royalty calculation endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from licensing_engine.agents import AgentContext, RoyaltyCalculatorAgent
from licensing_engine.config.settings import Settings, get_settings
from licensing_engine.models import (
    RoyaltyCalculation,
    RoyaltyCalculationCreate,
    RoyaltyCalculationResponse,
)

router = APIRouter()

# In-memory store for demo purposes
_calculations: dict[UUID, RoyaltyCalculation] = {}


@router.post(
    "/calculate",
    response_model=RoyaltyCalculationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Calculate royalties",
)
async def calculate_royalties(
    data: RoyaltyCalculationCreate,
    settings: Settings = Depends(get_settings),
) -> RoyaltyCalculationResponse:
    """Calculate royalties using the RoyaltyCalculatorAgent.

    Args:
        data: The royalty calculation request data.
        settings: Application settings.

    Returns:
        The royalty calculation result.
    """
    context = AgentContext(settings=settings)
    agent = RoyaltyCalculatorAgent(context)
    result = await agent.execute(data.model_dump(mode="json"))

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.error or "Failed to calculate royalties",
        )

    calculation = RoyaltyCalculation(
        license_id=data.license_id,
        usage_count=data.usage_count,
        revenue=data.revenue,
        currency=data.currency,
        total_royalty=result.data.get("total_royalty", 0.0),
        breakdown=result.data.get("breakdown", []),
    )
    _calculations[calculation.id] = calculation
    return RoyaltyCalculationResponse(
        calculation=calculation, message="Royalty calculation completed"
    )


@router.get(
    "/{calculation_id}",
    response_model=RoyaltyCalculationResponse,
    summary="Get a royalty calculation by ID",
)
async def get_calculation(calculation_id: UUID) -> RoyaltyCalculationResponse:
    """Get a specific royalty calculation by its ID.

    Args:
        calculation_id: The calculation ID.

    Returns:
        The requested royalty calculation.

    Raises:
        HTTPException: If the calculation is not found.
    """
    calculation = _calculations.get(calculation_id)
    if not calculation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Royalty calculation {calculation_id} not found",
        )
    return RoyaltyCalculationResponse(calculation=calculation)


@router.get(
    "/license/{license_id}",
    response_model=list[RoyaltyCalculation],
    summary="Get royalty calculations for a license",
)
async def get_license_calculations(license_id: UUID) -> list[RoyaltyCalculation]:
    """Get all royalty calculations for a specific license.

    Args:
        license_id: The license ID.

    Returns:
        List of royalty calculations for the license.
    """
    return [
        c for c in _calculations.values() if c.license_id == license_id
    ]
