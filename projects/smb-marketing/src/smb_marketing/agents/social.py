"""Social media agent for scheduling and publishing posts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class SocialPlatform(StrEnum):
    """Supported social media platforms."""

    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"


class PostStatus(StrEnum):
    """Social media post statuses."""

    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
    DRAFT = "draft"


class SocialPostRequest(BaseModel):
    """Request model for scheduling a social media post.

    Attributes:
        content: Post text content.
        platform: Target social platform.
        scheduled_time: When to publish the post.
        media_urls: Optional media attachments.
        hashtags: Optional hashtags to include.
    """

    content: str = Field(..., min_length=1, max_length=5000)
    platform: SocialPlatform
    scheduled_time: datetime
    media_urls: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)


class SocialPostResponse(BaseModel):
    """Response model for social media post operations.

    Attributes:
        id: Unique post identifier.
        content: Post content.
        platform: Target platform.
        status: Current post status.
        scheduled_time: Scheduled publish time.
        published_time: Actual publish time (if published).
    """

    id: str
    content: str
    platform: SocialPlatform
    status: PostStatus
    scheduled_time: datetime
    published_time: datetime | None = None


class SocialAgent:
    """AI agent for social media management.

    Handles post scheduling, publishing, hashtag optimization,
    and best-time analysis for Meta platforms.
    """

    def __init__(
        self,
        meta_client: Any | None = None,
        llm_client: Any | None = None,
    ) -> None:
        """Initialize the SocialAgent.

        Args:
            meta_client: Optional Meta API client.
            llm_client: Optional LLM client for content optimization.
        """
        self._meta_client = meta_client
        self._llm_client = llm_client
        self._logger = logger.bind(agent="social")
        self._posts: dict[str, SocialPostResponse] = {}

    async def schedule_post(self, request: SocialPostRequest) -> SocialPostResponse:
        """Schedule a social media post.

        Args:
            request: Post scheduling parameters.

        Returns:
            The scheduled post response.

        Raises:
            ValueError: If the scheduled time is in the past.
        """
        if request.scheduled_time < datetime.utcnow():
            raise ValueError("Scheduled time must be in the future")

        self._logger.info(
            "Scheduling social post",
            platform=request.platform.value,
            scheduled_time=request.scheduled_time.isoformat(),
        )

        post_id = self._generate_post_id()

        post = SocialPostResponse(
            id=post_id,
            content=request.content,
            platform=request.platform,
            status=PostStatus.SCHEDULED,
            scheduled_time=request.scheduled_time,
        )

        self._posts[post_id] = post

        self._logger.info("Social post scheduled", post_id=post_id)
        return post

    async def publish_post(self, post_id: str) -> SocialPostResponse:
        """Publish a scheduled post immediately.

        Args:
            post_id: Unique post identifier.

        Returns:
            The published post response.

        Raises:
            KeyError: If the post is not found.
        """
        if post_id not in self._posts:
            raise KeyError(f"Post not found: {post_id}")

        post = self._posts[post_id]

        if self._meta_client:
            try:
                # Publish via Meta API
                await self._meta_client.publish_post(
                    content=post.content,
                    platform=post.platform,
                )
                post.status = PostStatus.PUBLISHED
                post.published_time = datetime.utcnow()
            except Exception as exc:
                post.status = PostStatus.FAILED
                self._logger.error("Failed to publish post", error=str(exc))
                raise RuntimeError(f"Failed to publish post: {exc}") from exc
        else:
            # Simulate publishing for testing
            post.status = PostStatus.PUBLISHED
            post.published_time = datetime.utcnow()

        self._logger.info("Post published", post_id=post_id)
        return post

    async def get_post(self, post_id: str) -> SocialPostResponse:
        """Retrieve a post by ID.

        Args:
            post_id: Unique post identifier.

        Returns:
            The post response.

        Raises:
            KeyError: If the post is not found.
        """
        if post_id not in self._posts:
            raise KeyError(f"Post not found: {post_id}")
        return self._posts[post_id]

    async def list_posts(
        self,
        platform: SocialPlatform | None = None,
        status: PostStatus | None = None,
    ) -> list[SocialPostResponse]:
        """List posts with optional filters.

        Args:
            platform: Optional platform filter.
            status: Optional status filter.

        Returns:
            List of post responses.
        """
        posts = list(self._posts.values())
        if platform:
            posts = [p for p in posts if p.platform == platform]
        if status:
            posts = [p for p in posts if p.status == status]
        return posts

    def optimize_hashtags(self, content: str, max_tags: int = 10) -> list[str]:
        """Generate optimized hashtags for content.

        Args:
            content: Post content to analyze.
            max_tags: Maximum number of hashtags.

        Returns:
            List of recommended hashtags.
        """
        # Simple keyword extraction — replace with LLM-powered analysis
        words = content.lower().split()
        common_words = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at"}
        keywords = [w for w in words if w not in common_words and len(w) > 3]
        hashtags = [f"#{kw}" for kw in keywords[:max_tags]]
        return hashtags

    def _generate_post_id(self) -> str:
        """Generate a unique post identifier.

        Returns:
            Unique post ID string.
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        return f"post_{timestamp}"
