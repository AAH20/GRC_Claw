"""Content Agent - Generates marketing content with compliance awareness."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class ContentRequest(BaseModel):
    """Request model for content generation."""

    content_type: str = Field(..., description="Type of content to generate")
    topic: str = Field(..., description="Subject matter for the content")
    tone: str = Field(default="professional", description="Desired tone")
    target_audience: str = Field(default="retail investors", description="Target audience")
    max_length: int = Field(default=1000, ge=50, le=5000, description="Maximum length")
    keywords: list[str] = Field(default_factory=list, description="SEO keywords")
    call_to_action: str | None = Field(default=None, description="Call-to-action text")


class ContentResponse(BaseModel):
    """Response model for generated content."""

    content: str = Field(..., description="Generated marketing content")
    content_id: str = Field(..., description="Unique content identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)
    compliance_status: str = Field(default="pending_review")


class ContentAgent:
    """Agent responsible for generating compliance-aware marketing content."""

    def __init__(self) -> None:
        """Initialize the Content Agent."""
        self.model = os.getenv("CONTENT_MODEL", "gpt-4")
        self.temperature = float(os.getenv("CONTENT_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("CONTENT_MAX_TOKENS", "2000"))
        self._required_disclosures = [
            "Investing involves risk including possible loss of principal.",
            "Past performance is not indicative of future results.",
        ]
        logger.info("Content Agent initialized", model=self.model)

    async def generate(self, request: ContentRequest) -> ContentResponse:
        """Generate marketing content based on the request.

        Args:
            request: Content generation request parameters.

        Returns:
            Generated content response with metadata.
        """
        logger.info("Generating content", content_type=request.content_type, topic=request.topic)
        prompt = self._build_prompt(request)
        generated_text = await self._call_llm(prompt)
        final_content = self._append_disclosures(generated_text)
        content_id = (
            f"content_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            f"_{abs(hash(request.topic)) % 10000:04d}"
        )
        return ContentResponse(
            content=final_content,
            content_id=content_id,
            metadata={
                "model": self.model,
                "temperature": self.temperature,
                "content_type": request.content_type,
                "word_count": len(final_content.split()),
            },
        )

    def _build_prompt(self, request: ContentRequest) -> str:
        """Build the LLM prompt for content generation."""
        parts = [
            f"Write a {request.tone} {request.content_type} about {request.topic}.",
            f"Target audience: {request.target_audience}.",
            f"Maximum length: {request.max_length} characters.",
        ]
        if request.keywords:
            parts.append(f"Include these keywords: {', '.join(request.keywords)}.")
        if request.call_to_action:
            parts.append(f"Call to action: {request.call_to_action}")
        parts.append(
            "\nIMPORTANT: This is for financial services marketing. "
            "Do not make guarantees about returns or use prohibited terms."
        )
        return "\n".join(parts)

    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM to generate content."""
        logger.debug("Calling LLM", prompt_length=len(prompt))
        return (
            "Generated content for your financial marketing campaign. "
            "This content has been created with compliance considerations in mind. "
            "Topic coverage includes key insights and actionable information "
            "for your target audience."
        )

    def _append_disclosures(self, content: str) -> str:
        """Append required regulatory disclosures to content."""
        if not any(d in content for d in self._required_disclosures):
            content += "\n\n" + " ".join(self._required_disclosures)
        return content

    async def revise(self, content_id: str, feedback: str) -> ContentResponse:
        """Revise content based on feedback."""
        logger.info("Revising content", content_id=content_id, feedback=feedback)
        return ContentResponse(
            content=f"Revised content based on feedback: {feedback}",
            content_id=content_id,
            metadata={"revision": True, "feedback": feedback},
        )
