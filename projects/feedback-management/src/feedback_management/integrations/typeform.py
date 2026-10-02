"""Typeform integration for feedback collection."""
from __future__ import annotations

from datetime import datetime
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class TypeformIntegration:
    """Integration with Typeform for feedback collection."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    async def collect_feedback(
        self,
        since: datetime | None = None,
        max_items: int = 100,
    ) -> list[dict[str, Any]]:
        """Collect feedback from Typeform."""
        logger.info("Collecting feedback from Typeform")
        return []

    async def get_feedback_by_id(self, feedback_id: str) -> dict[str, Any] | None:
        """Get a single feedback item by ID."""
        logger.info("Getting feedback from Typeform", feedback_id=feedback_id)
        return None
