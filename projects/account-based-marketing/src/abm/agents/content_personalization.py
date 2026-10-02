"""Content Personalization Agent for generating tailored content per account."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class ContentType(str, Enum):
    """Types of content that can be personalized."""

    EMAIL = "email"
    LANDING_PAGE = "landing_page"
    AD_COPY = "ad_copy"
    SOCIAL_POST = "social_post"
    DIRECT_MAIL = "direct_mail"
    CASE_STUDY = "case_study"
    WHITEPAPER = "whitepaper"


class PersonaType(str, Enum):
    """Target persona types for content personalization."""

    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    PRACTITIONER = "practitioner"
    ECONOMIC = "economic"


@dataclass
class PersonalizedContent:
    """Represents generated personalized content."""

    content_id: str
    account_id: str
    content_type: ContentType
    persona: PersonaType
    subject: str
    body: str
    call_to_action: str
    personalization_factors: dict[str, Any] = field(default_factory=dict)


class ContentPersonalizationAgent:
    """Generates personalized content for target accounts and personas.

    This agent uses account data, intent signals, and committee information
    to create tailored content that resonates with specific accounts and
    individual stakeholders.
    """

    def __init__(self, model: str = "gpt-4") -> None:
        """Initialize the Content Personalization Agent.

        Args:
            model: The LLM model to use for content generation.
        """
        self.model = model
        logger.info("ContentPersonalizationAgent initialized", model=model)

    async def generate_content(
        self,
        account_id: str,
        content_type: ContentType,
        persona: PersonaType,
        context: dict[str, Any] | None = None,
    ) -> PersonalizedContent:
        """Generate personalized content for an account.

        Args:
            account_id: The target account identifier.
            content_type: The type of content to generate.
            persona: The target persona for personalization.
            context: Optional additional context for personalization.

        Returns:
            PersonalizedContent object with generated content.

        Raises:
            ValueError: If account_id is empty or content_type is invalid.
        """
        if not account_id:
            raise ValueError("account_id cannot be empty")

        logger.info(
            "Generating personalized content",
            account_id=account_id,
            content_type=content_type.value,
            persona=persona.value,
        )

        # In production, this would use LLM with account context
        content = self._generate_mock_content(account_id, content_type, persona, context)

        logger.info(
            "Content generation complete",
            account_id=account_id,
            content_id=content.content_id,
        )
        return content

    async def generate_campaign_content(
        self,
        account_ids: list[str],
        content_type: ContentType,
        campaign_context: dict[str, Any],
    ) -> list[PersonalizedContent]:
        """Generate personalized content for multiple accounts.

        Args:
            account_ids: List of target account identifiers.
            content_type: The type of content to generate.
            campaign_context: Campaign-specific context and messaging.

        Returns:
            List of PersonalizedContent objects.
        """
        if not account_ids:
            raise ValueError("account_ids cannot be empty")

        logger.info(
            "Generating campaign content",
            account_count=len(account_ids),
            content_type=content_type.value,
        )

        results: list[PersonalizedContent] = []
        for account_id in account_ids:
            content = await self.generate_content(
                account_id=account_id,
                content_type=content_type,
                persona=PersonaType.EXECUTIVE,
                context=campaign_context,
            )
            results.append(content)

        return results

    def _generate_mock_content(
        self,
        account_id: str,
        content_type: ContentType,
        persona: PersonaType,
        context: dict[str, Any] | None,
    ) -> PersonalizedContent:
        """Generate mock personalized content for demonstration.

        Args:
            account_id: The target account.
            content_type: Type of content.
            persona: Target persona.
            context: Additional context.

        Returns:
            PersonalizedContent object.
        """
        templates = {
            ContentType.EMAIL: {
                "subject": "How {company} can accelerate growth with ABM",
                "body": (
                    "Hi {name},\n\n"
                    "I noticed {company} has been expanding rapidly in the {industry} space. "
                    "Companies like yours are seeing 3x better engagement with account-based "
                    "marketing approaches.\n\n"
                    "Would you be open to a brief conversation about how we've helped "
                    "similar companies achieve their growth targets?"
                ),
                "call_to_action": "Schedule a 15-minute call",
            },
            ContentType.LANDING_PAGE: {
                "subject": "{company}'s Personalized ABM Dashboard",
                "body": (
                    "Welcome, {company}! See how ABM can drive "
                    "{revenue_target} in new pipeline for your team."
                ),
                "call_to_action": "View Your Custom ROI Report",
            },
            ContentType.AD_COPY: {
                "subject": "{company}: Ready to transform your marketing?",
                "body": (
                    "Join 500+ companies using ABM to drive "
                    "measurable revenue growth. See why {company} should too."
                ),
                "call_to_action": "Learn More",
            },
        }

        template = templates.get(content_type, templates[ContentType.EMAIL])

        return PersonalizedContent(
            content_id=f"content_{account_id}_{content_type.value}",
            account_id=account_id,
            content_type=content_type,
            persona=persona,
            subject=template["subject"].format(
                company="TechCorp",
                industry="technology",
                revenue_target="$10M",
            ),
            body=template["body"].format(
                name="Sarah",
                company="TechCorp",
                industry="technology",
                revenue_target="$10M",
            ),
            call_to_action=template["call_to_action"],
            personalization_factors={
                "industry": "technology",
                "company_size": "500-1000",
                "pain_point": "lead_quality",
                "intent_level": "high",
            },
        )
