"""HRMS (Human Resource Management System) client integration."""

from __future__ import annotations

import logging
from typing import Any

from recruitment_platform.integrations.base import BaseIntegration

logger = logging.getLogger(__name__)


class HRMSClient(BaseIntegration):
    """Client for interacting with HRMS platforms.

    Syncs employee data, organizational structure,
    and other HR information.
    """

    def __init__(self, base_url: str, api_key: str) -> None:
        """Initialize the HRMS client.

        Args:
            base_url: Base URL for the HRMS API.
            api_key: API key for authentication.
        """
        super().__init__(base_url=base_url, api_key=api_key)

    async def get_employees(self) -> list[dict[str, Any]]:
        """Get all employees.

        Returns:
            List of employee records.
        """
        response = await self.get("/employees")
        return response.json().get("employees", [])

    async def get_departments(self) -> list[dict[str, Any]]:
        """Get organizational departments.

        Returns:
            List of department records.
        """
        response = await self.get("/departments")
        return response.json().get("departments", [])

    async def create_employee(self, employee_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new employee record.

        Args:
            employee_data: Employee details.

        Returns:
            Created employee record.
        """
        response = await self.post("/employees", json=employee_data)
        return response.json()

    async def get_org_chart(self) -> dict[str, Any]:
        """Get organizational chart.

        Returns:
            Organizational hierarchy.
        """
        response = await self.get("/org-chart")
        return response.json()

    async def health_check(self) -> bool:
        """Check if the HRMS is available.

        Returns:
            True if the service is healthy.
        """
        try:
            await self.get("/health")
            return True
        except Exception:
            return False
