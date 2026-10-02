"""Social media marketing agent."""

from __future__ import annotations

from typing import Any

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ecommerce_marketing.config import get_settings

logger = structlog.get_logger(__name__)


class SocialPost(BaseModel):
    """Social media post data model."""

    id: str = Field(..., description="Post identifier")
    platform: str = Field(
        ..., description="Target platform (twitter, facebook, instagram, linkedin)"
    )
    content: str = Field(..., description="Post content text")
    hashtags: list[str] = Field(default_factory=list, description="Hashtags for the post")
    media_urls: list[str] = Field(default_factory=list, description="Media attachment URLs")
    scheduled_at: str | None = Field(default=None, description="Scheduled publish time")
    status: str = Field(default="draft", description="Post status")


class SocialPostRequest(BaseModel):
    """Request model for creating a social media post."""

    platform: str = Field(..., description="Target platform")
    topic: str = Field(..., description="Post topic or theme")
    tone: str = Field(default="professional", description="Tone of the post")
    include_hashtags: bool = Field(default=True, description="Whether to include hashtags")
    max_length: int = Field(default=280, ge=50, le=500, description="Maximum post length")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context")


class SocialAgent:
    """AI agent for social media content creation and scheduling.

    Generates platform-optimized social media posts with appropriate
    hashtags, tone, and formatting for each platform.
    """

    PLATFORM_LIMITS: dict[str, int] = {
        "twitter": 280,
        "facebook": 63206,
        "instagram": 2200,
        "linkedin": 3000,
    }

    def __init__(self, llm: BaseChatModel | None = None) -> None:
        """Initialize the social media agent.

        Args:
            llm: Optional LangChain chat model. If not provided, uses the default
                model from settings.
        """
        self.settings = get_settings()
        self.llm = llm or self._create_default_llm()
        self._prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert social media marketer. "
                    "Create engaging, platform-optimized content that drives engagement. "
                    "Adapt tone, length, and formatting for each platform. "
                    "Include relevant hashtags when appropriate. "
                    "Output valid JSON with content, hashtags, and media_suggestions fields.",
                ),
                (
                    "human",
                    "Platform: {platform}\n"
                    "Topic: {topic}\n"
                    "Tone: {tone}\n"
                    "Max length: {max_length}\n"
                    "Include hashtags: {include_hashtags}\n"
                    "Context: {context}\n\n"
                    "Create a social media post optimized for {platform}.",
                ),
            ]
        )

    def _create_default_llm(self) -> BaseChatModel:
        """Create the default LLM from settings.

        Returns:
            Configured LangChain chat model.

        Raises:
            ValueError: If OPENAI_API_KEY is not configured.
        """
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as exc:
            raise ImportError(
                "langchain-openai is required for default LLM. "
                "Install with: pip install langchain-openai"
            ) from exc

        if not self.settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for social media posts")

        return ChatOpenAI(
            model=self.settings.openai_model,
            api_key=self.settings.openai_api_key,
            temperature=0.8,
            max_tokens=1000,
        )

    async def create_post(self, request: SocialPostRequest) -> SocialPost:
        """Create a social media post optimized for the target platform.

        Args:
            request: Social post creation request.

        Returns:
            Created social media post.

        Raises:
            ValueError: If the platform is not supported or request is invalid.
        """
        if request.platform not in self.PLATFORM_LIMITS:
            raise ValueError(
                f"Unsupported platform: {request.platform}. "
                f"Supported: {', '.join(self.PLATFORM_LIMITS.keys())}"
            )

        # Enforce platform-specific length limits
        max_length = min(request.max_length, self.PLATFORM_LIMITS[request.platform])

        logger.info(
            "Creating social post",
            platform=request.platform,
            topic=request.topic,
            tone=request.tone,
        )

        chain = self._prompt | self.llm
        response = await chain.ainvoke(
            {
                "platform": request.platform,
                "topic": request.topic,
                "tone": request.tone,
                "max_length": max_length,
                "include_hashtags": request.include_hashtags,
                "context": str(request.context),
            }
        )

        post = self._parse_post(
            response.content if hasattr(response, "content") else str(response),
            request.platform,
            max_length,
        )

        logger.info(
            "Social post created",
            post_id=post.id,
            platform=post.platform,
        )

        return post

    def _parse_post(self, llm_output: str, platform: str, max_length: int) -> SocialPost:
        """Parse LLM output into a social media post.

        Args:
            llm_output: Raw text output from the LLM.
            platform: Target platform.
            max_length: Maximum post length.

        Returns:
            Parsed social media post.
        """
        import json
        import uuid

        try:
            data = json.loads(llm_output)
            content = data.get("content", "")
            # Truncate if necessary
            if len(content) > max_length:
                content = content[: max_length - 3] + "..."

            return SocialPost(
                id=str(uuid.uuid4()),
                platform=platform,
                content=content,
                hashtags=data.get("hashtags", []),
                media_urls=data.get("media_suggestions", []),
                status="draft",
            )
        except (json.JSONDecodeError, KeyError):
            logger.warning("Failed to parse social post, using fallback")
            return SocialPost(
                id=str(uuid.uuid4()),
                platform=platform,
                content=f"Check out our latest updates! #{platform}",
                hashtags=[platform],
                status="draft",
            )

    def get_optimal_posting_times(self, platform: str) -> list[str]:
        """Get optimal posting times for a platform.

        Args:
            platform: Social media platform.

        Returns:
            List of optimal posting times in ISO format.
        """
        # Simplified optimal times - in production, this would use analytics data
        optimal_times: dict[str, list[str]] = {
            "twitter": ["09:00", "12:00", "17:00"],
            "facebook": ["09:00", "13:00", "15:00"],
            "instagram": ["11:00", "13:00", "19:00"],
            "linkedin": ["08:00", "12:00", "17:00"],
        }
        return optimal_times.get(platform, ["09:00", "12:00", "17:00"])
