"""Distribution Agent.

Manages video distribution across multiple platforms including
YouTube, TikTok, Instagram, and custom channels.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class Platform(StrEnum):
    """Supported distribution platforms."""

    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    VIMEO = "vimeo"
    CUSTOM = "custom"


class DistributionStatus(StrEnum):
    """Distribution status."""

    PENDING = "pending"
    SCHEDULED = "scheduled"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    PUBLISHED = "published"
    FAILED = "failed"
    UNLISTED = "unlisted"
    PRIVATE = "private"


class VideoVisibility(StrEnum):
    """Video visibility options."""

    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"
    SCHEDULED = "scheduled"


@dataclass
class PlatformConfig:
    """Configuration for a platform distribution."""

    platform: Platform
    enabled: bool = True
    api_key: str = ""
    api_secret: str = ""
    access_token: str = ""
    refresh_token: str = ""
    default_visibility: VideoVisibility = VideoVisibility.PUBLIC
    default_tags: list[str] = field(default_factory=list)
    auto_publish: bool = False
    custom_settings: dict[str, Any] = field(default_factory=dict)


@dataclass
class Distribution:
    """A single distribution record."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    video_id: str = ""
    platform: Platform = Platform.YOUTUBE
    status: DistributionStatus = DistributionStatus.PENDING
    platform_video_id: str = ""
    platform_url: str = ""
    title: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    visibility: VideoVisibility = VideoVisibility.PUBLIC
    scheduled_time: datetime | None = None
    published_time: datetime | None = None
    error_message: str = ""
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_published(self) -> bool:
        """Check if distribution is published."""
        return self.status == DistributionStatus.PUBLISHED

    @property
    def can_retry(self) -> bool:
        """Check if distribution can be retried."""
        return self.status == DistributionStatus.FAILED and self.retry_count < self.max_retries

    def to_dict(self) -> dict[str, Any]:
        """Convert distribution to dictionary."""
        return {
            "id": self.id,
            "video_id": self.video_id,
            "platform": self.platform.value,
            "status": self.status.value,
            "platform_video_id": self.platform_video_id,
            "platform_url": self.platform_url,
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "visibility": self.visibility.value,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "published_time": self.published_time.isoformat() if self.published_time else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "can_retry": self.can_retry,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }


class DistributionError(Exception):
    """Raised when a distribution operation fails."""

    def __init__(self, message: str, distribution_id: str | None = None) -> None:
        super().__init__(message)
        self.distribution_id = distribution_id


