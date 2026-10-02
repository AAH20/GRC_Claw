"""
GRC_Claw Notification & Alerting Framework

Unified notification system for GRC (Governance, Risk, Compliance) alerts.
Supports multi-channel delivery (email, Slack, Teams, webhook), alert routing,
templating, and delivery analytics.
"""

from .analytics import NotificationAnalytics
from .channels import (
    BaseChannel,
    EmailChannel,
    SlackChannel,
    TeamsChannel,
    WebhookChannel,
)
from .engine import NotificationEngine
from .models import (
    Alert,
    AlertRule,
    AlertSeverity,
    AlertStatus,
    AnalyticsSummary,
    ChannelConfig,
    DeliveryResult,
    Notification,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
    RoutingRule,
    Template,
    TemplateVariable,
)
from .routing import AlertRouter
from .templates import TemplateEngine

__all__ = [
    "Alert",
    "AlertRouter",
    "AlertRule",
    "AlertSeverity",
    "AlertStatus",
    "AnalyticsSummary",
    "BaseChannel",
    "ChannelConfig",
    "DeliveryResult",
    "EmailChannel",
    "Notification",
    "NotificationAnalytics",
    "NotificationEngine",
    "NotificationPriority",
    "NotificationStatus",
    "NotificationType",
    "RoutingRule",
    "SlackChannel",
    "TeamsChannel",
    "Template",
    "TemplateEngine",
    "TemplateVariable",
    "WebhookChannel",
]
