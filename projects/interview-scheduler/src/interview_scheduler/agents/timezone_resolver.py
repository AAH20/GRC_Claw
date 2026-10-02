"""Timezone Resolver Agent using LangChain DeepAgents."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import pytz
from dateutil import parser as date_parser

logger = logging.getLogger(__name__)


class TimezoneResolverAgent:
    """Agent responsible for resolving and converting timezones.

    Uses LangChain DeepAgents to intelligently handle timezone conversions,
    detect ambiguous times, and resolve participant timezone preferences.
    """

    def __init__(self) -> None:
        """Initialize the Timezone Resolver Agent."""
        self._agent: Any = None

    async def _get_agent(self) -> Any:
        """Lazy-initialize the LangChain DeepAgent."""
        if self._agent is None:
            try:
                from langchain_deepagents import create_deep_agent

                self._agent = create_deep_agent(
                    tools=[self._convert_time_tool, self._validate_timezone_tool],
                    instructions=(
                        "You are a timezone resolution agent. Convert times between "
                        "timezones accurately, handle DST transitions, and validate "
                        "timezone identifiers."
                    ),
                )
            except ImportError:
                logger.warning("langchain-deepagents not available, using direct timezone calls")
                self._agent = None
        return self._agent

    async def _convert_time_tool(
        self, time_str: str, from_tz: str, to_tz: str
    ) -> str:
        """Tool for converting time between timezones."""
        dt = date_parser.parse(time_str)
        from_zone = pytz.timezone(from_tz)
        to_zone = pytz.timezone(to_tz)
        localized = from_zone.localize(dt)
        converted = localized.astimezone(to_zone)
        return converted.isoformat()

    async def _validate_timezone_tool(self, timezone: str) -> bool:
        """Tool for validating a timezone identifier."""
        return self.is_valid_timezone(timezone)

    def is_valid_timezone(self, timezone: str) -> bool:
        """Check if a timezone identifier is valid.

        Args:
            timezone: IANA timezone identifier (e.g., "America/New_York").

        Returns:
            True if valid, False otherwise.
        """
        try:
            pytz.timezone(timezone)
            return True
        except pytz.UnknownTimeZoneError:
            return False

    def convert_time(
        self,
        dt: datetime,
        from_timezone: str,
        to_timezone: str,
    ) -> datetime:
        """Convert a datetime from one timezone to another.

        Args:
            dt: The datetime to convert.
            from_timezone: Source timezone.
            to_timezone: Target timezone.

        Returns:
            Converted datetime.

        Raises:
            ValueError: If either timezone is invalid.
        """
        if not self.is_valid_timezone(from_timezone):
            raise ValueError(f"Invalid source timezone: {from_timezone}")
        if not self.is_valid_timezone(to_timezone):
            raise ValueError(f"Invalid target timezone: {to_timezone}")

        from_zone = pytz.timezone(from_timezone)
        to_zone = pytz.timezone(to_timezone)

        localized = from_zone.localize(dt) if dt.tzinfo is None else dt.astimezone(from_zone)
        return localized.astimezone(to_zone)

    def resolve_participant_timezone(
        self,
        preferred_timezones: list[str],
        default_timezone: str = "UTC",
    ) -> str:
        """Resolve the best timezone from participant preferences.

        Args:
            preferred_timezones: List of preferred timezone identifiers.
            default_timezone: Fallback timezone if none are valid.

        Returns:
            The first valid timezone from preferences, or the default.
        """
        for tz in preferred_timezones:
            if self.is_valid_timezone(tz):
                return tz
        return default_timezone

    def get_utc_offset(self, timezone: str, dt: datetime | None = None) -> int:
        """Get the UTC offset in minutes for a timezone.

        Args:
            timezone: IANA timezone identifier.
            dt: Optional datetime for DST-aware offset calculation.

        Returns:
            Offset in minutes from UTC.
        """
        if not self.is_valid_timezone(timezone):
            raise ValueError(f"Invalid timezone: {timezone}")
        zone = pytz.timezone(timezone)
        if dt is None:
            dt = datetime.now()
        if dt.tzinfo is None:
            dt = zone.localize(dt)
        offset = dt.utcoffset()
        return int(offset.total_seconds() / 60) if offset else 0

    def find_common_business_hours(
        self,
        timezones: list[str],
        business_start: int = 9,
        business_end: int = 17,
    ) -> dict[str, tuple[int, int]]:
        """Find overlapping business hours across multiple timezones.

        Args:
            timezones: List of timezone identifiers.
            business_start: Business start hour (0-23).
            business_end: Business end hour (0-23).

        Returns:
            Dict mapping timezone to (start_hour, end_hour) in local time.
        """
        result: dict[str, tuple[int, int]] = {}
        for tz in timezones:
            if not self.is_valid_timezone(tz):
                continue
            # Simple approximation: find hours that overlap with UTC business hours
            now = datetime.now(pytz.UTC)
            local_now = now.astimezone(pytz.timezone(tz))
            offset_hours = local_now.utcoffset().total_seconds() / 3600  # type: ignore[union-attr]
            utc_start = business_start
            utc_end = business_end
            local_start = int((utc_start + offset_hours) % 24)
            local_end = int((utc_end + offset_hours) % 24)
            result[tz] = (local_start, local_end)
        return result

    def normalize_to_utc(self, dt: datetime, timezone: str) -> datetime:
        """Normalize a datetime to UTC.

        Args:
            dt: The datetime to normalize.
            timezone: The timezone of the datetime.

        Returns:
            Datetime in UTC.
        """
        return self.convert_time(dt, timezone, "UTC")
