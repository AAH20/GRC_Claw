"""Content Creation agent — generates platform-aware post copy."""

from __future__ import annotations

from typing import Any

from social_media_manager.agents.base import BaseAgent

PLATFORM_LIMITS: dict[str, int] = {
    "twitter": 280,
    "instagram": 2200,
    "facebook": 63206,
    "linkedin": 3000,
    "tiktok": 2200,
}


class ContentCreationAgent(BaseAgent):
    """Generates social post copy, hashtags and calls-to-action.

    The agent enforces per-platform character limits and produces a
    deterministic draft that downstream tooling (or an LLM) can refine.
    """

    name = "content_creation"
    description = "Generates platform-optimised post copy, hashtags and CTAs"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a draft post for a given topic and platform.

        Args:
            payload: Must contain ``topic`` and ``platform``. Optional keys:
                ``tone``, ``audience``, ``keywords``, ``include_hashtags``.

        Returns:
            Dictionary with ``content``, ``hashtags``, ``cta`` and ``platform``.

        Raises:
            ValueError: If ``topic``/``platform`` is missing or unsupported.
        """
        topic = self._require(payload, "topic")
        platform = str(self._require(payload, "platform")).lower()

        if platform not in PLATFORM_LIMITS:
            raise ValueError(
                f"Unsupported platform '{platform}'. "
                f"Valid options: {', '.join(sorted(PLATFORM_LIMITS))}"
            )

        tone = payload.get("tone", "professional")
        audience = payload.get("audience", "general audience")
        keywords = payload.get("keywords", [])
        include_hashtags = bool(payload.get("include_hashtags", True))

        if not isinstance(keywords, list):
            raise ValueError("'keywords' must be a list of strings")

        body = (
            f"{topic.strip().capitalize()} — crafted for {audience} "
            f"with a {tone} tone."
        )
        hashtags = self._build_hashtags(keywords, topic) if include_hashtags else []
        cta = self._build_cta(platform)

        limit = PLATFORM_LIMITS[platform]
        content = body
        if hashtags:
            content = f"{body}\n\n{' '.join(hashtags)}"
        if len(content) > limit:
            content = content[: limit - 3].rstrip() + "..."

        return {
            "platform": platform,
            "content": content,
            "hashtags": hashtags,
            "cta": cta,
            "character_count": len(content),
            "character_limit": limit,
            "tone": tone,
            "audience": audience,
        }

    @staticmethod
    def _build_hashtags(keywords: list[Any], topic: str) -> list[str]:
        """Derive a deduplicated, sanitised hashtag list."""
        raw = [str(k).strip() for k in keywords] or topic.split()
        seen: set[str] = set()
        tags: list[str] = []
        for item in raw:
            tag = "#" + "".join(ch for ch in item.title() if ch.isalnum())
            if len(tag) > 1 and tag.lower() not in seen:
                seen.add(tag.lower())
                tags.append(tag)
        return tags[:8]

    @staticmethod
    def _build_cta(platform: str) -> str:
        """Return a platform-appropriate call to action."""
        return {
            "twitter": "Repost if you agree 🔁",
            "instagram": "Double tap if this resonates ❤️",
            "facebook": "Share your thoughts in the comments 👇",
            "linkedin": "Follow for more insights.",
            "tiktok": "Follow for part two!",
        }.get(platform, "Learn more at the link in bio.")
