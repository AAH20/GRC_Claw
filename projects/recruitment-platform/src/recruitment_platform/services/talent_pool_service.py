"""Talent pool service for recruitment platform."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class TalentPoolError(Exception):
    """Base exception for talent pool operations."""


class PoolNotFoundError(TalentPoolError):
    """Raised when a talent pool is not found."""


class CandidateNotFoundError(TalentPoolError):
    """Raised when a candidate is not found."""


class DuplicateCandidateError(TalentPoolError):
    """Raised when a candidate is already in the pool."""


# In-memory storage for demonstration purposes
_pools: dict[str, dict[str, Any]] = {}
_candidates: dict[str, dict[str, Any]] = {}


def create_pool(data: dict[str, Any]) -> dict[str, Any]:
    """Create a new talent pool.

    Args:
        data: Pool data containing at least 'name' and optionally
              'description', 'tags', 'owner_id'.

    Returns:
        The created pool record with generated 'id' and timestamps.

    Raises:
        TalentPoolError: If required fields are missing or invalid.
    """
    if not isinstance(data, dict):
        raise TalentPoolError("Pool data must be a dictionary")

    name = data.get("name")
    if not name or not isinstance(name, str):
        raise TalentPoolError("Pool 'name' is required and must be a non-empty string")

    import uuid
    from datetime import datetime, timezone

    pool_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    pool = {
        "id": pool_id,
        "name": name,
        "description": data.get("description", ""),
        "tags": data.get("tags", []),
        "owner_id": data.get("owner_id"),
        "candidate_ids": [],
        "created_at": now,
        "updated_at": now,
    }

    _pools[pool_id] = pool
    logger.info("Created talent pool %s (%s)", pool_id, name)
    return pool


def add_candidate_to_pool(pool_id: str, candidate_id: str) -> dict[str, Any]:
    """Add a candidate to a talent pool.

    Args:
        pool_id: The unique identifier of the talent pool.
        candidate_id: The unique identifier of the candidate.

    Returns:
        The updated pool record.

    Raises:
        PoolNotFoundError: If the pool does not exist.
        CandidateNotFoundError: If the candidate does not exist.
        DuplicateCandidateError: If the candidate is already in the pool.
    """
    if not pool_id or not isinstance(pool_id, str):
        raise TalentPoolError("pool_id must be a non-empty string")
    if not candidate_id or not isinstance(candidate_id, str):
        raise TalentPoolError("candidate_id must be a non-empty string")

    pool = _pools.get(pool_id)
    if pool is None:
        raise PoolNotFoundError(f"Talent pool '{pool_id}' not found")

    if candidate_id not in _candidates:
        raise CandidateNotFoundError(f"Candidate '{candidate_id}' not found")

    if candidate_id in pool["candidate_ids"]:
        raise DuplicateCandidateError(
            f"Candidate '{candidate_id}' is already in pool '{pool_id}'"
        )

    from datetime import datetime, timezone

    pool["candidate_ids"].append(candidate_id)
    pool["updated_at"] = datetime.now(timezone.utc).isoformat()

    logger.info("Added candidate %s to pool %s", candidate_id, pool_id)
    return pool


def search_pools(
    query: str | None = None,
    filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Search talent pools by query string and filters.

    Args:
        query: Optional text to match against pool name and description.
        filters: Optional filters such as 'tags', 'owner_id', 'created_after'.

    Returns:
        A list of matching pool records, sorted by most recently updated.
    """
    results: list[dict[str, Any]] = []
    filters = filters or {}

    for pool in _pools.values():
        # Text search on name and description
        if query:
            q = query.lower()
            name_match = q in pool.get("name", "").lower()
            desc_match = q in pool.get("description", "").lower()
            if not (name_match or desc_match):
                continue

        # Apply filters
        if "tags" in filters:
            required_tags = set(filters["tags"])
            pool_tags = set(pool.get("tags", []))
            if not required_tags.issubset(pool_tags):
                continue

        if "owner_id" in filters:
            if pool.get("owner_id") != filters["owner_id"]:
                continue

        if "created_after" in filters:
            if pool.get("created_at", "") < filters["created_after"]:
                continue

        results.append(pool)

    # Sort by most recently updated
    results.sort(key=lambda p: p.get("updated_at", ""), reverse=True)
    return results
