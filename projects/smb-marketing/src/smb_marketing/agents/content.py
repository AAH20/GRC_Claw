"""Content generation agent for creating marketing copy and content."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class ContentType(StrEnum):
    """Supported content types."""

    BLOG_POST = "blog_post"
    AD_COPY = "ad_copy"
    PRODUCT_DESCRIPTION = "product_description"
    SOCIAL_CAPTION = "social_caption"
    EMAIL_BODY = "email_body"


class ContentTone(StrEnum):
    """Supported content tones."""

    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"


class ContentRequest(BaseModel):
    """Request model for content generation.

    Attributes:
        content_type: Type of content to generate.
        topic: Subject matter for the content.
        tone: Desired tone of voice.
        max_length: Maximum character length of generated content.
        keywords: Optional SEO keywords to include.
        target_audience: Optional target audience description.
    """

    content_type: ContentType
    topic: str = Field(..., min_length=1, max_length=500)
    tone: ContentTone = ContentTone.PROFESSIONAL
    max_length: int = Field(default=2000, ge=50, le=10000)
    keywords: list[str] = Field(default_factory=list)
    target_audience: str | None = None


class ContentResponse(BaseModel):
    """Response model for generated content.

    Attributes:
        content: The generated marketing content.
        content_type: Type of content generated.
        word_count: Number of words in the generated content.
        metadata: Additional metadata about the generation.
    """

    content: str
    content_type: ContentType
    word_count: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContentAgent:
    """AI agent for generating marketing content.

    Uses LLM-powered pipelines to produce blog posts, ad copy,
    product descriptions, social media captions, and email bodies.
    """

    def __init__(self, llm_client: Any | None = None) -> None:
        """Initialize the ContentAgent.

        Args:
            llm_client: Optional LLM client for content generation.
        """
        self._llm_client = llm_client
        self._logger = logger.bind(agent="content")

    async def generate(self, request: ContentRequest) -> ContentResponse:
        """Generate marketing content based on the request.

        Args:
            request: Content generation parameters.

        Returns:
            Generated content with metadata.

        Raises:
            ValueError: If the request parameters are invalid.
        """
        self._logger.info(
            "Generating content",
            content_type=request.content_type.value,
            topic=request.topic,
        )

        prompt = self._build_prompt(request)
        content = await self._call_llm(prompt, request.max_length)

        word_count = len(content.split())

        self._logger.info(
            "Content generated successfully",
            word_count=word_count,
            content_type=request.content_type.value,
        )

        return ContentResponse(
            content=content,
            content_type=request.content_type,
            word_count=word_count,
            metadata={
                "tone": request.tone.value,
                "keywords_used": request.keywords,
            },
        )

    def _build_prompt(self, request: ContentRequest) -> str:
        """Build the LLM prompt for content generation.

        Args:
            request: Content generation parameters.

        Returns:
            Formatted prompt string.
        """
        parts = [
            f"Write a {request.content_type.value.replace('_', ' ')} "
            f"about '{request.topic}' in a {request.tone.value} tone.",
        ]

        if request.target_audience:
            parts.append(f"Target audience: {request.target_audience}")

        if request.keywords:
            keywords_str = ", ".join(request.keywords)
            parts.append(f"Include these keywords naturally: {keywords_str}")

        parts.append(f"Maximum length: {request.max_length} characters.")

        return "\n".join(parts)

    async def _call_llm(self, prompt: str, max_length: int) -> str:
        """Call the LLM to generate content.

        Args:
            prompt: The formatted prompt.
            max_length: Maximum response length.

        Returns:
            Generated text from the LLM.

        Raises:
            RuntimeError: If the LLM call fails.
        """
        if self._llm_client is None:
            # Fallback for testing/demo without an LLM client
            return (
                f"This is generated content for your marketing needs. "
                f"Topic: {prompt[:100]}... "
                f"(Connect an LLM client for AI-powered generation)"
            )

        try:
            response = await self._llm_client.ainvoke(
                prompt,
                max_tokens=max_length // 4,  # Approximate token-to-char ratio
            )
            return str(response.content if hasattr(response, "content") else response)
        except Exception as exc:
            self._logger.error("LLM call failed", error=str(exc))
            raise RuntimeError(f"Content generation failed: {exc}") from exc
