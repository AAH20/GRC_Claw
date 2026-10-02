"""Applicant Tracking System (ATS) API client."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import date

from recruitment_analytics.integrations.base import BaseAPIClient


class ATSClient(BaseAPIClient):
    """Client for interacting with the ATS API."""

    async def get_candidates(
        self,
        start_date: date,
        end_date: date,
        department: str | None = None,
        role: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch candidates from ATS within date range."""
        params: dict[str, Any] = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        if department:
            params["department"] = department
        if role:
            params["role"] = role
        result = await self.get("/v1/candidates", params=params)
        return result.get("data", [])

    async def get_funnel_data(
        self,
        start_date: date,
        end_date: date,
        department: str | None = None,
        role: str | None = None,
    ) -> dict[str, Any]:
        """Fetch funnel stage data from ATS."""
        params: dict[str, Any] = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        if department:
            params["department"] = department
        if role:
            params["role"] = role
        return await self.get("/v1/funnel", params=params)

    async def get_sources(
        self,
        start_date: date,
        end_date: date,
    ) -> list[dict[str, Any]]:
        """Fetch source tracking data from ATS."""
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        result = await self.get("/v1/sources", params=params)
        return result.get("data", [])

    async def get_diversity_data(
        self,
        start_date: date,
        end_date: date,
        department: str | None = None,
    ) -> dict[str, Any]:
        """Fetch diversity data from ATS."""
        params: dict[str, Any] = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        if department:
            params["department"] = department
        return await self.get("/v1/diversity", params=params)
