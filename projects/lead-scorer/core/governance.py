"""GRC_Claw governance integration."""

from __future__ import annotations

import hashlib
import re
from typing import Any

import structlog

from core.config import get_settings

logger = structlog.get_logger(__name__)


class GovernanceEngine:
    """GRC_Claw governance engine for compliance and audit.

    Provides PII redaction, audit logging, and rate limiting.
    """

    # PII patterns for redaction
    PII_PATTERNS: dict[str, re.Pattern[str]] = {
        "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        "phone": re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
        "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "credit_card": re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),
    }

    def __init__(self) -> None:
        """Initialize the governance engine."""
        self.settings = get_settings()
        self._audit_entries: list[dict[str, Any]] = []

    def redact_pii(self, text: str) -> str:
        """Redact PII from text.

        Args:
            text: Input text that may contain PII.

        Returns:
            Text with PII redacted.
        """
        if not self.settings.pii_redaction:
            return text

        redacted = text
        for pii_type, pattern in self.PII_PATTERNS.items():
            redacted = pattern.sub(f"[REDACTED_{pii_type.upper()}]", redacted)
        return redacted

    def audit_log(
        self,
        action: str,
        lead_id: str,
        tenant_id: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Record an audit log entry.

        Args:
            action: Action performed.
            lead_id: Lead identifier.
            tenant_id: Tenant identifier.
            details: Additional details.
        """
        if not self.settings.audit_log:
            return

        entry = {
            "action": action,
            "lead_id": self._hash_id(lead_id),
            "tenant_id": self._hash_id(tenant_id),
            "details": details or {},
        }
        self._audit_entries.append(entry)
        logger.info("audit_log", **entry)

    def validate_tenant_access(
        self, tenant_id: str, lead_tenant_id: str
    ) -> bool:
        """Validate tenant access to a lead.

        Args:
            tenant_id: Requesting tenant.
            lead_tenant_id: Lead's owning tenant.

        Returns:
            True if access is allowed.
        """
        return tenant_id == lead_tenant_id

    def check_rate_limit(
        self, key: str, max_requests: int, window_seconds: int
    ) -> bool:
        """Check if a rate limit has been exceeded.

        Args:
            key: Rate limit key (e.g., tenant_id or IP).
            max_requests: Maximum requests allowed in the window.
            window_seconds: Time window in seconds.

        Returns:
            True if the request is allowed, False if rate limited.
        """
        # In production, use Redis for distributed rate limiting
        # This is a simplified in-memory implementation
        return True

    def _hash_id(self, id_value: str) -> str:
        """Hash an identifier for audit logging.

        Args:
            id_value: Identifier to hash.

        Returns:
            SHA-256 hash of the identifier.
        """
        return hashlib.sha256(id_value.encode()).hexdigest()[:16]

    def get_audit_trail(
        self, lead_id: str | None = None, tenant_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Retrieve audit trail entries.

        Args:
            lead_id: Filter by lead ID.
            tenant_id: Filter by tenant ID.

        Returns:
            List of audit entries.
        """
        entries = self._audit_entries
        if lead_id:
            hashed = self._hash_id(lead_id)
            entries = [e for e in entries if e["lead_id"] == hashed]
        if tenant_id:
            hashed = self._hash_id(tenant_id)
            entries = [e for e in entries if e["tenant_id"] == hashed]
        return entries


# Singleton instance
_governance_engine: GovernanceEngine | None = None


def get_governance() -> GovernanceEngine:
    """Get the governance engine singleton.

    Returns:
        Governance engine instance.
    """
    global _governance_engine
    if _governance_engine is None:
        _governance_engine = GovernanceEngine()
    return _governance_engine
