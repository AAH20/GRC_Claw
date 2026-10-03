"""Moderation queue and item management routes."""
from fastapi import APIRouter, Request
from typing import Any

router = APIRouter(prefix="/moderation", tags=["moderation"])

_MOCK_QUEUE = [
    {"id": "mod_001", "type": "post", "status": "pending", "author": "user_42", "reason": "spam", "created_at": "2026-10-01T08:30:00Z"},
    {"id": "mod_002", "type": "comment", "status": "pending", "author": "user_17", "reason": "harassment", "created_at": "2026-10-01T09:15:00Z"},
    {"id": "mod_003", "type": "member", "status": "pending", "author": "user_88", "reason": "tos_violation", "created_at": "2026-10-02T14:20:00Z"},
]


@router.get("/queue")
async def get_moderation_queue() -> dict[str, Any]:
    """Return pending moderation items."""
    return {"items": _MOCK_QUEUE, "total": len(_MOCK_QUEUE), "page": 1}


@router.post("/items")
async def create_moderation_item(request: Request) -> dict[str, Any]:
    """Submit a new moderation item for review."""
    body = await request.json()
    item = {
        "id": f"mod_{len(_MOCK_QUEUE) + 1:03d}",
        "type": body.get("type", "post"),
        "status": "pending",
        "author": body.get("author", "unknown"),
        "reason": body.get("reason", "unspecified"),
        "created_at": "2026-10-03T10:00:00Z",
    }
    _MOCK_QUEUE.append(item)
    return {"item": item, "queued": True}
