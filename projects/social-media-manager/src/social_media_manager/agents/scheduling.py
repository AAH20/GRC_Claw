"""Scheduling agent — plans optimal posting windows."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from social_media_manager.agents.base import BaseAgent

# Best-effort engagement windows (UTC hours) per platform.
OPTIMAL_HOURS: dict[str, list[int]] = {
    "twitter": [8, 12, 17],
    "instagram": [11, 14, 19],
    "facebook": [9, 13, 16],
    "linkedin": [7, 10, 15],
    "tiktok": [6, 15, 21],
}

DEFAULT_WINDOW = [9, 13, 18]


class SchedulingAgent(BaseAgent):
    """Builds a posting schedule across one or more platforms."""

    name = "scheduling"
    description = "Plans optimal posting times and builds content calendars"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Produce a schedule of posting slots.

        Args:
            payload: Must contain ``platforms`` (list) and ``start_date``
                (ISO-8601 string). Optional: ``posts_per_day``, ``posts``
                (list of content items to assign).

        Returns:
            Dictionary with ``schedule`` (list of slots) and ``summary``.

        Raises:
            ValueError: If inputs are missing or malformed.
        """
        platforms = self._require(payload, "platforms")
        start_raw = self._require(payload, "start_date")

        if not isinstance(platforms, list) or not platforms:
            raise ValueError("'platforms' must be a non-empty list")

        try:
            start = datetime.fromisoformat(str(start_raw).replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"Invalid start_date '{start_raw}': {exc}") from exc

        if start.tzinfo is None:
            start = start.replace(tzinfo=UTC)

        posts_per_day = int(payload.get("posts_per_day", 1))
        if posts_per_day < 1:
            raise ValueError("'posts_per_day' must be >= 1")

        posts = payload.get("posts", [])
        if posts and not isinstance(posts, list):
            raise ValueError("'posts' must be a list when provided")

        schedule: list[dict[str, Any]] = []
        post_iter = iter(posts)
        for platform in platforms:
            platform_key = str(platform).lower()
            hours = OPTIMAL_HOURS.get(platform_key, DEFAULT_WINDOW)
            for day in range(posts_per_day):
                hour = hours[day % len(hours)]
                slot_time = (start + timedelta(days=day)).replace(
                    hour=hour, minute=0, second=0, microsecond=0
                )
                item = next(post_iter, None)
                schedule.append(
                    {
                        "platform": platform_key,
                        "scheduled_at": slot_time.isoformat(),
                        "optimal_hour_utc": hour,
                        "content_id": (item or {}).get("id") if item else None,
                    }
                )

        schedule.sort(key=lambda s: s["scheduled_at"])
        return {
            "schedule": schedule,
            "summary": {
                "total_slots": len(schedule),
                "platforms": [str(p).lower() for p in platforms],
                "start_date": start.isoformat(),
                "posts_per_day": posts_per_day,
            },
        }
