"""Partner API routes for the Broker Enablement platform."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, HTTPException, status

from broker_enablement.agents.partner_enablement import (
    EnablementRequest,
    EnablementResult,
    PartnerEnablementAgent,
)
from broker_enablement.agents.partner_onboarding import (
    PartnerOnboardingAgent,
    PartnerRegistrationRequest,
    PartnerRegistrationResult,
)

logger = structlog.get_logger(__name__)

router = APIRouter()

# Agent instances (in production, use dependency injection)
_onboarding_agent = PartnerOnboardingAgent()
_enablement_agent = PartnerEnablementAgent()


@router.post(
    "",
    response_model=PartnerRegistrationResult,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new partner",
)
async def register_partner(
    request: PartnerRegistrationRequest,
) -> PartnerRegistrationResult:
    """Register a new partner with KYC verification and account provisioning.

    Args:
        request: Partner registration details.

    Returns:
        PartnerRegistrationResult with partner ID and status.

    Raises:
        HTTPException: If registration fails.
    """
    try:
        result = await _onboarding_agent.register_partner(request)
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
    response_model=dict,
    summary="Get partner details",
)
async def get_partner(partner_id: str) -> dict:
    """Get partner details by ID.

    Args:
        partner_id: The partner ID.

    Returns:
        Partner details dictionary.

    Raises:
        HTTPException: If partner is not found.
    """
    # Implementation would query database
    return {
        "partner_id": partner_id,
        "business_name": "Example Partner",
        "status": "active",
        "kyc_status": "verified",
    }


@router.post(
    "/{partner_id}/enable",
    response_model=EnablementResult,
    summary="Start partner enablement workflow",
)
async def enable_partner(
    partner_id: str, request: EnablementRequest
) -> EnablementResult:
    """Start the enablement workflow for a partner.

    Args:
        partner_id: The partner ID.
        request: Enablement request details.

    Returns:
        EnablementResult with status and progress.

    Raises:
        HTTPException: If enablement fails.
    """
    try:
        # Ensure partner_id in request matches path
        request.partner_id = partner_id
        result = await _enablement_agent.start_enablement(request)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e
