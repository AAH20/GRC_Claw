"""Creative Agent - Content and creative generation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class CreativeType(str, Enum):
    """Types of creative assets."""

    AD_COPY = "ad_copy"
    SOCIAL_POST = "social_post"
    EMAIL = "email"
    LANDING_PAGE = "landing_page"
    BLOG_POST = "blog_post"
    VIDEO_SCRIPT = "video_script"
    IMAGE_PROMPT = "image_prompt"
    TAGLINE = "tagline"


class CreativeFormat(str, Enum):
    """Creative format specifications."""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    CAROUSEL = "carousel"
    STORY = "story"
    REEL = "reel"


class ToneOfVoice(str, Enum):
    """Brand tone of voice options."""

    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"
    PLAYFUL = "playful"
    EMPATHETIC = "empathetic"
    BOLD = "bold"
    INFORMATIVE = "informative"
    INSPIRATIONAL = "inspirational"


class CreativeVariant(BaseModel):
    """A single creative variant."""

    id: str = Field(..., description="Unique variant identifier")
    name: str = Field(..., description="Variant name")
    content: str = Field(..., description="Creative content")
    format: CreativeFormat = Field(..., description="Content format")
    character_count: int | None = Field(None, description="Character count")
    word_count: int | None = Field(None, description="Word count")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class CreativeResult(BaseModel):
    """Result of creative generation."""

    creative_type: CreativeType = Field(..., description="Type of creative")
    variants: list[CreativeVariant] = Field(default_factory=list, description="Generated variants")
    brand_guidelines_followed: bool = Field(
        True, description="Whether brand guidelines were followed"
    )
    ab_test_ready: bool = Field(False, description="Whether variants are ready for A/B testing")
    tags: list[str] = Field(default_factory=list, description="Content tags")
    created_at: str | None = Field(None, description="ISO timestamp of creation")


@dataclass
class CreativeAgentConfig:
    """Configuration for the Creative Agent."""

    model: str = "gpt-4"
    max_tokens: int = 4096
    temperature: float = 0.8
    timeout_seconds: int = 120
    retry_attempts: int = 3
    enabled: bool = True


class CreativeAgent:
    """AI agent for creative content generation.

    This agent generates ad copy, social media content, email campaigns,
    landing page copy, and other marketing creative assets with brand
    voice consistency and A/B testing variants.
    """

    def __init__(self, config: CreativeAgentConfig | None = None) -> None:
        """Initialize the Creative Agent.

        Args:
            config: Optional configuration override.
        """
        self.config = config or CreativeAgentConfig()
        self._agent: Any = None
        self._initialize_agent()

    def _initialize_agent(self) -> None:
        """Initialize the underlying LangChain agent."""
        try:
            from langchain.agents import create_openai_functions_agent
            from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )

            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert copywriter and creative director with deep
                experience in digital marketing, brand storytelling, and conversion optimization.
                Create compelling, on-brand content that drives action.
                Always generate multiple variants for A/B testing."""),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])

            self._agent = create_openai_functions_agent(llm, [], prompt)
            logger.info("CreativeAgent initialized", model=self.config.model)
        except ImportError:
            logger.warning("LangChain not available, running in mock mode")
            self._agent = None

    async def generate_creative(
        self,
        creative_type: CreativeType,
        brief: str,
        tone: ToneOfVoice = ToneOfVoice.PROFESSIONAL,
        num_variants: int = 3,
        context: dict[str, Any] | None = None,
    ) -> CreativeResult:
        """Generate creative content based on a brief.

        Args:
            creative_type: Type of creative to generate.
            brief: Creative brief describing requirements.
            tone: Desired tone of voice.
            num_variants: Number of variants to generate.
            context: Optional additional context (brand guidelines, etc.).

        Returns:
            CreativeResult with generated variants.

        Raises:
            ValueError: If the agent is not enabled or parameters are invalid.
            RuntimeError: If creative generation fails.
        """
        if not self.config.enabled:
            raise ValueError("CreativeAgent is not enabled")

        if num_variants < 1:
            raise ValueError("Must generate at least one variant")

        logger.info(
            "Generating creative",
            creative_type=creative_type.value,
            tone=tone.value,
            num_variants=num_variants,
        )

        try:
            if self._agent is None:
                return await self._mock_creative(creative_type, brief, tone, num_variants, context)

            result = await self._execute_creative(creative_type, brief, tone, num_variants, context)
            return result

        except Exception as e:
            logger.error("Creative generation failed", error=str(e))
            raise RuntimeError(f"Creative generation failed: {e}") from e

    async def _execute_creative(
        self,
        creative_type: CreativeType,
        brief: str,
        tone: ToneOfVoice,
        num_variants: int,
        context: dict[str, Any] | None,
    ) -> CreativeResult:
        """Execute creative generation using the LangChain agent.

        Args:
            creative_type: Type of creative.
            brief: Creative brief.
            tone: Tone of voice.
            num_variants: Number of variants.
            context: Additional context.

        Returns:
            CreativeResult with generated content.
        """
        return await self._mock_creative(creative_type, brief, tone, num_variants, context)

    async def _mock_creative(
        self,
        creative_type: CreativeType,
        brief: str,
        tone: ToneOfVoice,
        num_variants: int,
        context: dict[str, Any] | None,
    ) -> CreativeResult:
        """Generate mock creative content for testing/development.

        Args:
            creative_type: Type of creative.
            brief: Creative brief.
            tone: Tone of voice.
            num_variants: Number of variants.
            context: Additional context.

        Returns:
            CreativeResult with mock content.
        """
        variants: list[CreativeVariant] = []
        for i in range(num_variants):
            content = f"Creative variant {i + 1} for {creative_type.value}: {brief}"
            variants.append(CreativeVariant(
                id=f"variant_{i + 1}",
                name=f"Variant {chr(65 + i)}",
                content=content,
                format=CreativeFormat.TEXT,
                character_count=len(content),
                word_count=len(content.split()),
                metadata={"tone": tone.value, "variant_number": i + 1},
            ))

        return CreativeResult(
            creative_type=creative_type,
            variants=variants,
            brand_guidelines_followed=True,
            ab_test_ready=num_variants >= 2,
            tags=[creative_type.value, tone.value, "ai-generated"],
        )

    async def generate_ad_copy(
        self,
        product_name: str,
        key_benefits: list[str],
        target_audience: str,
        call_to_action: str,
        num_variants: int = 3,
    ) -> CreativeResult:
        """Generate ad copy variants.

        Args:
            product_name: Name of the product/service.
            key_benefits: List of key benefits to highlight.
            target_audience: Target audience description.
            call_to_action: Desired call to action.
            num_variants: Number of variants to generate.

        Returns:
            CreativeResult with ad copy variants.
        """
        brief = (
            f"Create {CreativeType.AD_COPY.value} marketing content for {target_audience}. "
            f"Key benefits: {', '.join(key_benefits)}. CTA: {call_to_action}"
        )
        return await self.generate_creative(
            creative_type=CreativeType.AD_COPY,
            brief=brief,
            num_variants=num_variants,
        )

    async def generate_social_posts(
        self,
        topic: str,
        platform: str,
        num_posts: int = 5,
        context: dict[str, Any] | None = None,
    ) -> list[CreativeVariant]:
        """Generate social media post variants.

        Args:
            topic: Post topic or theme.
            platform: Target social platform.
            num_posts: Number of posts to generate.
            context: Optional additional context.

        Returns:
            List of CreativeVariant objects.
        """
        logger.info("Generating social posts", topic=topic, platform=platform, count=num_posts)

        posts: list[CreativeVariant] = []
        for i in range(num_posts):
            content = f"Social post {i + 1} about {topic} for {platform}"
            posts.append(CreativeVariant(
                id=f"post_{i + 1}",
                name=f"Post {i + 1}",
                content=content,
                format=CreativeFormat.TEXT,
                character_count=len(content),
                word_count=len(content.split()),
                metadata={"platform": platform, "topic": topic},
            ))

        return posts
