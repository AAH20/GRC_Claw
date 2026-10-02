"""Human Resource Management System (HRMS) API client."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from recruitment_analytics.integrations.base import BaseAPIClient


class HRMSClient(BaseAPIClient):
    """Client for interacting with the HRMS API."""

    async def get_hiring_costs(
        self,
        start_date: date,
        end_date: date,
        department: str | None = None,
    ) -> dict[str, Any]:
        """Fetch hiring cost data from HRMS."""
        params: dict[str, Any] = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        if department:
            params["department"] = department
        return await self.get("/v1/costs", params=params)

    async def get_employee_demographics(
        self,
        department: str | None = None,
    ) -> dict[str, Any]:
        """Fetch employee demographic data from HRMS."""
        params: dict[str, Any] = {}
        if department:
            params["department"] = department
        return await self.get("/v1/demographics", params=params)

    async def get_budget_data(
        self,
        start_date: date,
        end_date: date,
        department: str | None = None,
    ) -> dict[str, Any]:
        """Fetch budget data from HRMS."""
        params: dict[str, Any] = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        if department:
            params["department"] = department
        return await self.get("/v1/budgets", params=params)

    async def get_performance_data(
        self,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        """Fetch performance data for predictive hiring."""
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        result = await self.get("/v1/performance", params=params)
        return result.get("data", [])
