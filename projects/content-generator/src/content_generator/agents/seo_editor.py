"""SEO Editor agent — optimizes content for search engines."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from content_generator.agents.strategist import StrategyResult
from content_generator.agents.writer import WriterResult

logger = logging.getLogger(__name__)


@dataclass
class SEOResult:
    """Output from the SEO Editor agent."""

    optimized_content: str
    meta_title: str
    meta_description: str
    slug: str
    keyword_density: dict[str, float] = field(default_factory=dict)
    readability_score: float = 0.0
    seo_score: float = 0.0
    suggestions: list[str] = field(default_factory=list)


class SEOEditorAgent:
    """Agent responsible for optimizing content for search engines.

    Takes generated content and applies SEO best practices including
    keyword optimization, meta tag generation, and readability improvements.
    """

    SYSTEM_PROMPT = """You are an expert SEO editor. Your job is to optimize content for search
engines while maintaining readability and user experience.

Your tasks:
1. Optimize keyword placement (primary keyword in title, first 100 words, headings)
2. Generate SEO meta title (50-60 characters)
3. Generate meta description (150-160 characters)
4. Create a URL-friendly slug
5. Improve readability (short paragraphs, active voice, transition words)
6. Add internal/external link suggestions
7. Ensure proper heading hierarchy (H1 > H2 > H3)

Output the optimized content in Markdown format.
Also provide a JSON block at the end with:
```json
{{
    "meta_title": "...",
    "meta_description": "...",
    "slug": "...",
    "keyword_density": {{"keyword": 0.02}},
    "readability_score": 85.0,
    "seo_score": 90.0,
    "suggestions": ["suggestion1", "suggestion2"]
}}
```"""

    def __init__(
        self,
        *,
        model: str = "gpt-4-turbo-preview",
        max_tokens: int = 2048,
        temperature: float = 0.3,
        api_key: str | None = None,
    ) -> None:
        """Initialize the SEO Editor agent.

        Args:
            model: OpenAI model identifier.
            max_tokens: Maximum tokens for the response.
            temperature: Sampling temperature.
            api_key: OpenAI API key (falls back to env var).
        """
        self._llm = ChatOpenAI(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            openai_api_key=api_key,
        )

    async def optimize(
        self,
        content: WriterResult,
        strategy: StrategyResult,
    ) -> SEOResult:
        """Optimize content for SEO.

        Args:
            content: Generated content from the Writer agent.
            strategy: Content strategy with SEO recommendations.

        Returns:
            SEOResult with optimized content and metadata.

        Raises:
            ValueError: If content is empty.
            RuntimeError: If the LLM call fails.
        """
        if not content.content:
            raise ValueError("Content must not be empty")

        logger.info("Optimizing content for SEO: %s", content.title)

        user_prompt = self._build_prompt(content, strategy)

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
        except Exception as exc:
            logger.error("SEO Editor LLM call failed: %s", exc)
            raise RuntimeError(f"SEO Editor failed: {exc}") from exc

        optimized_content, seo_data = self._parse_response(raw)
        keyword_density = self._calculate_keyword_density(optimized_content, strategy)

        result = SEOResult(
            optimized_content=optimized_content,
            meta_title=seo_data.get("meta_title", content.title),
            meta_description=seo_data.get("meta_description", content.meta_description),
            slug=seo_data.get("slug", self._generate_slug(content.title)),
            keyword_density=keyword_density,
            readability_score=float(seo_data.get("readability_score", 0.0)),
            seo_score=float(seo_data.get("seo_score", 0.0)),
            suggestions=seo_data.get("suggestions", []),
        )

        logger.info(
            "SEO optimization complete: score=%.1f, readability=%.1f",
            result.seo_score,
            result.readability_score,
        )
        return result

    def _build_prompt(self, content: WriterResult, strategy: StrategyResult) -> str:
        """Build the user prompt for the SEO editor.

        Args:
            content: Generated content.
            strategy: Content strategy.

        Returns:
            Formatted prompt string.
        """
        seo_json = __import__("json").dumps(strategy.seo_recommendations, indent=2)

        return f"""Optimize the following content for SEO.

## Original Title
{content.title}

## Original Content
{content.content}

## SEO Recommendations
{seo_json}

## Target Word Count
{strategy.word_count_target}

Provide the optimized content followed by the JSON metadata block."""

    def _parse_response(self, raw: str) -> tuple[str, dict[str, Any]]:
        """Parse the LLM response into content and metadata.

        Args:
            raw: Raw LLM response.

        Returns:
            Tuple of (optimized_content, seo_metadata_dict).
        """
        import json

        # Try to extract JSON block
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if json_match:
            try:
                seo_data = json.loads(json_match.group(1))
                # Remove the JSON block from content
                content = raw[: json_match.start()].strip()
                return content, seo_data
            except json.JSONDecodeError:
                logger.warning("Failed to parse SEO JSON block")

        # Fallback: return raw as content with empty metadata
        return raw.strip(), {}

    def _calculate_keyword_density(
        self,
        content: str,
        strategy: StrategyResult,
    ) -> dict[str, float]:
        """Calculate keyword density for the primary and secondary keywords.

        Args:
            content: Optimized content.
            strategy: Content strategy with SEO recommendations.

        Returns:
            Dictionary mapping keywords to their density percentages.
        """
        seo = strategy.seo_recommendations
        if not isinstance(seo, dict):
            return {}

        keywords: list[str] = []
        primary = seo.get("primary_keyword", "")
        if primary:
            keywords.append(primary)
        secondary = seo.get("secondary_keywords", [])
        if isinstance(secondary, list):
            keywords.extend(secondary)

        if not keywords:
            return {}

        word_count = len(content.split())
        if word_count == 0:
            return {}

        density: dict[str, float] = {}
        content_lower = content.lower()
        for keyword in keywords:
            keyword_lower = keyword.lower()
            count = content_lower.count(keyword_lower)
            density[keyword] = round(count / word_count, 4)

        return density

    def _generate_slug(self, title: str) -> str:
        """Generate a URL-friendly slug from a title.

        Args:
            title: Content title.

        Returns:
            URL-friendly slug.
        """
        slug = title.lower()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)
        slug = re.sub(r"-+", "-", slug)
        return slug.strip("-")