class DistributionAgent:
    """Agent responsible for distributing videos across platforms.

    Manages multi-platform distribution with scheduling, retry logic,
    and platform-specific optimizations.
    """

    def __init__(self, storage_backend: Any | None = None) -> None:
        """Initialize the Distribution Agent.

        Args:
            storage_backend: Optional storage backend for persistence.
        """
        self._storage = storage_backend
        self._distributions: dict[str, Distribution] = {}
        self._platform_configs: dict[Platform, PlatformConfig] = {}
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def configure_platform(self, config: PlatformConfig) -> None:
        """Configure a distribution platform.

        Args:
            config: Platform configuration.
        """
        self._platform_configs[config.platform] = config
        self._logger.info(
            "Platform configured",
            extra={"platform": config.platform.value, "enabled": config.enabled},
        )

    async def distribute(
        self,
        video_id: str,
        platforms: list[Platform],
        title: str = "",
        description: str = "",
        tags: list[str] | None = None,
        visibility: VideoVisibility = VideoVisibility.PUBLIC,
        scheduled_time: datetime | None = None,
    ) -> list[Distribution]:
        """Distribute a video to multiple platforms.

        Args:
            video_id: The video ID to distribute.
            platforms: Target platforms.
            title: Video title.
            description: Video description.
            tags: Video tags.
            visibility: Video visibility.
            scheduled_time: Optional scheduled publish time.

        Returns:
            List of Distribution records.

        Raises:
            DistributionError: If distribution fails.
        """
        if not video_id:
            raise DistributionError("Video ID is required")
        if not platforms:
            raise DistributionError("At least one platform must be specified")

        distributions: list[Distribution] = []

        for platform in platforms:
            config = self._platform_configs.get(platform)
            if config and not config.enabled:
                self._logger.warning(
                    "Skipping disabled platform",
                    extra={"platform": platform.value, "video_id": video_id},
                )
                continue

            distribution = Distribution(
                video_id=video_id,
                platform=platform,
                title=title,
                description=description,
                tags=tags or [],
                visibility=visibility,
                scheduled_time=scheduled_time,
                status=(
                    DistributionStatus.SCHEDULED
                    if scheduled_time
                    else DistributionStatus.PENDING
                ),
            )

            self._distributions[distribution.id] = distribution
            distributions.append(distribution)

            self._logger.info(
                "Distribution created",
                extra={
                    "distribution_id": distribution.id,
                    "video_id": video_id,
                    "platform": platform.value,
                },
            )

        return distributions

    async def get_distribution(self, distribution_id: str) -> Distribution:
        """Get a distribution by ID.

        Args:
            distribution_id: The distribution ID.

        Returns:
            The Distribution object.

        Raises:
            DistributionError: If not found.
        """
        if distribution_id not in self._distributions:
            raise DistributionError(
                f"Distribution '{distribution_id}' not found",
                distribution_id=distribution_id,
            )
        return self._distributions[distribution_id]

    async def update_status(
        self,
        distribution_id: str,
        status: DistributionStatus,
        platform_video_id: str = "",
        platform_url: str = "",
        error_message: str = "",
    ) -> Distribution:
        """Update distribution status.

        Args:
            distribution_id: The distribution ID.
            status: New status.
            platform_video_id: Platform-assigned video ID.
            platform_url: Platform video URL.
            error_message: Error message if failed.

        Returns:
            Updated Distribution.

        Raises:
            DistributionError: If not found.
        """
        distribution = await self.get_distribution(distribution_id)

        distribution.status = status
        distribution.updated_at = datetime.now(UTC)

        if platform_video_id:
            distribution.platform_video_id = platform_video_id
        if platform_url:
            distribution.platform_url = platform_url
        if error_message:
            distribution.error_message = error_message

        if status == DistributionStatus.PUBLISHED:
            distribution.published_time = datetime.now(UTC)
        elif status == DistributionStatus.FAILED:
            distribution.retry_count += 1

        self._logger.info(
            "Distribution status updated",
            extra={
                "distribution_id": distribution_id,
                "status": status.value,
                "platform": distribution.platform.value,
            },
        )
        return distribution

    async def retry(self, distribution_id: str) -> Distribution:
        """Retry a failed distribution.

        Args:
            distribution_id: The distribution ID.

        Returns:
            Updated Distribution.

        Raises:
            DistributionError: If not found or cannot retry.
        """
        distribution = await self.get_distribution(distribution_id)

        if not distribution.can_retry:
            raise DistributionError(
                f"Distribution '{distribution_id}' cannot be retried "
                f"(status: {distribution.status.value}, retries: {distribution.retry_count})",
                distribution_id=distribution_id,
            )

        distribution.status = DistributionStatus.PENDING
        distribution.error_message = ""
        distribution.updated_at = datetime.now(UTC)

        self._logger.info(
            "Distribution retry initiated",
            extra={"distribution_id": distribution_id, "platform": distribution.platform.value},
        )
        return distribution

    async def list_distributions(
        self,
        video_id: str | None = None,
        platform: Platform | None = None,
        status: DistributionStatus | None = None,
    ) -> list[Distribution]:
        """List distributions with optional filters.

        Args:
            video_id: Filter by video ID.
            platform: Filter by platform.
            status: Filter by status.

        Returns:
            List of Distribution objects.
        """
        distributions = list(self._distributions.values())

        if video_id is not None:
            distributions = [d for d in distributions if d.video_id == video_id]
        if platform is not None:
            distributions = [d for d in distributions if d.platform == platform]
        if status is not None:
            distributions = [d for d in distributions if d.status == status]

        return sorted(distributions, key=lambda d: d.created_at, reverse=True)

    async def get_platform_stats(self, video_id: str) -> dict[str, Any]:
        """Get distribution stats for a video across platforms.

        Args:
            video_id: The video ID.

        Returns:
            Dictionary with platform distribution stats.
        """
        distributions = await self.list_distributions(video_id=video_id)

        stats: dict[str, Any] = {
            "video_id": video_id,
            "total_platforms": len(distributions),
            "published": 0,
            "pending": 0,
            "failed": 0,
            "scheduled": 0,
            "platforms": {},
        }

        for d in distributions:
            if d.is_published:
                stats["published"] += 1
            elif d.status == DistributionStatus.FAILED:
                stats["failed"] += 1
            elif d.status == DistributionStatus.SCHEDULED:
                stats["scheduled"] += 1
            else:
                stats["pending"] += 1

            stats["platforms"][d.platform.value] = {
                "status": d.status.value,
                "url": d.platform_url,
                "published_time": d.published_time.isoformat() if d.published_time else None,
            }

        return stats
