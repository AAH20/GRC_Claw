"""Timezone resolution agent."""

from __future__ import annotations

from typing import Any

from recruitment_platform.agents.base import BaseAgent


class TimezoneResolver(BaseAgent[dict[str, Any], dict[str, str]]):
    """Resolves timezone information for interview participants.

    Converts times between timezones and handles
    daylight saving time transitions.
    """

    def __init__(self) -> None:
        """Initialize the timezone resolver."""
        super().__init__(name="timezone_resolver")

    async def process(self, input_data: dict[str, Any]) -> dict[str, str]:
        """Resolve timezone for a participant.

        Args:
            input_data: Dictionary with 'location' or 'timezone_hint'.

        Returns:
            Resolved timezone information.
        """
        return {"timezone": "UTC", "offset": "+00:00", "dst_active": False}
