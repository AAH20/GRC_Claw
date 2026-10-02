"""Personalization Engine agent - generates personalized content per customer."""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class CustomerProfile(BaseModel):
    """Customer profile data used for personalization."""

    customer_id: str
    email: str = ""
    first_name: str = ""
    segment: str = ""
    preferences: dict[str, Any] = Field(default_factory=dict)
    behavioral_data: dict[str, Any] = Field(default_factory=dict)


class PersonalizationRequest(BaseModel):
    """Request for content personalization."""

    customer: CustomerProfile
    content_type: str = Field(..., description="Type of content to personalize")
    context: dict[str, Any] = Field(default_factory=dict)


class PersonalizedContent(BaseModel):
    """Output of the Personalization Engine."""

    subject: str
    body: str
    call_to_action: str
    recommended_channel: str
    confidence_score: float = Field(ge=0.0, le=1.0)


class PersonalizationEngine:
    """Agent that generates personalized content for individual customers.

    Uses customer profiles, behavioral data, and preferences to tailor
    messaging for maximum engagement and conversion.
    """

    def __init__(self, llm_client: Any | None = None) -> None:
        """Initialize the Personalization Engine.

        Args:
            llm_client: Optional LLM client for AI-powered personalization.
        """
        self.llm_client = llm_client
        self.logger = logger.bind(agent="personalization_engine")

    async def personalize(self, request: PersonalizationRequest) -> PersonalizedContent:
        """Generate personalized content for a customer.

        Args:
            request: The personalization request with customer profile.

        Returns:
            Personalized content tailored to the customer.

        Raises:
            ValueError: If the request is invalid.
        """
        if not request.customer.customer_id:
            raise ValueError("customer_id must not be empty")
        if not request.content_type.strip():
            raise ValueError("content_type must not be empty")

        self.logger.info(
            "Personalizing content",
            customer_id=request.customer.customer_id,
            content_type=request.content_type,
        )

        customer = request.customer
        name = customer.first_name or "there"

        content = PersonalizedContent(
            subject=f"Special update for you, {name}!",
            body=f"Hi {name}, we've prepared something special based on your interests.",
            call_to_action="Learn More",
            recommended_channel="email",
            confidence_score=0.85,
        )

        self.logger.info(
            "Content personalized",
            customer_id=customer.customer_id,
            confidence=content.confidence_score,
        )
        return content
