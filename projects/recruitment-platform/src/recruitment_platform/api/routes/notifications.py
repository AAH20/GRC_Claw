"""Notification API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from recruitment_platform.notifications.notification_service import (
    NotificationChannel,
    NotificationPriority,
    notification_service,
)

router = APIRouter()


@router.post("/notifications/send")
async def send_notification(
    channels: list[NotificationChannel],
    recipients: dict[str, str],
    subject: str,
    message: str,
    priority: NotificationPriority = NotificationPriority.NORMAL,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Send a notification across multiple channels."""
    try:
        results = await notification_service.notify(
            channels=channels,
            recipients=recipients,
            subject=subject,
            message=message,
            priority=priority,
            data=data,
        )
        return {"success": True, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/notifications/email")
async def send_email(
    to: str,
    subject: str,
    body: str,
    html_body: str | None = None,
) -> dict[str, Any]:
    """Send an email notification."""
    result = await notification_service.send_email(to, subject, body, html_body)
    return result


@router.post("/notifications/sms")
async def send_sms(
    to: str,
    message: str,
) -> dict[str, Any]:
    """Send an SMS notification."""
    result = await notification_service.send_sms(to, message)
    return result


@router.post("/notifications/push")
async def send_push(
    user_id: str,
    title: str,
    body: str,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Send a push notification."""
    result = await notification_service.send_push(user_id, title, body, data)
    return result
