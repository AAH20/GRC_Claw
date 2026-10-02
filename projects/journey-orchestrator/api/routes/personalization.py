"""Personalization API endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status

from api.models import PersonalizeRequest, PersonalizeResponse
from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/personalize", response_model=PersonalizeResponse)
async def personalize(request: PersonalizeRequest) -> PersonalizeResponse:
    """Generate personalized content for a customer.

    Args:
        request: The personalization request.

    Returns:
        Personalized content and recommendations.
    """
    try:
        # In production, this would call the PersonalizationEngineAgent
        logger.info(
            "personalization_requested",
            customer_id=request.customer_id,
            channel=request.channel,
        )

        return PersonalizeResponse(
            customer_id=request.customer_id,
            contents=[
                {
                    "channel": request.channel.value if request.channel else "email",
                    "subject": "Your personalized recommendation",
                    "body": f"Hi {request.customer_profile.get('name', 'there')}, we have something special for you!",
                    "call_to_action": "Learn More",
                    "personalization_tokens": {"name": request.customer_profile.get("name", "")},
                }
            ],
            recommended_offers=["offer_1", "offer_2"],
            next_best_action="send_email",
            confidence_score=0.85,
        )

    except Exception as e:
        logger.error("personalization_failed", customer_id=request.customer_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Personalization failed: {e}",
        ) from e
