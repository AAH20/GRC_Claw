"""Integration modules for rights management."""

from ugc_marketplace.integrations.rights_management.notifications import \
    NotificationService
from ugc_marketplace.integrations.rights_management.storage import \
    InMemoryStorage

__all__ = ["InMemoryStorage", "NotificationService"]
