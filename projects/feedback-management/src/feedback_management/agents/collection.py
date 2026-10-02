"""Feedback Collection Agent - gathers feedback from multiple platforms."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog
from pydantic import BaseModel, Field

from feedback_management.integrations.google_forms import GoogleFormsIntegration
from feedback_management.integrations.surveymonkey import SurveyMonkeyIntegration
from feedback_management.integrations.typeform import TypeformIntegration

logger = structlog.get_logger(__name__)


class FeedbackItem(BaseModel):
    """Represents a single feedback item collected from any source."""

    id: str
    source: str
    platform: str
    customer_id: str | None = None
    customer_email: str | None = None
    rating: float | None = None
    text: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    language: str = "en"
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    raw_data: dict[str, Any] = Field(default_factory=dict)


class CollectionResult(BaseModel):
    """Result of a feedback collection run."""

    success: bool
    items_collected: int = 0
    errors: list[str] = Field(default_factory=list)
    platform_results: dict[str, dict[str, Any]] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


class CollectionAgent:
    """Agent responsible for collecting feedback from survey and review platforms.

    This agent orchestrates data collection from SurveyMonkey, Typeform,
    Google Forms, and other integrated platforms. It handles pagination,
    rate limiting, and data normalization.
    """

    def __init__(
        self,
        surveymonkey_integration: SurveyMonkeyIntegration | None = None,
        typeform_integration: TypeformIntegration | None = None,
        google_forms_integration: GoogleFormsIntegration | None = None,
    ) -> None:
        """Initialize the Collection Agent.

        Args:
            surveymonkey_integration: SurveyMonkey API integration instance.
            typeform_integration: Typeform API integration instance.
            google_forms_integration: Google Forms API integration instance.
        """
        self.surveymonkey = surveymonkey_integration or SurveyMonkeyIntegration()
        self.typeform = typeform_integration or TypeformIntegration()
        self.google_forms = google_forms_integration or GoogleFormsIntegration()
        self._platforms = {
            "surveymonkey": self.surveymonkey,
            "typeform": self.typeform,
            "google_forms": self.google_forms,
        }

    async def collect_all(
        self,
        since: datetime | None = None,
        platforms: list[str] | None = None,
        max_items: int = 100,
    ) -> CollectionResult:
        """Collect feedback from all configured platforms.

        Args:
            since: Only collect feedback after this datetime.
            platforms: List of platform names to collect from. If None, collects from all.
            max_items: Maximum number of items to collect per platform.

        Returns:
            CollectionResult with collected items and any errors.
        """
        result = CollectionResult(success=True)
        target_platforms = platforms or list(self._platforms.keys())
        since = since or datetime.now(timezone.utc) - timedelta(days=7)

        tasks = [
            self._collect_platform(name, since, max_items, result)
            for name in target_platforms
            if name in self._platforms
        ]

        await asyncio.gather(*tasks, return_exceptions=True)
        result.completed_at = datetime.now(timezone.utc)

        if result.errors:
            logger.warning(
                "Collection completed with errors",
                errors=len(result.errors),
                items=result.items_collected,
            )
        else:
            logger.info("Collection completed successfully", items=result.items_collected)

        return result

    async def _collect_platform(
        self,
        platform_name: str,
        since: datetime,
        max_items: int,
        result: CollectionResult,
    ) -> None:
        """Collect feedback from a single platform.

        Args:
            platform_name: Name of the platform to collect from.
            since: Only collect feedback after this datetime.
            max_items: Maximum items to collect.
            result: CollectionResult to update in-place.
        """
        integration = self._platforms[platform_name]
        try:
            logger.info("Collecting feedback from platform", platform=platform_name)
            items = await integration.collect_feedback(since=since, max_items=max_items)

            result.items_collected += len(items)
            result.platform_results[platform_name] = {
                "items": len(items),
                "status": "success",
            }

            logger.info(
                "Platform collection complete",
                platform=platform_name,
                items=len(items),
            )
        except Exception as exc:
            error_msg = f"Failed to collect from {platform_name}: {exc}"
            result.errors.append(error_msg)
            result.platform_results[platform_name] = {
                "items": 0,
                "status": "error",
                "error": str(exc),
            }
            logger.error("Platform collection failed", platform=platform_name, error=str(exc))

    async def collect_single(
        self,
        platform: str,
        feedback_id: str,
    ) -> FeedbackItem | None:
        """Collect a single feedback item by ID from a specific platform.

        Args:
            platform: Platform name to collect from.
            feedback_id: The ID of the feedback item.

        Returns:
            FeedbackItem if found, None otherwise.
        """
        if platform not in self._platforms:
            raise ValueError(f"Unknown platform: {platform}")

        integration = self._platforms[platform]
        try:
            item = await integration.get_feedback_by_id(feedback_id)
            return item
        except Exception as exc:
            logger.error(
                "Failed to collect single feedback item",
                platform=platform,
                feedback_id=feedback_id,
                error=str(exc),
            )
            return None
