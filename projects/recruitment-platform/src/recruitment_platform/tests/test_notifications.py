"""Tests for notifications module."""

from __future__ import annotations

import pytest

from recruitment_platform.notifications.notification_service import (
    NotificationChannel,
    NotificationPriority,
    NotificationService,
)


class TestNotificationService:
    """Test notification service."""

    @pytest.mark.asyncio
    async def test_send_email(self) -> None:
        """Test email notification."""
        service = NotificationService()
        result = await service.send_email("test@example.com", "Test", "Body")
        assert result["success"] is True
        assert result["channel"] == "email"

    @pytest.mark.asyncio
    async def test_send_sms(self) -> None:
        """Test SMS notification."""
        service = NotificationService()
        result = await service.send_sms("+1234567890", "Test message")
        assert result["success"] is True
        assert result["channel"] == "sms"

    @pytest.mark.asyncio
    async def test_send_push(self) -> None:
        """Test push notification."""
        service = NotificationService()
        result = await service.send_push("user-123", "Title", "Body")
        assert result["success"] is True
        assert result["channel"] == "push"

    @pytest.mark.asyncio
    async def test_send_in_app(self) -> None:
        """Test in-app notification."""
        service = NotificationService()
        result = await service.send_in_app("user-123", "Title", "Message")
        assert result["success"] is True
        assert result["channel"] == "in_app"

    @pytest.mark.asyncio
    async def test_multi_channel_notify(self) -> None:
        """Test multi-channel notification."""
        service = NotificationService()
        result = await service.notify(
            channels=[NotificationChannel.EMAIL, NotificationChannel.SMS],
            recipients={"email": "test@example.com", "phone": "+1234567890"},
            subject="Test",
            message="Test message",
        )
        assert "email" in result
        assert "sms" in result
