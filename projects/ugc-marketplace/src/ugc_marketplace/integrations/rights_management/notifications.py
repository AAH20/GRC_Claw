"""Notification service for rights management."""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)


class NotificationService:
    """Service for sending rights management notifications."""

    async def notify_license_created(self, license_id: str, content_id: str) -> None:
        """Notify about license creation.

        Args:
            license_id: License identifier.
            content_id: Content identifier.
        """
        logger.info(
            "License created notification", license_id=license_id, content_id=content_id
        )

    async def notify_infringement_detected(
        self,
        report_id: str,
        content_id: str,
        severity: str = "medium",
    ) -> None:
        """Notify about infringement detection.

        Args:
            report_id: Report identifier.
            content_id: Content identifier.
            severity: Severity level.
        """
        logger.warning(
            "Infringement detected notification",
            report_id=report_id,
            content_id=content_id,
            severity=severity,
        )

    async def notify_takedown_processed(
        self,
        request_id: str,
        content_id: str,
        action: str = "removed",
    ) -> None:
        """Notify about takedown processing.

        Args:
            request_id: Request identifier.
            content_id: Content identifier.
            action: Action taken.
        """
        logger.info(
            "Takedown processed notification",
            request_id=request_id,
            content_id=content_id,
            action=action,
        )
