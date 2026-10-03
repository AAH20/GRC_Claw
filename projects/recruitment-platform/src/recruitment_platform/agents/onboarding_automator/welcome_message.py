"""Welcome message generation agent."""

from __future__ import annotations

from typing import Any

from recruitment_platform.agents.base import BaseAgent


class WelcomeMessage(BaseAgent[dict[str, Any], dict[str, str]]):
    """Generates personalized welcome messages for new hires.

    Creates customized welcome communications based on
    role, team, and company culture.
    """

    def __init__(self) -> None:
        """Initialize the welcome message agent."""
        super().__init__(name="welcome_message")

    async def process(self, input_data: dict[str, Any]) -> dict[str, str]:
        """Generate welcome message for a new hire.

        Args:
            input_data: Dictionary with 'employee' and 'team_info'.

        Returns:
            Personalized welcome message content.
        """
        return {"subject": "", "body": "", "email_html": ""}
