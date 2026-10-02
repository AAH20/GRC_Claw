"""Skill database integration for skills-assessor."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx

from skills_assessor.models.schemas import Skill, SkillCategory

if TYPE_CHECKING:
    from skills_assessor.config.settings import Settings


class SkillDatabase:
    """Client for interacting with external skill databases.

    Provides methods to query and sync skill data from external sources
    such as O*NET, ESCO, or custom skill taxonomies.
    """

    def __init__(self, settings: Settings, base_url: str | None = None) -> None:
        """Initialize the skill database client.

        Args:
            settings: Application settings.
            base_url: Optional base URL for the skill database API.
        """
        self._settings = settings
        self._base_url = base_url or "https://api.example.com/skills"
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=30.0,
            headers={"Content-Type": "application/json"},
        )

    async def search_skills(
        self, query: str, category: SkillCategory | None = None, limit: int = 20
    ) -> list[Skill]:
        """Search for skills in the database.

        Args:
            query: Search query string.
            category: Optional category filter.
            limit: Maximum results to return.

        Returns:
            list[Skill]: Matching skills.
        """
        params: dict[str, Any] = {"q": query, "limit": limit}
        if category:
            params["category"] = category.value

        try:
            response = await self._client.get("/search", params=params)
            response.raise_for_status()
            data = response.json()
            return [Skill(**item) for item in data.get("results", [])]
        except httpx.HTTPError:
            return []

    async def get_skill_by_name(self, name: str) -> Skill | None:
        """Get a skill by its exact name.

        Args:
            name: The skill name to look up.

        Returns:
            Skill | None: The matching skill or None.
        """
        try:
            response = await self._client.get(f"/skills/{name}")
            response.raise_for_status()
            return Skill(**response.json())
        except httpx.HTTPError:
            return None

    async def get_related_skills(self, skill_id: str) -> list[Skill]:
        """Get skills related to the given skill.

        Args:
            skill_id: The skill identifier.

        Returns:
            list[Skill]: Related skills.
        """
        try:
            response = await self._client.get(f"/skills/{skill_id}/related")
            response.raise_for_status()
            data = response.json()
            return [Skill(**item) for item in data.get("related", [])]
        except httpx.HTTPError:
            return []

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
