"""
GRC_Claw Notification & Alerting Framework

Unified notification system for GRC (Governance, Risk, Compliance) alerts.
Supports multi-channel delivery (email, Slack, Teams, webhook), alert routing,
templating, and delivery analytics.
"""

from .models import (
    Notification,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
    Alert,
    AlertSeverity,
    AlertStatus,
    AlertRule,
    DeliveryResult,
    Template,
    TemplateVariable,
    AnalyticsSummary,
    ChannelConfig,
    RoutingRule,
)
from .engine import NotificationEngine
from .routing import AlertRouter
from .templates import TemplateEngine
from .analytics import NotificationAnalytics
from .channels import (
    BaseChannel,
    EmailChannel,
    SlackChannel,
    TeamsChannel,
    WebhookChannel,
)

__all__ = [
    "Notification",
    "NotificationPriority",
    "NotificationStatus",
    "NotificationType",
    "Alert",
    "AlertSeverity",
    "AlertStatus",
    "AlertRule",
    "DeliveryResult",
    "Template",
    "TemplateVariable",
    "AnalyticsSummary",
    "ChannelConfig",
    "RoutingRule",
    "NotificationEngine",
    "AlertRouter",
    "TemplateEngine",
    "NotificationAnalytics",
    "BaseChannel",
    "EmailChannel",
    "SlackChannel",
    "TeamsChannel",
    "WebhookChannel",
]
