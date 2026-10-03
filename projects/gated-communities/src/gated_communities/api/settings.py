"""
Settings API endpoints for gated communities.

Provides GET and PUT /settings for retrieving and updating community settings.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/settings", tags=["settings"])


# ─── Mock Data ───────────────────────────────────────────────────────────────

MOCK_SETTINGS = {
    "community_id": "gc_01H8X7K2MNPQRSTUVWXYZ",
    "community_name": "The Inner Circle",
    "description": "An exclusive community for senior engineers and architects.",
    "visibility": "private",
    "join_policy": "invite_only",
    "member_approval_required": True,
    "content_moderation": {
        "enabled": True,
        "auto_flag_keywords": ["spam", "scam", "crypto-pump"],
        "require_post_approval": False,
        "max_daily_posts_per_member": 25,
    },
    "notifications": {
        "email_digest": "weekly",
        "push_enabled": True,
        "mention_alerts": True,
        "new_member_alerts": True,
    },
    "branding": {
        "primary_color": "#6366F1",
        "logo_url": "https://cdn.gated-communities.io/gc_01H8X7K2MN/logo.png",
        "banner_url": "https://cdn.gated-communities.io/gc_01H8X7K2MN/banner.png",
        "custom_domain": "innercircle.gated-communities.io",
    },
    "integrations": {
        "discord_webhook": "https://discord.com/api/webhooks/123456789/abcdef",
        "slack_channel": "#inner-circle-general",
        "github_org": "inner-circle-dev",
    },
    "limits": {
        "max_members": 500,
        "max_channels": 50,
        "max_file_upload_mb": 100,
        "retention_days": 365,
    },
    "created_at": "2024-06-15T10:30:00Z",
    "updated_at": "2025-09-20T14:22:00Z",
}


# ─── Pydantic Models ─────────────────────────────────────────────────────────

class ContentModerationSettings(BaseModel):
    enabled: bool = True
    auto_flag_keywords: List[str] = Field(default_factory=list)
    require_post_approval: bool = False
    max_daily_posts_per_member: int = Field(default=25, ge=1, le=100)


class NotificationSettings(BaseModel):
    email_digest: str = Field(default="weekly", pattern="^(daily|weekly|monthly|never)$")
    push_enabled: bool = True
    mention_alerts: bool = True
    new_member_alerts: bool = True


class BrandingSettings(BaseModel):
    primary_color: str = Field(default="#6366F1", pattern="^#[0-9A-Fa-f]{6}$")
    logo_url: Optional[str] = None
    banner_url: Optional[str] = None
    custom_domain: Optional[str] = None


class IntegrationSettings(BaseModel):
    discord_webhook: Optional[str] = None
    slack_channel: Optional[str] = None
    github_org: Optional[str] = None


class LimitSettings(BaseModel):
    max_members: int = Field(default=500, ge=1, le=100000)
    max_channels: int = Field(default=50, ge=1, le=500)
    max_file_upload_mb: int = Field(default=100, ge=1, le=1024)
    retention_days: int = Field(default=365, ge=30, le=3650)


class SettingsUpdateRequest(BaseModel):
    """Partial update — only provided fields are changed."""
    community_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    visibility: Optional[str] = Field(default=None, pattern="^(public|private|unlisted)$")
    join_policy: Optional[str] = Field(default=None, pattern="^(open|invite_only|application|closed)$")
    member_approval_required: Optional[bool] = None
    content_moderation: Optional[ContentModerationSettings] = None
    notifications: Optional[NotificationSettings] = None
    branding: Optional[BrandingSettings] = None
    integrations: Optional[IntegrationSettings] = None
    limits: Optional[LimitSettings] = None


class SettingsResponse(BaseModel):
    community_id: str
    community_name: str
    description: str
    visibility: str
    join_policy: str
    member_approval_required: bool
    content_moderation: ContentModerationSettings
    notifications: NotificationSettings
    branding: BrandingSettings
    integrations: IntegrationSettings
    limits: LimitSettings
    created_at: str
    updated_at: str


# ─── In-memory store (mock) ──────────────────────────────────────────────────

_settings_store: dict = {**MOCK_SETTINGS}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _deep_update(base: dict, updates: dict) -> dict:
    """Recursively merge updates into base dict."""
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_update(base[key], value)
        else:
            base[key] = value
    return base


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.get("", response_model=SettingsResponse)
async def get_settings() -> dict:
    """
    Retrieve the current community settings.

    Returns the full settings object for the gated community.
    """
    return {**_settings_store}


@router.put("", response_model=SettingsResponse)
async def update_settings(body: SettingsUpdateRequest) -> dict:
    """
    Update community settings.

    Only fields provided in the request body are modified.
    Returns the updated settings object.
    """
    global _settings_store

    update_data = body.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update.",
        )

    _deep_update(_settings_store, update_data)
    _settings_store["updated_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    return {**_settings_store}
