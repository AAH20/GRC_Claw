"""Script Generation Agent.

Generates video scripts from topics, briefs, or campaign objectives.
Supports multiple formats: talking head, tutorial, product demo, and social clips.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class ScriptFormat(StrEnum):
    """Supported script formats."""

    TALKING_HEAD = "talking_head"
    TUTORIAL = "tutorial"
    PRODUCT_DEMO = "product_demo"
    SOCIAL_CLIP = "social_clip"
    INTERVIEW = "interview"
    STORY = "story"


class Tone(StrEnum):
    """Script tone options."""

    PROFESSIONAL = "professional"
    CASUAL = "casual"
    HUMOROUS = "humorous"
    EDUCATIONAL = "educational"
    INSPIRATIONAL = "inspirational"
    URGENT = "urgent"


@dataclass
class ScriptSection:
    """A single section of a video script."""

    title: str
    content: str
    duration_seconds: float
    visual_notes: str = ""
    b_roll_suggestions: list[str] = field(default_factory=list)


@dataclass
class VideoScript:
    """Complete video script with metadata."""

    title: str
    format: ScriptFormat
    tone: Tone
    target_duration_seconds: float
    sections: list[ScriptSection]
    target_audience: str = ""
    call_to_action: str = ""
    keywords: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_duration(self) -> float:
        """Calculate total script duration."""
        return sum(s.duration_seconds for s in self.sections)

    @property
    def word_count(self) -> int:
        """Calculate total word count."""
        return sum(len(s.content.split()) for s in self.sections)

    def to_dict(self) -> dict[str, Any]:
        """Convert script to dictionary representation."""
        return {
            "title": self.title,
            "format": self.format.value,
            "tone": self.tone.value,
            "target_duration_seconds": self.target_duration_seconds,
            "total_duration_seconds": self.total_duration,
            "word_count": self.word_count,
            "target_audience": self.target_audience,
            "call_to_action": self.call_to_action,
            "keywords": self.keywords,
            "sections": [
                {
                    "title": s.title,
                    "content": s.content,
                    "duration_seconds": s.duration_seconds,
                    "visual_notes": s.visual_notes,
                    "b_roll_suggestions": s.b_roll_suggestions,
                }
                for s in self.sections
            ],
            "metadata": self.metadata,
        }


class ScriptGenerationError(Exception):
    """Raised when script generation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


