"""Atomizer agent — breaks content into platform-specific micro-content."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from content_generator.agents.seo_editor import SEOResult

logger = logging.getLogger(__name__)


@dataclass
class AtomizedContent:
    """A single piece of atomized micro-content."""

    platform: str
    format: str
    content: str
    character_count: int
    hashtags: list[str] = field(default_factory=list)
    call_to_action: str = ""


@dataclass
class AtomizerResult:
    """Output from the Atomizer agent."""

    original_title: str
    pieces: list[AtomizedContent] = field(default_factory=list)
    total_pieces: int = 0


class AtomizerAgent:
    """Agent responsible for breaking content into platform-specific micro-content.

    Takes optimized content and creates tailored versions for various
    social media platforms and marketing channels.
    """

    SYSTEM_PROMPT = """You are a social media content atomizer. Your job is to break down
long-form content into platform-specific micro-content pieces.

Supported platforms and their constraints:
- Twitter/X: 280 characters, concise, hashtags
- LinkedIn: 3000 characters, professional tone, hashtags
- Instagram: 2200 characters, visual descriptions, hashtags
- Facebook: 63206 characters, conversational tone
- TikTok: 2200 characters, trending hooks, hashtags
- Email Subject: 60 characters, curiosity-driven
- Email Body: 500 characters, CTA-focused

For each platform, create:
1. The micro-content text
2. Relevant hashtags (3-5)
3. A call-to-action

Respond with valid JSON:
```json
{{
    "pieces": [
        {{
            "platform": "twitter",
            "format": "tweet",
            "content": "...",
            "character_count": 280,
            "hashtags": ["#tag1", "#tag2"],
            "call_to_action": "..."
        }}
    ]
}}
```"""

    def __init__(
        self,
        *,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        api_key: str | None = None,
    ) -> None:
        """Initialize the Atomizer agent.

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

    async def atomize(
        self,
        content: SEOResult,
        *,
        platforms: list[str] | None = None,
        language: str = "en",
    ) -> AtomizerResult:
        """Break content into platform-specific micro-content.

        Args:
            content: Optimized content from the SEO Editor.
            platforms: List of platforms to generate for (default: all).
            language: Target language code.

        Returns:
            AtomizerResult with all micro-content pieces.

        Raises:
            ValueError: If content is empty.
            RuntimeError: If the LLM call fails.
        """
        if not content.optimized_content:
            raise ValueError("Content must not be empty")

        target_platforms = platforms or ["twitter", "linkedin", "instagram", "facebook", "email"]
        logger.info(
            "Atomizing content for %d platforms: %s", len(target_platforms), target_platforms
        )

        user_prompt = self._build_prompt(content, platforms=target_platforms, language=language)

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
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse atomizer JSON: %s", exc)
            raise RuntimeError("Atomizer returned invalid JSON") from exc
        except Exception as exc:
            logger.error("Atomizer LLM call failed: %s", exc)
            raise RuntimeError(f"Atomizer failed: {exc}") from exc

        pieces: list[AtomizedContent] = []
        for item in data.get("pieces", []):
            piece = AtomizedContent(
                platform=item.get("platform", "unknown"),
                format=item.get("format", "post"),
                content=item.get("content", ""),
                character_count=len(item.get("content", "")),
                hashtags=item.get("hashtags", []),
                call_to_action=item.get("call_to_action", ""),
            )
            pieces.append(piece)

        result = AtomizerResult(
            original_title=content.meta_title,
            pieces=pieces,
            total_pieces=len(pieces),
        )

        logger.info("Atomization complete: %d pieces generated", result.total_pieces)
        return result

    def _build_prompt(
        self,
        content: SEOResult,
        *,
        platforms: list[str],
        language: str,
    ) -> str:
        """Build the user prompt for the atomizer.

        Args:
            content: Optimized content.
            platforms: Target platforms.
            language: Target language.

        Returns:
            Formatted prompt string.
        """
        return f"""Break down the following content into micro-content for these platforms: {
            ', '.join(platforms)
        }

Target Language: {language}

## Title
{content.meta_title}

## Content
{content.optimized_content}

## Meta Description
{content.meta_description}

## SEO Keywords
{json.dumps(content.keyword_density, indent=2)}

Create platform-specific content for each platform listed above.
Adapt the tone, length, and format for each platform's best practices."""
