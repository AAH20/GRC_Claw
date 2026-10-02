"""Ad Creative Agent — generates and iterates ad copy, headlines, and CTAs."""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class AdVariant(BaseModel):
    """A single ad creative variant.

    Attributes:
        headline: The ad headline.
        description: The ad description body.
        cta: Call-to-action text.
        platform: Target platform (google, meta, linkedin, tiktok).
        character_count: Total character count of the variant.
    """

    headline: str
    description: str
    cta: str
    platform: str = "google"
    character_count: int = 0


class AdCreativeResult(BaseModel):
    """Result of an ad creative generation operation.

    Attributes:
        campaign_id: The campaign this creative is for.
        variants: List of ad variants.
        total_variants: Total number of variants generated.
    """

    campaign_id: str
    variants: list[AdVariant] = Field(default_factory=list)
    total_variants: int = 0


class AdCreativeAgent:
    """Agent responsible for generating ad creative content.

    Uses LLM-powered copywriting to produce platform-optimized ad variants
    with headlines, descriptions, and calls-to-action.
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        max_variants: int = 5,
    ) -> None:
        """Initialize the Ad Creative Agent.

        Args:
            model: The LLM model to use for copy generation.
            max_variants: Maximum number of variants to generate.
        """
        self.model = model
        self.max_variants = max_variants
        self._llm: Any = None

    def _get_llm(self) -> Any:
        """Lazy-load the LLM client.

        Returns:
            The LangChain LLM instance.
        """
        if self._llm is None:
            from langchain_openai import ChatOpenAI

            self._llm = ChatOpenAI(model=self.model, temperature=0.7)
        return self._llm

    async def generate_creatives(
        self,
        campaign_id: str,
        product_name: str,
        target_audience: str,
        key_benefits: list[str],
        platform: str = "google",
    ) -> AdCreativeResult:
        """Generate ad creative variants for a campaign.

        Args:
            campaign_id: The campaign identifier.
            product_name: The product or service name.
            target_audience: Description of the target audience.
            key_benefits: List of key product benefits.
            platform: Target ad platform.

        Returns:
            An AdCreativeResult with generated variants.

        Raises:
            ValueError: If product_name is empty.
        """
        if not product_name.strip():
            raise ValueError("Product name cannot be empty")

        logger.info(
            "Generating ad creatives",
            campaign_id=campaign_id,
            platform=platform,
        )

        llm = self._get_llm()
        prompt = self._build_prompt(
            product_name, target_audience, key_benefits, platform
        )

        try:
            response = await llm.ainvoke(prompt)
            variants = self._parse_response(response.content, platform)
        except Exception as exc:
            logger.error("Ad creative generation failed", error=str(exc))
            variants = self._fallback_variants(product_name, platform)

        result = AdCreativeResult(
            campaign_id=campaign_id,
            variants=variants[: self.max_variants],
            total_variants=len(variants),
        )

        logger.info("Ad creative generation complete", count=len(variants))
        return result

    def _build_prompt(
        self,
        product: str,
        audience: str,
        benefits: list[str],
        platform: str,
    ) -> str:
        """Build the LLM prompt for ad creative generation.

        Args:
            product: The product name.
            audience: Target audience description.
            benefits: Key product benefits.
            platform: Target platform.

        Returns:
            The formatted prompt string.
        """
        benefits_text = "\n".join(f"- {b}" for b in benefits)
        return (
            f"You are a world-class copywriter specializing in {platform} ads.\n\n"
            f"Product: {product}\n"
            f"Target Audience: {audience}\n"
            f"Key Benefits:\n{benefits_text}\n\n"
            f"Generate {self.max_variants} ad variants. Each variant must include:\n"
            "- headline: compelling headline (max 30 chars for Google, 40 for Meta)\n"
            "- description: persuasive body copy (max 90 chars for Google, 125 for Meta)\n"
            "- cta: call-to-action (e.g., 'Shop Now', 'Learn More', 'Sign Up')\n\n"
            "Return ONLY a JSON array of objects with headline, description, and cta fields."
        )

    def _parse_response(self, content: str, platform: str) -> list[AdVariant]:
        """Parse the LLM response into AdVariant objects.

        Args:
            content: The raw LLM response content.
            platform: The target platform.

        Returns:
            A list of parsed AdVariant objects.
        """
        import json

        variants: list[AdVariant] = []
        try:
            data = json.loads(content)
            if isinstance(data, list):
                for item in data:
                    headline = item.get("headline", "")
                    description = item.get("description", "")
                    cta = item.get("cta", "Learn More")
                    variants.append(
                        AdVariant(
                            headline=headline,
                            description=description,
                            cta=cta,
                            platform=platform,
                            character_count=len(headline) + len(description) + len(cta),
                        )
                    )
        except (json.JSONDecodeError, TypeError, KeyError) as exc:
            logger.warning("Failed to parse LLM response", error=str(exc))

        return variants

    def _fallback_variants(self, product: str, platform: str) -> list[AdVariant]:
        """Generate fallback ad variants when LLM is unavailable.

        Args:
            product: The product name.
            platform: The target platform.

        Returns:
            A list of basic AdVariant objects.
        """
        return [
            AdVariant(
                headline=f"Discover {product}",
                description=f"See why thousands choose {product}. Start your journey today.",
                cta="Learn More",
                platform=platform,
            ),
            AdVariant(
                headline=f"{product} — Try It Now",
                description=f"Experience the difference. {product} delivers results.",
                cta="Shop Now",
                platform=platform,
            ),
        ]
