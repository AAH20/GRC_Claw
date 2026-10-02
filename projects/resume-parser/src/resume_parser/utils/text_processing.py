"""Utility functions for resume parsing."""

from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


def generate_id() -> str:
    """Generate a unique identifier.

    Returns:
        str: A UUID4 string.
    """
    return str(uuid.uuid4())


def compute_file_hash(content: bytes) -> str:
    """Compute SHA-256 hash of file content.

    Args:
        content: Raw file bytes.

    Returns:
        str: Hex digest of the hash.
    """
    return hashlib.sha256(content).hexdigest()


def detect_file_type(file_name: str) -> str:
    """Detect file type from filename extension.

    Args:
        file_name: Name of the file.

    Returns:
        str: File extension without dot, or 'unknown'.
    """
    ext = Path(file_name).suffix.lower().lstrip(".")
    return ext if ext else "unknown"


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe storage.

    Args:
        filename: Original filename.

    Returns:
        str: Sanitized filename.
    """
    # Remove path components and non-alphanumeric chars except dots and dashes
    name = Path(filename).name
    name = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    return name.strip("._")


def truncate_text(text: str, max_length: int = 10000) -> str:
    """Truncate text to a maximum length.

    Args:
        text: Input text.
        max_length: Maximum allowed length.

    Returns:
        str: Truncated text.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def clean_text(text: str) -> str:
    """Clean extracted text by removing excessive whitespace.

    Args:
        text: Raw extracted text.

    Returns:
        str: Cleaned text.
    """
    # Replace multiple whitespace with single space
    text = re.sub(r"\s+", " ", text)
    # Remove non-printable characters
    text = re.sub(r"[^\x20-\x7E\n\r\t]", "", text)
    return text.strip()


def format_datetime(dt: datetime | None) -> str | None:
    """Format datetime to ISO string.

    Args:
        dt: Datetime to format.

    Returns:
        str | None: ISO formatted string or None.
    """
    if dt is None:
        return None
    return dt.isoformat()


def chunk_text(text: str, chunk_size: int = 4000, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks for LLM processing.

    Args:
        text: Input text to chunk.
        chunk_size: Maximum size of each chunk.
        overlap: Number of overlapping characters between chunks.

    Returns:
        list[str]: List of text chunks.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap

    return chunks


def merge_dicts(*dicts: dict[str, Any]) -> dict[str, Any]:
    """Merge multiple dictionaries, with later values taking precedence.

    Args:
        *dicts: Dictionaries to merge.

    Returns:
        dict[str, Any]: Merged dictionary.
    """
    result: dict[str, Any] = {}
    for d in dicts:
        result.update(d)
    return result


def extract_emails(text: str) -> list[str]:
    """Extract email addresses from text.

    Args:
        text: Input text.

    Returns:
        list[str]: List of found email addresses.
    """
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    return list(set(re.findall(pattern, text)))


def extract_phone_numbers(text: str) -> list[str]:
    """Extract phone numbers from text.

    Args:
        text: Input text.

    Returns:
        list[str]: List of found phone numbers.
    """
    pattern = r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
    return list(set(re.findall(pattern, text)))


def extract_urls(text: str) -> list[str]:
    """Extract URLs from text.

    Args:
        text: Input text.

    Returns:
        list[str]: List of found URLs.
    """
    pattern = r"https?://[^\s<>\"{}|\\^`\[\]]+"
    return list(set(re.findall(pattern, text)))


def safe_json_loads(text: str, default: Any = None) -> Any:
    """Safely parse JSON string.

    Args:
        text: JSON string to parse.
        default: Default value if parsing fails.

    Returns:
        Any: Parsed JSON or default value.
    """
    import json

    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default
