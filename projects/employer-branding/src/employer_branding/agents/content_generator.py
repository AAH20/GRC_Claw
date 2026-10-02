"""Content Generator Agent for creating employer brand content."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from employer_branding.agents.base import BaseAgent
from employer_branding.models import BrandAsset, ContentGenerationRequest, ContentTone, ContentType


class ContentGeneratorAgent(BaseAgent[BrandAsset]):
    """Agent that generates employer brand content using AI.

    Creates various types of content including job postings, social media posts,
    blog articles, and more, tailored to specific tones and target audiences.
    """

    def __init__(self) -> None:
        """Initialize the content generator agent."""
        super().__init__()
        self._prompt_template = self._build_prompt_template()

    def _build_prompt_template(self) -> ChatPromptTemplate:
        """Build the prompt template for content generation.

        Returns:
            Configured ChatPromptTemplate.
        """
        system_message = """You are an expert employer branding content creator.
You craft compelling, authentic content that attracts top talent and showcases
company culture. Your content is inclusive, engaging, and aligned with the
employer's brand voice and values.

Guidelines:
- Use clear, jargon-free language
- Highlight unique value propositions
- Maintain authenticity and avoid clichés
- Include diverse perspectives
- Follow the specified tone precisely
- Optimize for the target platform/format"""

        return ChatPromptTemplate.from_messages([
            SystemMessage(content=system_message),
            HumanMessage(content="{input}"),
        ])

    async def run(self, request: ContentGenerationRequest) -> BrandAsset:
        """Generate brand content based on the request.

        Args:
            request: Content generation request with type, topic, tone, etc.

        Returns:
            Generated BrandAsset with content.

        Raises:
            ValueError: If request parameters are invalid.
            RuntimeError: If content generation fails.
        """
        self.logger.info(
            "generating_content",
            content_type=request.content_type.value,
            topic=request.topic,
            tone=request.tone.value,
        )

        try:
            prompt = self._build_generation_prompt(request)
            response = await self._model.ainvoke(prompt)
            content = response.content if hasattr(response, "content") else str(response)

            asset = BrandAsset(
                title=self._generate_title(request),
                content=content,
                content_type=request.content_type,
                tone=request.tone,
                language=request.language,
                tags=request.keywords,
                target_audience=request.target_audience,
                metadata={
                    "generated_by": "ContentGeneratorAgent",
                    "model": self._settings.openai_model,
                    "topic": request.topic,
                },
            )

            self.logger.info("content_generated", asset_id=str(asset.id))
            return asset

        except Exception as exc:
            self.logger.error("content_generation_failed", error=str(exc))
            raise RuntimeError(f"Failed to generate content: {exc}") from exc

    def _build_generation_prompt(self, request: ContentGenerationRequest) -> str:
        """Build the generation prompt from request parameters.

        Args:
            request: Content generation request.

        Returns:
            Formatted prompt string.
        """
        parts = [
            f"Create a {request.content_type.value.replace('_', ' ')} about: {request.topic}",
            f"Tone: {request.tone.value}",
            f"Language: {request.language}",
            f"Maximum length: {request.max_length} characters",
        ]

        if request.keywords:
            parts.append(f"Include these keywords: {', '.join(request.keywords)}")
        if request.target_audience:
            parts.append(f"Target audience: {request.target_audience}")
        if request.additional_context:
            parts.append(f"Additional context: {request.additional_context}")

        return "\n".join(parts)

    def _generate_title(self, request: ContentGenerationRequest) -> str:
        """Generate a title for the content.

        Args:
            request: Content generation request.

        Returns:
            Generated title string.
        """
        type_labels = {
            ContentType.JOB_POSTING: "Job Opportunity",
            ContentType.SOCIAL_MEDIA: "Social Post",
            ContentType.BLOG_POST: "Blog Article",
            ContentType.EMPLOYER_VIDEO_SCRIPT: "Video Script",
            ContentType.CAREERS_PAGE: "Careers Page",
            ContentType.EMAIL_CAMPAIGN: "Email Campaign",
            ContentType.PRESS_RELEASE: "Press Release",
        }
        label = type_labels.get(request.content_type, "Content")
        return f"{label}: {request.topic[:80]}"
