"""Writer agent — produces long-form content based on strategy."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from content_generator.agents.strategist import StrategyResult

logger = logging.getLogger(__name__)


@dataclass
class WriterResult:
    """Output from the Writer agent."""

    title: str
    content: str
    word_count: int
    sections: list[dict[str, Any]] = field(default_factory=list)
    meta_description: str = ""


class WriterAgent:
    """Agent responsible for generating long-form content.

    Takes a content strategy and produces high-quality, structured content
    optimized for the target audience and tone.
    """

    SYSTEM_PROMPT = """You are an expert content writer for a marketing agency.
You produce high-quality, engaging, and well-structured content.

Rules:
- Write in the specified tone and for the specified audience
- Follow the content outline exactly
- Incorporate key messages naturally
- Use the SEO recommendations for keyword placement
- Write compelling headlines and subheadings
- Use short paragraphs and clear structure
- Include a strong introduction and conclusion
- Target the specified word count

Output format: Markdown with proper heading hierarchy."""

    def __init__(
        self,
        *,
        model: str = "gpt-4-turbo-preview",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        api_key: str | None = None,
    ) -> None:
        """Initialize the Writer agent.

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

    async def write(
        self,
        strategy: StrategyResult,
        *,
        language: str = "en",
    ) -> WriterResult:
        """Generate content based on the strategy.

        Args:
            strategy: Content strategy from the Strategist agent.
            language: Target language code.

        Returns:
            WriterResult with the generated content.

        Raises:
            ValueError: If strategy is invalid.
            RuntimeError: If the LLM call fails.
        """
        if not strategy.content_outline:
            raise ValueError("Strategy must have a content outline")

        logger.info(
            "Writing content: type=%s, lang=%s, target_words=%d",
            strategy.content_type,
            language,
            strategy.word_count_target,
        )

        user_prompt = self._build_prompt(strategy, language=language)

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
            content = raw.strip()
        except Exception as exc:
            logger.error("Writer LLM call failed: %s", exc)
            raise RuntimeError(f"Writer failed: {exc}") from exc

        word_count = len(content.split())
        title = self._extract_title(content)
        meta_description = self._extract_meta_description(strategy)

        result = WriterResult(
            title=title,
            content=content,
            word_count=word_count,
            sections=strategy.content_outline,
            meta_description=meta_description,
        )

        logger.info("Content written: %d words, title=%s", word_count, title)
        return result

    def _build_prompt(self, strategy: StrategyResult, *, language: str) -> str:
        """Build the user prompt for the writer.

        Args:
            strategy: Content strategy.
            language: Target language.

        Returns:
            Formatted prompt string.
        """
        outline_json = __import__("json").dumps(strategy.content_outline, indent=2)
        key_messages_json = __import__("json").dumps(strategy.key_messages, indent=2)
        seo_json = __import__("json").dumps(strategy.seo_recommendations, indent=2)

        return f"""Write {strategy.content_type} content in language: {language}

## Target Audience
{strategy.target_audience}

## Tone
{strategy.tone}

## Angle
{strategy.angle}

## Key Messages
{key_messages_json}

## Content Outline
{outline_json}

## SEO Recommendations
{seo_json}

## Word Count Target
{strategy.word_count_target} words

Write the full content now in Markdown format. Use the outline as your section structure."""

    def _extract_title(self, content: str) -> str:
        """Extract the title from the generated content.

        Args:
            content: Generated markdown content.

        Returns:
            Title string.
        """
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
        return "Untitled"

    def _extract_meta_description(self, strategy: StrategyResult) -> str:
        """Extract or generate a meta description.

        Args:
            strategy: Content strategy.

        Returns:
            Meta description string.
        """
        seo = strategy.seo_recommendations
        if isinstance(seo, dict):
            return seo.get("meta_description", "")
        return ""
