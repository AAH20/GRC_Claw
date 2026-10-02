"""Content generation agent for marketing copy, emails, and social media."""

from __future__ import annotations

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class ContentRequest(BaseModel):
    """Request model for content generation."""

    content_type: str = Field(..., description="Type of content: email, social, blog, ad")
    topic: str = Field(..., description="Subject or topic of the content")
    tone: str = Field(default="professional", description="Tone: professional, casual, friendly")
    target_audience: str = Field(..., description="Target audience description")
    length: str = Field(default="medium", description="Length: short, medium, long")
    keywords: list[str] = Field(default_factory=list, description="SEO keywords to include")
    call_to_action: str | None = Field(default=None, description="Desired call to action")


class ContentResponse(BaseModel):
    """Response model for generated content."""

    content: str = Field(..., description="Generated marketing content")
    content_type: str = Field(..., description="Type of content generated")
    word_count: int = Field(..., description="Word count of generated content")
    metadata: dict[str, str] = Field(default_factory=dict, description="Additional metadata")


class ContentAgent:
    """Agent responsible for generating marketing content.

    Uses LLM-powered generation to create email sequences, social media posts,
    blog articles, and ad copy tailored to SaaS PLG audiences.
    """

    SUPPORTED_TYPES = {"email", "social", "blog", "ad"}
    SUPPORTED_TONES = {"professional", "casual", "friendly", "authoritative"}
    SUPPORTED_LENGTHS = {"short", "medium", "long"}

    def __init__(self, model: str = "gpt-4", temperature: float = 0.7) -> None:
        """Initialize the ContentAgent.

        Args:
            model: LLM model identifier to use for generation.
            temperature: Sampling temperature for generation.
        """
        self.model = model
        self.temperature = temperature
        self._initialized = True
        logger.info("content_agent_initialized", model=model)

    async def generate(self, request: ContentRequest) -> ContentResponse:
        """Generate marketing content based on the request.

        Args:
            request: Content generation parameters.

        Returns:
            Generated content with metadata.

        Raises:
            ValueError: If content_type, tone, or length is unsupported.
        """
        self._validate_request(request)

        logger.info(
            "generating_content",
            content_type=request.content_type,
            topic=request.topic,
            tone=request.tone,
        )

        # In production, this would call an LLM via LangChain DeepAgents
        content = self._generate_mock_content(request)

        word_count = len(content.split())

        logger.info(
            "content_generated",
            content_type=request.content_type,
            word_count=word_count,
        )

        return ContentResponse(
            content=content,
            content_type=request.content_type,
            word_count=word_count,
            metadata={
                "model": self.model,
                "tone": request.tone,
                "target_audience": request.target_audience,
            },
        )

    def _validate_request(self, request: ContentRequest) -> None:
        """Validate the content generation request.

        Args:
            request: Request to validate.

        Raises:
            ValueError: If any parameter is invalid.
        """
        if request.content_type not in self.SUPPORTED_TYPES:
            raise ValueError(
                f"Unsupported content_type: {request.content_type}. "
                f"Must be one of {self.SUPPORTED_TYPES}"
            )
        if request.tone not in self.SUPPORTED_TONES:
            raise ValueError(
                f"Unsupported tone: {request.tone}. Must be one of {self.SUPPORTED_TONES}"
            )
        if request.length not in self.SUPPORTED_LENGTHS:
            raise ValueError(
                f"Unsupported length: {request.length}. Must be one of {self.SUPPORTED_LENGTHS}"
            )

    def _generate_mock_content(self, request: ContentRequest) -> str:
        """Generate placeholder content for development/testing.

        In production, replace with actual LLM call via LangChain DeepAgents.

        Args:
            request: Content generation parameters.

        Returns:
            Generated content string.
        """
        templates = {
            "email": (
                f"Subject: Unlock the Power of {request.topic}\n\n"
                f"Hi there,\n\n"
                f"Discover how {request.topic} can transform your workflow. "
                f"Join thousands of teams already benefiting from our platform.\n\n"
                f"{request.call_to_action or 'Get started today!'}\n\n"
                f"Best regards,\nThe Team"
            ),
            "social": (
                f"🚀 Excited about {request.topic}? "
                f"Here's why teams love it: ✅ Easy setup ✅ Powerful analytics "
                f"✅ Seamless integrations\n\n"
                f"{request.call_to_action or 'Try it free today!'}"
            ),
            "blog": (
                f"# {request.topic}: A Comprehensive Guide\n\n"
                f"In this article, we explore how {request.topic} is changing "
                f"the way modern SaaS teams operate.\n\n"
                f"## Key Benefits\n\n"
                f"- Increased productivity\n- Better collaboration\n- Measurable results\n\n"
                f"## Getting Started\n\n"
                f"{request.call_to_action or 'Start your free trial now.'}"
            ),
            "ad": (
                f"{request.topic} — Built for {request.target_audience}\n\n"
                f"Streamline your workflow. Boost your metrics. Scale faster.\n\n"
                f"{request.call_to_action or 'Start Free Trial'}"
            ),
        }
        return templates[request.content_type]
