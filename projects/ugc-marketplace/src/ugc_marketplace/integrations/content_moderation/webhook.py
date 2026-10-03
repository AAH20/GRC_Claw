"""Webhook client for async moderation callbacks."""

from __future__ import annotations

import httpx
import structlog

from ugc_marketplace.models.schemas import ModerationResult

logger = structlog.get_logger(__name__)


class WebhookClient:
    """HTTP client for sending webhook callbacks."""

    def __init__(self, timeout: float = 10.0) -> None:
        """Initialize webhook client.

        Args:
            timeout: Request timeout in seconds.
        """
        self.timeout = timeout

    async def send_result(self, url: str, result: ModerationResult) -> bool:
        """Send moderation result to webhook URL.

        Args:
            url: Webhook endpoint URL.
            result: Moderation result to send.

        Returns:
            True if delivery succeeded, False otherwise.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=result.model_dump(mode="json"),
                    headers={"Content-Type": "application/json"},
                )
                success = response.is_success
                if success:
                    logger.info("Webhook delivered", url=url, result_id=str(result.id))
                else:
                    logger.warning(
                        "Webhook delivery failed",
                        url=url,
                        status_code=response.status_code,
                    )
                return success
        except httpx.HTTPError as exc:
            logger.error("Webhook delivery error", url=url, error=str(exc))
            return False
