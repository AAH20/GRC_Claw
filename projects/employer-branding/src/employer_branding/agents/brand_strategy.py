"""Brand Strategy Agent for creating employer brand strategies."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from employer_branding.agents.base import BaseAgent
from employer_branding.models import BrandStrategy, BrandStrategyRequest


class BrandStrategyAgent(BaseAgent[BrandStrategy]):
    """Agent that creates comprehensive employer brand strategies.

    Develops strategic frameworks including EVP, content pillars, channel
    recommendations, and tone guidelines based on company profile and
    target audience.
    """

    def __init__(self) -> None:
        """Initialize the brand strategy agent."""
        super().__init__()
        self._prompt_template = self._build_prompt_template()

    def _build_prompt_template(self) -> ChatPromptTemplate:
        """Build the prompt template for brand strategy creation.

        Returns:
            Configured ChatPromptTemplate.
        """
        system_message = """You are an expert employer branding strategist.
Create a comprehensive brand strategy and return a JSON object with:
{
    "employee_value_proposition": "compelling EVP statement",
    "key_messages": ["key brand message strings"],
    "content_pillars": ["content theme strings"],
    "channels": ["recommended marketing channel strings"],
    "tone_guidelines": {"context": "tone description"},
    "competitive_positioning": "positioning statement or null"
}

Base your strategy on the company's mission, vision, values, and target audience.
Be specific, actionable, and differentiated from competitors."""

        return ChatPromptTemplate.from_messages([
            SystemMessage(content=system_message),
            HumanMessage(content="{input}"),
        ])

    async def run(self, request: BrandStrategyRequest) -> BrandStrategy:
        """Create an employer brand strategy.

        Args:
            request: Brand strategy request with company details.

        Returns:
            BrandStrategy with complete strategic framework.

        Raises:
            ValueError: If request parameters are invalid.
            RuntimeError: If strategy creation fails.
        """
        self.logger.info(
            "creating_brand_strategy",
            company=request.company_name,
            industry=request.industry,
        )

        try:
            prompt = self._build_strategy_prompt(request)
            response = await self._model.ainvoke(prompt)
            raw_content = response.content if hasattr(response, "content") else str(response)

            parsed = self._parse_response(raw_content)

            strategy = BrandStrategy(
                company_name=request.company_name,
                mission=request.mission,
                vision=request.vision,
                values=request.values,
                employee_value_proposition=parsed["employee_value_proposition"],
                target_audience=request.target_audience,
                key_messages=parsed.get("key_messages", []),
                content_pillars=parsed.get("content_pillars", []),
                channels=parsed.get("channels", []),
                tone_guidelines=parsed.get("tone_guidelines", {}),
                competitive_positioning=parsed.get("competitive_positioning"),
            )

            self.logger.info(
                "brand_strategy_created",
                strategy_id=str(strategy.id),
                company=request.company_name,
            )
            return strategy

        except Exception as exc:
            self.logger.error("brand_strategy_creation_failed", error=str(exc))
            raise RuntimeError(f"Failed to create brand strategy: {exc}") from exc

    def _build_strategy_prompt(self, request: BrandStrategyRequest) -> str:
        """Build the strategy creation prompt.

        Args:
            request: Brand strategy request.

        Returns:
            Formatted prompt string.
        """
        parts = [
            f"Create an employer brand strategy for: {request.company_name}",
            f"Industry: {request.industry}",
            f"Company size: {request.company_size}",
            f"Mission: {request.mission}",
            f"Vision: {request.vision}",
            f"Values: {', '.join(request.values)}",
            f"Target audience: {', '.join(request.target_audience)}",
        ]

        if request.additional_context:
            parts.append(f"Additional context: {request.additional_context}")

        return "\n".join(parts)

    def _parse_response(self, raw_content: str) -> dict[str, Any]:
        """Parse the LLM response into a structured dictionary.

        Args:
            raw_content: Raw response content from the model.

        Returns:
            Parsed dictionary with strategy data.

        Raises:
            ValueError: If response cannot be parsed.
        """
        import json

        content = raw_content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])

        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to parse brand strategy response: {exc}") from exc

        if "employee_value_proposition" not in parsed:
            raise ValueError("Missing required field: employee_value_proposition")

        return parsed
