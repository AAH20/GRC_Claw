"""Audit log API."""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter()


class AuditLogEntry(BaseModel):
    """Schema for audit log entry."""
    id: str
    action: str
    user_id: str
    resource_type: str
    resource_id: str
    details: dict[str, Any]
    ip_address: str | None
    created_at: str


class AuditLogCreate(BaseModel):
    """Schema for creating audit log entry."""
    action: str
    user_id: str
    resource_type: str
    resource_id: str
    details: dict[str, Any] = Field(default_factory=dict)
    ip_address: str | None = None


# In-memory store (replace with database in production)
_audit_logs: dict[str, AuditLogEntry] = {}


@router.post("/audit", response_model=AuditLogEntry, status_code=201)
async def create_audit_log(entry: AuditLogCreate) -> AuditLogEntry:
    """Create an audit log entry."""
    log_id = str(uuid4())
    audit_entry = AuditLogEntry(
        id=log_id,
        **entry.model_dump(),
        created_at=datetime.now(UTC).isoformat(),
    )
    _audit_logs[log_id] = audit_entry
    logger.info("audit_log_created", log_id=log_id, action=entry.action)
    return audit_entry


@router.get("/audit", response_model=list[AuditLogEntry])
async def list_audit_logs(
    user_id: str | None = None,
    resource_type: str | None = None,
    limit: int = Query(100, ge=1, le_=1000),
) -> list[AuditLogEntry]:
    """List audit log entries with optional filtering."""
    logs = list(_audit_logs.values())
    if user_id:
        logs = [log for log in logs if log.user_id == user_id]
    if resource_type:
        logs = [log for log in logs if log.resource_type == resource_type]
    return sorted(logs, key=lambda x: x.created_at, reverse=True)[:limit]


@router.get("/audit/{log_id}", response_model=AuditLogEntry)
async def get_audit_log(log_id: str) -> AuditLogEntry:
    """Get a specific audit log entry."""
    if log_id not in _audit_logs:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return _audit_logs[log_id]
