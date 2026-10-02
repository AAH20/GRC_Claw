"""Commission API routes for the Broker Enablement platform."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException, status

from broker_enablement.agents.commission_tracking import (
    CommissionCalculationRequest,
    CommissionRecord,
    CommissionTrackingAgent,
)

logger = structlog.get_logger(__name__)

router = APIRouter()

# Agent instance (in production, use dependency injection)
_commission_agent = CommissionTrackingAgent()


@router.post(
    "/calculate",
    response_model=CommissionRecord,
    status_code=status.HTTP_201_CREATED,
    summary="Calculate commission for a transaction",
)
async def calculate_commission(
    request: CommissionCalculationRequest,
) -> CommissionRecord:
    """Calculate commission for a transaction.

    Args:
        request: Commission calculation request.

    Returns:
        CommissionRecord with calculated commission details.

    Raises:
        HTTPException: If calculation fails.
    """
    try:
        result = await _commission_agent.calculate_commission(request)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.get(
    "/{partner_id}",
    response_model=list[CommissionRecord],
    summary="Get commission records for a partner",
)
async def get_partner_commissions(
    partner_id: str, status_filter: str | None = None
) -> list[CommissionRecord]:
    """Get commission records for a partner.

    Args:
        partner_id: The partner ID.
        status_filter: Optional status filter.

    Returns:
        List of CommissionRecord objects.

    Raises:
        HTTPException: If fetching fails.
    """
    try:
        records = await _commission_agent.get_partner_commissions(
            partner_id, status_filter
        )
        return records
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e


@router.post(
    "/{commission_id}/payout",
    response_model=dict,
    summary="Process payout for a commission",
)
async def process_payout(commission_id: str) -> dict:
    """Process payout for a commission via Stripe.

    Args:
        commission_id: The commission ID.

    Returns:
        Payout result dictionary.

    Raises:
        HTTPException: If payout processing fails.
    """
    try:
        result = await _commission_agent.process_payout(commission_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e
