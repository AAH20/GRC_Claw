"""Creative Agent — Ad copy generation and creative recommendations."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool

from agents.base import AgentContext, AgentResult, BaseAgent
from core.logging import get_logger

logger = get_logger(__name__)


class CreativeAgent(BaseAgent[dict[str, Any]]):
    """Agent responsible for ad copy generation and creative direction."""

    def __init__(
        self,
        llm: BaseLanguageModel | None = None,
        tools: list[BaseTool] | None = None,
    ) -> None:
        super().__init__(
            name="Creative Agent",
            description="Ad copy generation, creative asset recommendations, and A/B test variants",
            llm=llm,
            tools=tools,
            timeout=90,
            max_iterations=4,
        )

    async def _execute(self, context: AgentContext) -> AgentResult[dict[str, Any]]:
        self._logger.info(
            "creative_generation_started",
            campaign_id=context.campaign_id,
            task=context.task,
        )
        creative_package = self._generate_creative(context)
        return AgentResult(
            success=True,
            data=creative_package,
            metadata={
                "agent": self.name,
                "campaign_id": context.campaign_id,
                "variants_count": len(creative_package.get("ab_test_variants", [])),
            },
        )

    def _generate_creative(self, context: AgentContext) -> dict[str, Any]:
        params = context.parameters
        brand_voice = params.get("brand_voice", "professional")
        channels = params.get("channels", ["search", "social"])
        key_message = params.get("key_message", "")
        target_audience = params.get("target_audience", {})
        return {
            "campaign_id": context.campaign_id,
            "brand_voice": brand_voice,
            "key_message": key_message,
            "ad_copy_variants": self._generate_ad_copy(
                brand_voice, channels, key_message, target_audience
            ),
            "creative_recommendations": self._recommend_creative_assets(channels),
            "ab_test_variants": self._create_ab_variants(channels, key_message),
            "landing_page_suggestions": self._suggest_landing_pages(key_message),
        }

    def _generate_ad_copy(
        self,
        brand_voice: str,
        channels: list[str],
        key_message: str,
        target_audience: dict[str, Any],
    ) -> dict[str, list[dict[str, str]]]:
        copy_templates = {
            "search": [
                {"headline": key_message[:30], "description": f"Discover {key_message}"},
                {"headline": f"Best {key_message}", "description": "Learn more today"},
            ],
            "social": [
                {"headline": key_message, "body": "Swipe up to learn more", "cta": "Learn More"},
                {"headline": "You asked, we delivered", "body": key_message, "cta": "Shop Now"},
            ],
            "display": [
                {"headline": key_message, "subheadline": "Limited time offer", "cta": "Get Started"},
            ],
            "email": [
                {"subject": f"Introducing: {key_message}", "preview": "Exclusive offer inside"},
            ],
        }
        result: dict[str, list[dict[str, str]]] = {}
        for channel in channels:
            result[channel] = copy_templates.get(channel, copy_templates["social"])
        return result

    def _recommend_creative_assets(self, channels: list[str]) -> list[dict[str, Any]]:
        recommendations = []
        for channel in channels:
            if channel == "social":
                recommendations.extend([
                    {"type": "video", "format": "9:16", "duration": "15s", "purpose": "awareness"},
                    {"type": "carousel", "format": "1:1", "slides": 5, "purpose": "consideration"},
                ])
            elif channel == "display":
                recommendations.extend([
                    {"type": "banner", "format": "300x250", "purpose": "retargeting"},
                    {"type": "banner", "format": "728x90", "purpose": "awareness"},
                ])
            elif channel == "search":
                recommendations.append(
                    {"type": "responsive_search_ad", "format": "text", "purpose": "conversion"}
                )
        return recommendations

    def _create_ab_variants(
        self, channels: list[str], key_message: str
    ) -> list[dict[str, Any]]:
        variants = []
        for channel in channels:
            variants.append({
                "channel": channel,
                "variant_a": {"headline": key_message, "approach": "benefit_driven"},
                "variant_b": {"headline": f"Why {key_message} matters", "approach": "curiosity_driven"},
                "test_metric": "ctr",
                "sample_size": 10000,
                "duration_days": 7,
            })
        return variants

    def _suggest_landing_pages(self, key_message: str) -> list[dict[str, Any]]:
        return [
            {
                "type": "dedicated_lp",
                "headline": key_message,
                "elements": ["hero_image", "benefit_bullets", "social_proof", "cta_button"],
                "load_time_target": "2s",
            },
            {
                "type": "dynamic_lp",
                "headline": key_message,
                "elements": ["personalized_hero", "product_grid", "reviews", "cta_button"],
                "load_time_target": "2.5s",
            },
        ]
