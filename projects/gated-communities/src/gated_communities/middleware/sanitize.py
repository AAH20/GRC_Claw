"""Input sanitization utilities."""

from __future__ import annotations

import html
import re
from typing import Any


def sanitize_string(value: str) -> str:
    """Sanitize a string value."""
    value = value.replace("\x00", "")
    value = html.escape(value)
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)
    return value.strip()


def sanitize_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively sanitize dictionary values."""
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_string(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_string(v) if isinstance(v, str) else v for v in value
            ]
        else:
            sanitized[key] = value
    return sanitized


def sanitize_html(value: str, allowed_tags: list[str] | None = None) -> str:
    """Sanitize HTML content, allowing only specified tags."""
    if allowed_tags is None:
        allowed_tags = [
            "p",
            "br",
            "strong",
            "em",
            "u",
            "h1",
            "h2",
            "h3",
            "ul",
            "ol",
            "li",
        ]
    pattern = r"<(?!/?({})\b)[^>]*>".format("|".join(allowed_tags))
    value = re.sub(pattern, "", value)
    return value
