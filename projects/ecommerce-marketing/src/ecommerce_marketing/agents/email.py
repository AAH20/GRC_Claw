"""Email marketing campaign agent."""

from __future__ import annotations

from typing import Any

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ecommerce_marketing.config import get_settings

logger = structlog.get_logger(__name__)


class EmailTemplate(BaseModel):
    """Email template data model."""

    name: str = Field(..., description="Template name")
    subject: str = Field(..., description="Email subject line")
    body_html: str = Field(..., description="HTML email body")
    body_text: str = Field(..., description="Plain text email body")
    variables: list[str] = Field(default_factory=list, description="Template variables")


class EmailCampaign(BaseModel):
    """Email campaign data model."""

    id: str = Field(..., description="Campaign identifier")
    name: str = Field(..., description="Campaign name")
    template: EmailTemplate = Field(..., description="Email template")
    segment: str = Field(..., description="Target customer segment")
    status: str = Field(default="draft", description="Campaign status")
    scheduled_at: str | None = Field(default=None, description="Scheduled send time")
    ab_test_variant: str | None = Field(default=None, description="A/B test variant")


class EmailCampaignRequest(BaseModel):
    """Request model for creating an email campaign."""

    name: str = Field(..., description="Campaign name")
    segment: str = Field(..., description="Target customer segment")
    campaign_type: str = Field(..., description="Type of campaign (promotional, newsletter, welcome)")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context for personalization")
    enable_ab_test: bool = Field(default=True, description="Whether to enable A/B testing")


class EmailAgent:
    """AI agent for creating and managing email marketing campaigns.

    Generates personalized email content, manages A/B testing, and optimizes
    subject lines for maximum engagement.
    """

    def __init__(self, llm: BaseChatModel | None = None) -> None:
        """Initialize the email agent.

        Args:
            llm: Optional LangChain chat model. If not provided, uses the default
                model from settings.
        """
        self.settings = get_settings()
        self.llm = llm or self._create_default_llm()
        self._prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert email marketing copywriter. "
                    "Create compelling, personalized email content that drives engagement and conversions. "
                    "Follow best practices for subject lines, CTAs, and mobile optimization. "
                    "Output valid JSON with subject, body_html, body_text, and variables fields.",
                ),
                (
                    "human",
                    "Campaign name: {name}\n"
                    "Campaign type: {campaign_type}\n"
                    "Target segment: {segment}\n"
                    "Context: {context}\n"
                    "A/B test enabled: {enable_ab_test}\n\n"
                    "Create an email campaign with compelling subject and body content.",
                ),
            ]
        )

    def _create_default_llm(self) -> BaseChatModel:
        """Create the default LLM from settings.

        Returns:
            Configured LangChain chat model.

        Raises:
            ValueError: If OPENAI_API_KEY is not configured.
        """
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as exc:
            raise ImportError(
                "langchain-openai is required for default LLM. "
                "Install with: pip install langchain-openai"
            ) from exc

        if not self.settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for email campaigns")

        return ChatOpenAI(
            model=self.settings.openai_model,
            api_key=self.settings.openai_api_key,
            temperature=0.7,
            max_tokens=2000,
        )

    async def create_campaign(self, request: EmailCampaignRequest) -> EmailCampaign:
        """Create a new email campaign with AI-generated content.

        Args:
            request: Campaign creation request.

        Returns:
            Created email campaign with generated content.

        Raises:
            ValueError: If the request is invalid.
        """
        if not request.name.strip():
            raise ValueError("Campaign name is required")

        logger.info(
            "Creating email campaign",
            name=request.name,
            segment=request.segment,
            campaign_type=request.campaign_type,
        )

        chain = self._prompt | self.llm
        response = await chain.ainvoke(
            {
                "name": request.name,
                "campaign_type": request.campaign_type,
                "segment": request.segment,
                "context": str(request.context),
                "enable_ab_test": request.enable_ab_test,
            }
        )

        template = self._parse_template(
            response.content if hasattr(response, "content") else str(response),
            request.name,
        )

        campaign = EmailCampaign(
            id="",
            name=request.name,
            template=template,
            segment=request.segment,
            status="draft",
            ab_test_variant="A" if request.enable_ab_test else None,
        )

        logger.info(
            "Email campaign created",
            campaign_id=campaign.id,
            name=campaign.name,
        )

        return campaign

    def _parse_template(self, llm_output: str, name: str) -> EmailTemplate:
        """Parse LLM output into an email template.

        Args:
            llm_output: Raw text output from the LLM.
            name: Campaign name for fallback.

        Returns:
            Parsed email template.
        """
        import json

        try:
            data = json.loads(llm_output)
            return EmailTemplate(
                name=name,
                subject=data.get("subject", "Special Offer Just for You"),
                body_html=data.get("body_html", ""),
                body_text=data.get("body_text", ""),
                variables=data.get("variables", []),
            )
        except (json.JSONDecodeError, KeyError):
            logger.warning("Failed to parse email template, using fallback")
            return EmailTemplate(
                name=name,
                subject="Special Offer Just for You",
                body_html="<p>Check out our latest offers!</p>",
                body_text="Check out our latest offers!",
                variables=[],
            )

    def generate_ab_variants(self, template: EmailTemplate) -> list[EmailTemplate]:
        """Generate A/B test variants for an email template.

        Args:
            template: Base email template.

        Returns:
            List of template variants for A/B testing.
        """
        if not self.settings.agents.email.ab_test_enabled:
            return [template]

        # Generate variant B with different subject line
        variant_b = EmailTemplate(
            name=f"{template.name} (Variant B)",
            subject=f"🔥 {template.subject}",
            body_html=template.body_html,
            body_text=template.body_text,
            variables=template.variables,
        )

        return [template, variant_b]
