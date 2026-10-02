"""Strategist agent — defines content strategy, audience, tone, and angle."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from content_generator.agents.researcher import ResearchResult

logger = logging.getLogger(__name__)


@dataclass
class StrategyResult:
    """Output from the Strategist agent."""

    content_type: str
    target_audience: str
    tone: str
    angle: str
    key_messages: list[str] = field(default_factory=list)
    content_outline: list[dict[str, Any]] = field(default_factory=list)
    seo_recommendations: dict[str, Any] = field(default_factory=dict)
    word_count_target: int = 1500


class StrategistAgent:
    """Agent responsible for defining the content strategy.

    Takes research output and produces a comprehensive content strategy
    including target audience, tone, angle, key messages, and outline.
    """

    SYSTEM_PROMPT = """You are an expert content strategist for a marketing agency.
Your job is to analyze research data and produce a detailed content strategy.

You must respond with valid JSON in this exact schema:
{
    "content_type": "article|landing_page|social_post|email",
    "target_audience": "description of the ideal reader",
    "tone": "professional|casual|authoritative|friendly|persuasive",
    "angle": "the unique perspective or hook",
    "key_messages": ["message1", "message2", "message3"],
    "content_outline": [
        {"heading": "Section heading", "key_points": ["point1", "point2"]}
    ],
    "seo_recommendations": {
        "primary_keyword": "main keyword",
        "secondary_keywords": ["kw1", "kw2"],
        "meta_description": "SEO meta description",
        "suggested_title": "SEO-optimized title"
    },
    "word_count_target": 1500
}

Be specific, actionable, and data-driven. Consider the research findings carefully."""

    def __init__(
        self,
        *,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        api_key: str | None = None,
    ) -> None:
        """Initialize the Strategist agent.

        Args:
            model: Anthropic model identifier.
            max_tokens: Maximum tokens for the response.
            temperature: Sampling temperature.
            api_key: Anthropic API key (falls back to env var).
        """
        self._llm = ChatAnthropic(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            anthropic_api_key=api_key,
        )

    async def strategize(
        self,
        research: ResearchResult,
        *,
        content_type: str = "article",
        language: str = "en",
    ) -> StrategyResult:
        """Generate a content strategy based on research.

        Args:
            research: Research output from the Researcher agent.
            content_type: Type of content to create.
            language: Target language code.

        Returns:
            StrategyResult with the full content strategy.

        Raises:
            ValueError: If research is empty or invalid.
            RuntimeError: If the LLM call fails.
        """
        if not research.query:
            raise ValueError("Research query must not be empty")

        logger.info(
            "Generating strategy for: %s (type=%s, lang=%s)",
            research.query,
            content_type,
            language,
        )

        user_prompt = self._build_prompt(research, content_type=content_type, language=language)

        try:
            response = await self._llm.ainvoke(
                [
                    SystemMessage(content=self.SYSTEM_PROMPT),
                    HumanMessage(content=user_prompt),
                ]
            )
            raw = response.content
            if isinstance(raw, list):
                raw = "".join(
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in raw
                )
            strategy_data = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse strategy JSON: %s", exc)
            raise RuntimeError("Strategist returned invalid JSON") from exc
        except Exception as exc:
            logger.error("Strategist LLM call failed: %s", exc)
            raise RuntimeError(f"Strategist failed: {exc}") from exc

        result = StrategyResult(
            content_type=strategy_data.get("content_type", content_type),
            target_audience=strategy_data.get("target_audience", ""),
            tone=strategy_data.get("tone", "professional"),
            angle=strategy_data.get("angle", ""),
            key_messages=strategy_data.get("key_messages", []),
            content_outline=strategy_data.get("content_outline", []),
            seo_recommendations=strategy_data.get("seo_recommendations", {}),
            word_count_target=int(strategy_data.get("word_count_target", 1500)),
        )

        logger.info(
            "Strategy generated: %d sections, %d key messages",
            len(result.content_outline),
            len(result.key_messages),
        )
        return result

    def _build_prompt(
        self,
        research: ResearchResult,
        *,
        content_type: str,
        language: str,
    ) -> str:
        """Build the user prompt for the strategist.

        Args:
            research: Research data.
            content_type: Content type.
            language: Target language.

        Returns:
            Formatted prompt string.
        """
        competitors_json = json.dumps(research.competitors, indent=2)
        trending_json = json.dumps(research.trending_topics, indent=2)
        keywords_json = json.dumps(research.keywords, indent=2)

        return f"""Research Query: {research.query}
Content Type: {content_type}
Target Language: {language}

## SERP Summary
{research.summary}

## Competitors
{competitors_json}

## Trending Topics
{trending_json}

## Keywords
{keywords_json}

Based on this research, create a comprehensive content strategy.
Consider the competitive landscape, trending topics, and keyword opportunities.
The strategy should be tailored for {language} language content."""
