"""Notification service for rights-management events."""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)


class NotificationService:
    """Service for dispatching notifications about rights-management events.

    This is a stub implementation that logs events. In production,
    integrate with email, Slack, webhooks, or a message queue.
    """

    async def notify_license_created(self, license_id: str, content_id: str) -> None:
        """Notify that a new license has been created.

        Args:
            license_id: The license identifier.
            content_id: The content identifier.
        """
        logger.info("license_created", license_id=license_id, content_id=content_id)

    async def notify_infringement_detected(
        self,
        content_id: str,
        risk_score: float,
    ) -> None:
        """Notify that a potential infringement has been detected.

        Args:
            content_id: The content identifier.
            risk_score: The detected risk score.
        """
        logger.warning(
            "infringement_detected",
            content_id=content_id,
            risk_score=risk_score,
        )

    async def notify_takedown_processed(
        self,
        request_id: str,
        status: str,
    ) -> None:
        """Notify that a takedown request has been processed.

        Args:
            request_id: The takedown request identifier.
            status: The resulting status.
        """
        logger.info("takedown_processed", request_id=request_id, status=status)
