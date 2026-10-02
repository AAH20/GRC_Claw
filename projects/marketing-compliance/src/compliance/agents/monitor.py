"""Monitor agent: scans marketing content across integrated platforms."""

from __future__ import annotations

from typing import Any

from compliance.agents.base import AgentResult, BaseAgent

DEFAULT_SOURCES = ["salesforce", "hubspot", "mailchimp"]


class MonitorAgent(BaseAgent):
    """Continuously scans marketing content for compliance review.

    The monitor collects campaign and content artefacts from each configured
    source integration and forwards them downstream for detection. It is
    intentionally side-effect free: it only reads and normalises.
    """

    name = "monitor"

    async def run(self, payload: dict[str, Any]) -> AgentResult:
        """Scan configured sources and return normalised content items.

        Args:
            payload: Optional mapping containing:
                - ``sources``: list of source names to scan.
                - ``campaigns``: pre-fetched campaign payloads (used for
                  testing / offline operation).
                - ``batch_size``: maximum items to return.

        Returns:
            An :class:`AgentResult` whose ``items`` are normalised content
            records ready for the detect agent.
        """
        sources: list[str] = payload.get("sources", DEFAULT_SOURCES)
        batch_size: int = int(payload.get("batch_size", self.config.get("batch_size", 50)))
        campaigns: list[dict[str, Any]] = payload.get("campaigns", [])

        collected: list[dict[str, Any]] = []
        errors: list[str] = []

        for campaign in campaigns[:batch_size]:
            normalised = self._normalise(campaign)
            if normalised is None:
                errors.append(f"campaign missing required fields: {campaign.get('id', 'unknown')}")
                continue
            collected.append(normalised)

        return AgentResult(
            agent=self.name,
            items=collected,
            metrics={
                "sources_scanned": float(len(sources)),
                "items_collected": float(len(collected)),
                "items_skipped": float(len(errors)),
            },
            errors=errors,
        )

    @staticmethod
    def _normalise(campaign: dict[str, Any]) -> dict[str, Any] | None:
        """Normalise a raw campaign record.

        Args:
            campaign: Raw campaign payload from an integration.

        Returns:
            A normalised record, or ``None`` when required fields are absent.
        """
        content = campaign.get("content")
        campaign_id = campaign.get("id")
        if not content or not campaign_id:
            return None
        return {
            "id": str(campaign_id),
            "source": campaign.get("source", "unknown"),
            "content": str(content),
            "audience": campaign.get("audience", "unknown"),
            "channel": campaign.get("channel", "email"),
            "metadata": campaign.get("metadata", {}),
        }
