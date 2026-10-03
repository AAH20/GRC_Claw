"""License detector agent for rights management."""

from __future__ import annotations

import time
from typing import Any

from langchain.agents import create_agent

from ugc_marketplace.agents.rights_management.base import BaseAgent
from ugc_marketplace.agents.rights_management.types import (
    LicenseDetectionRequest,
    LicenseDetectionResult,
)


class LicenseDetectorAgent(
    BaseAgent["LicenseDetectionRequest", "LicenseDetectionResult"]
):
    """Agent that detects and validates content licenses.

    Analyzes content to determine licensing status, detect
    expired or invalid licenses, and verify usage rights.
    """

    def _build_agent(self) -> Any:
        """Build the LangChain agent for license detection.

        Returns:
            Configured agent instance.
        """
        tools = [
            self._check_license_status,
            self._verify_usage_rights,
            self._detect_expired_licenses,
        ]

        agent = create_agent(
            tools=tools,
            instructions=(
                "You are a license detection and validation specialist. "
                "Analyze content to determine licensing status, verify usage "
                "rights, and detect expired or invalid licenses."
            ),
        )
        return agent

    async def execute(
        self, input_data: LicenseDetectionRequest
    ) -> LicenseDetectionResult:
        """Execute license detection.

        Args:
            input_data: Detection request with content to analyze.

        Returns:
            License detection result.
        """
        start_time = time.monotonic()
        result = await self._timed_execute(input_data, "execute")
        elapsed_ms = (time.monotonic() - start_time) * 1000
        return result

    async def _timed_execute(self, input_data: Any, method_name: str) -> Any:
        """Execute with timing.

        Args:
            input_data: Input data.
            method_name: Method name.

        Returns:
            Agent output.
        """
        return await self.execute(input_data)

    @staticmethod
    async def _check_license_status(content_id: str) -> dict[str, Any]:
        """Check license status for content.

        Args:
            content_id: Content identifier.

        Returns:
            License status data.
        """
        return {"content_id": content_id, "license_status": "unknown"}

    @staticmethod
    async def _verify_usage_rights(content_id: str, usage_type: str) -> dict[str, Any]:
        """Verify usage rights for content.

        Args:
            content_id: Content identifier.
            usage_type: Type of usage.

        Returns:
            Usage rights verification result.
        """
        return {"content_id": content_id, "usage_type": usage_type, "authorized": False}

    @staticmethod
    async def _detect_expired_licenses(content_id: str) -> dict[str, Any]:
        """Detect expired licenses.

        Args:
            content_id: Content identifier.

        Returns:
            Expired license detection result.
        """
        return {"content_id": content_id, "expired": False}