class ScriptGenerationAgent:
    """Agent responsible for generating video scripts.

    Uses LLM-based generation with structured output to create
    production-ready video scripts with timing, visual notes,
    and B-roll suggestions.
    """

    def __init__(
        self,
        llm_client: Any | None = None,
        default_tone: Tone = Tone.PROFESSIONAL,
        max_retries: int = 3,
    ) -> None:
        """Initialize the Script Generation Agent.

        Args:
            llm_client: Optional LLM client for script generation.
            default_tone: Default tone for generated scripts.
            max_retries: Maximum retry attempts on failure.
        """
        self._llm_client = llm_client
        self._default_tone = default_tone
        self._max_retries = max_retries
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def generate_script(
        self,
        topic: str,
        format: ScriptFormat = ScriptFormat.TALKING_HEAD,
        tone: Tone | None = None,
        target_duration: float = 60.0,
        target_audience: str = "",
        keywords: list[str] | None = None,
        context: str = "",
    ) -> VideoScript:
        """Generate a video script from a topic.

        Args:
            topic: The main topic or subject of the video.
            format: Script format type.
            tone: Script tone (defaults to agent default).
            target_duration: Target video duration in seconds.
            target_audience: Description of target audience.
            keywords: SEO/optimization keywords.
            context: Additional context or background information.

        Returns:
            A complete VideoScript object.

        Raises:
            ScriptGenerationError: If script generation fails.
            ValueError: If topic is empty or duration is invalid.
        """
        if not topic or not topic.strip():
            raise ValueError("Topic must be a non-empty string")
        if target_duration <= 0:
            raise ValueError("Target duration must be positive")

        tone = tone or self._default_tone
        keywords = keywords or []

        self._logger.info(
            "Generating script",
            extra={
                "topic": topic,
                "format": format.value,
                "tone": tone.value,
                "target_duration": target_duration,
            },
        )

        try:
            script = await self._generate_with_llm(
                topic=topic,
                format=format,
                tone=tone,
                target_duration=target_duration,
                target_audience=target_audience,
                keywords=keywords,
                context=context,
            )
            self._logger.info(
                "Script generated successfully",
                extra={
                    "title": script.title,
                    "sections": len(script.sections),
                    "duration": script.total_duration,
                },
            )
            return script
        except Exception as exc:
            self._logger.error("Script generation failed", exc_info=True)
            raise ScriptGenerationError(
                f"Failed to generate script for topic '{topic}': {exc}",
                details={"topic": topic, "format": format.value},
            ) from exc

    async def _generate_with_llm(
        self,
        topic: str,
        format: ScriptFormat,
        tone: Tone,
        target_duration: float,
        target_audience: str,
        keywords: list[str],
        context: str,
    ) -> VideoScript:
        """Generate script using LLM client.

        In production, this calls the LLM with structured output.
        Falls back to template-based generation if no LLM client.
        """
        if self._llm_client is not None:
            return await self._generate_with_llm_client(
                topic, format, tone, target_duration, target_audience, keywords, context
            )
        return self._generate_template(
            topic, format, tone, target_duration, target_audience, keywords
        )

    async def _generate_with_llm_client(
        self,
        topic: str,
        format: ScriptFormat,
        tone: Tone,
        target_duration: float,
        target_audience: str,
        keywords: list[str],
        context: str,
    ) -> VideoScript:
        """Generate script using the configured LLM client."""
        prompt = self._build_prompt(
            topic, format, tone, target_duration, target_audience, keywords, context
        )
        self._logger.debug("LLM prompt built", extra={"prompt_length": len(prompt)})

        # Placeholder for actual LLM call - would use langchain structured output
        # response = await self._llm_client.ainvoke(prompt)
        # return self._parse_llm_response(response)

        # Fallback to template for now
        return self._generate_template(
            topic, format, tone, target_duration, target_audience, keywords
        )

    def _build_prompt(
        self,
        topic: str,
        format: ScriptFormat,
        tone: Tone,
        target_duration: float,
        target_audience: str,
        keywords: list[str],
        context: str,
    ) -> str:
        """Build the LLM prompt for script generation."""
        return f"""Create a {format.value} video script about: {topic}

Tone: {tone.value}
Target Duration: {target_duration} seconds
Target Audience: {target_audience or 'General audience'}
Keywords: {', '.join(keywords) if keywords else 'None specified'}
Additional Context: {context or 'None'}

Provide the script with:
1. A compelling title
2. Multiple sections with timing
3. Visual notes for each section
4. B-roll suggestions
5. A clear call-to-action

Format the output as structured data."""

    def _generate_template(
        self,
        topic: str,
        format: ScriptFormat,
        tone: Tone,
        target_duration: float,
        target_audience: str,
        keywords: list[str],
    ) -> VideoScript:
        """Generate a template-based script (fallback when no LLM)."""
        intro_duration = min(10.0, target_duration * 0.15)
        body_duration = target_duration * 0.7
        cta_duration = target_duration - intro_duration - body_duration

        sections = [
            ScriptSection(
                title="Introduction",
                content=f"Welcome! Today we're exploring {topic}. "
                f"In this video, you'll discover key insights and actionable takeaways.",
                duration_seconds=intro_duration,
                visual_notes="Direct address to camera, engaging opening shot",
                b_roll_suggestions=[f"{topic} overview", "Setting/scene establishment"],
            ),
            ScriptSection(
                title="Main Content",
                content=f"Let's dive deep into {topic}. "
                f"We'll cover the essential aspects, best practices, and common pitfalls to avoid. "
                f"By the end, you'll have a clear understanding of how to apply these insights.",
                duration_seconds=body_duration,
                visual_notes="Mix of talking head and demonstration b-roll",
                b_roll_suggestions=[
                    f"{topic} demonstration",
                    "Step-by-step visuals",
                    "Data/statistics overlay",
                ],
            ),
            ScriptSection(
                title="Conclusion & CTA",
                content=f"That's a wrap on {topic}! "
                f"If you found this valuable, please like, share, and subscribe for more content. "
                f"Leave a comment below with your questions or experiences.",
                duration_seconds=cta_duration,
                visual_notes="Return to direct address, end screen with subscribe button",
                b_roll_suggestions=["End screen", "Subscribe animation"],
            ),
        ]

        return VideoScript(
            title=f"{topic.title()} - Complete Guide",
            format=format,
            tone=tone,
            target_duration_seconds=target_duration,
            sections=sections,
            target_audience=target_audience,
            call_to_action="Like, share, and subscribe for more content",
            keywords=keywords,
            metadata={"generated_by": "template", "topic": topic},
        )

    def refine_script(
        self,
        script: VideoScript,
        feedback: str,
    ) -> VideoScript:
        """Refine an existing script based on feedback.

        Args:
            script: The original script to refine.
            feedback: Feedback for improvements.

        Returns:
            A refined VideoScript.

        Raises:
            ScriptGenerationError: If refinement fails.
        """
        self._logger.info("Refining script", extra={"title": script.title, "feedback": feedback})
        # Production: would send script + feedback to LLM for revision
        # For now, return the original with updated metadata
        script.metadata["refined"] = True
        script.metadata["feedback"] = feedback
        return script

    def estimate_production_time(self, script: VideoScript) -> dict[str, float]:
        """Estimate production time breakdown for a script.

        Args:
            script: The video script to estimate.

        Returns:
            Dictionary with time estimates in hours for each phase.
        """
        duration_minutes = script.total_duration / 60
        return {
            "pre_production_hours": duration_minutes * 0.5,
            "filming_hours": duration_minutes * 2.0,
            "editing_hours": duration_minutes * 3.0,
            "post_production_hours": duration_minutes * 1.5,
            "total_hours": duration_minutes * 7.0,
        }
