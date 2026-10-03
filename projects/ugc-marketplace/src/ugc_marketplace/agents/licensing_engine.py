"""
Licensing Engine Agent for UGC Marketplace.

Handles creation and validation of content licenses with realistic mock data.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums & Constants
# ---------------------------------------------------------------------------

class LicenseType(str, Enum):
    """Supported license types."""
    PERSONAL = "personal"
    COMMERCIAL = "commercial"
    EXCLUSIVE = "exclusive"
    EDITORIAL = "editorial"
    CREATIVE_COMMONS = "creative_commons"


class LicenseStatus(str, Enum):
    """Lifecycle status of a license."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    PENDING = "pending"
    SUSPENDED = "suspended"


class UsageType(str, Enum):
    """Types of usage that can be validated."""
    VIEW = "view"
    DOWNLOAD = "download"
    MODIFY = "modify"
    REDISTRIBUTE = "redistribute"
    COMMERCIAL_USE = "commercial_use"
    ATTRIBUTE = "attribute"


class ValidationResult(str, Enum):
    """Outcome of a license validation check."""
    VALID = "valid"
    INVALID = "invalid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    USAGE_NOT_PERMITTED = "usage_not_permitted"
    LIMIT_EXCEEDED = "limit_exceeded"
    NOT_FOUND = "not_found"


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class LicenseTerms:
    """Terms and conditions attached to a license."""
    license_type: LicenseType
    max_usage_count: int | None = None
    allowed_usages: list[UsageType] = field(default_factory=list)
    requires_attribution: bool = False
    allows_modification: bool = False
    allows_redistribution: bool = False
    territory_restrictions: list[str] = field(default_factory=list)
    valid_from: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    valid_until: datetime | None = None
    royalty_percentage: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class License:
    """Represents a content license."""
    license_id: str
    content_id: str
    licensor_id: str
    licensee_id: str
    terms: LicenseTerms
    status: LicenseStatus
    usage_count: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    license_hash: str = ""


@dataclass
class ValidationReport:
    """Result of validating a license against a usage request."""
    result: ValidationResult
    license_id: str
    usage: UsageType
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Mock Data Store
# ---------------------------------------------------------------------------

_MOCK_CONTENT_DB: dict[str, dict[str, Any]] = {
    "content_001": {
        "title": "Urban Skyline Timelapse",
        "creator_id": "creator_001",
        "content_type": "video",
        "base_price": 49.99,
    },
    "content_002": {
        "title": "Abstract Watercolor Collection",
        "creator_id": "creator_002",
        "content_type": "image_set",
        "base_price": 29.99,
    },
    "content_003": {
        "title": "Podcast Intro Jingle Pack",
        "creator_id": "creator_003",
        "content_type": "audio",
        "base_price": 19.99,
    },
    "content_004": {
        "title": "3D Low-Poly Asset Bundle",
        "creator_id": "creator_004",
        "content_type": "3d_model",
        "base_price": 79.99,
    },
    "content_005": {
        "title": "Handwritten Font Family",
        "creator_id": "creator_005",
        "content_type": "font",
        "base_price": 39.99,
    },
}

_MOCK_USER_DB: dict[str, dict[str, Any]] = {
    "user_001": {"name": "Alice Chen", "role": "creator", "verified": True},
    "user_002": {"name": "Bob Martinez", "role": "buyer", "verified": True},
    "user_003": {"name": "Carol Davis", "role": "buyer", "verified": False},
    "user_004": {"name": "Diana Park", "role": "enterprise", "verified": True},
    "user_005": {"name": "Eve Johnson", "role": "creator", "verified": True},
}

# In-memory license store (mock database)
_LICENSE_STORE: dict[str, License] = {}


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def _generate_license_id() -> str:
    """Generate a unique license identifier."""
    raw = f"{uuid.uuid4().hex}-{datetime.now(timezone.utc).isoformat()}"
    return f"LIC-{hashlib.sha256(raw.encode()).hexdigest()[:16].upper()}"


def _compute_license_hash(license: License) -> str:
    """Compute a tamper-evident hash for the license."""
    data = (
        f"{license.license_id}|{license.content_id}|{license.licensor_id}|"
        f"{license.licensee_id}|{license.terms.license_type.value}|"
        f"{license.created_at.isoformat()}"
    )
    return hashlib.sha256(data.encode()).hexdigest()


def _get_content_info(content_id: str) -> dict[str, Any] | None:
    """Retrieve content metadata from mock database."""
    return _MOCK_CONTENT_DB.get(content_id)


def _get_user_info(user_id: str) -> dict[str, Any] | None:
    """Retrieve user metadata from mock database."""
    return _MOCK_USER_DB.get(user_id)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_license(
    content_id: str,
    terms: LicenseTerms,
    *,
    licensor_id: str | None = None,
    licensee_id: str | None = None,
) -> License:
    """
    Create a new license for the given content.

    Args:
        content_id: The unique identifier of the content being licensed.
        terms: The license terms and conditions.
        licensor_id: Optional override for the content creator (auto-resolved if None).
        licensee_id: Optional override for the license buyer (defaults to a mock buyer).

    Returns:
        The newly created License object.

    Raises:
        ValueError: If the content_id is not found in the marketplace.
    """
    content_info = _get_content_info(content_id)
    if content_info is None:
        raise ValueError(
            f"Content '{content_id}' not found in marketplace. "
            f"Available content IDs: {list(_MOCK_CONTENT_DB.keys())}"
        )

    resolved_licensor = licensor_id or content_info["creator_id"]
    resolved_licensee = licensee_id or "user_002"

    if _get_user_info(resolved_licensor) is None:
        raise ValueError(f"Licensor '{resolved_licensor}' not found.")
    if _get_user_info(resolved_licensee) is None:
        raise ValueError(f"Licensee '{resolved_licensee}' not found.")

    license_id = _generate_license_id()

    license_obj = License(
        license_id=license_id,
        content_id=content_id,
        licensor_id=resolved_licensor,
        licensee_id=resolved_licensee,
        terms=terms,
        status=LicenseStatus.ACTIVE,
        usage_count=0,
    )
    license_obj.license_hash = _compute_license_hash(license_obj)

    _LICENSE_STORE[license_id] = license_obj

    return license_obj


def validate_license(license_id: str, usage: UsageType) -> ValidationReport:
    """
    Validate whether a license permits the requested usage.

    Args:
        license_id: The unique identifier of the license to validate.
        usage: The type of usage being requested.

    Returns:
        A ValidationReport indicating whether the usage is permitted and why.
    """
    license_obj = _LICENSE_STORE.get(license_id)

    if license_obj is None:
        return ValidationReport(
            result=ValidationResult.NOT_FOUND,
            license_id=license_id,
            usage=usage,
            message=f"License '{license_id}' not found in the licensing registry.",
        )

    # Check lifecycle status
    if license_obj.status == LicenseStatus.REVOKED:
        return ValidationReport(
            result=ValidationResult.REVOKED,
            license_id=license_id,
            usage=usage,
            message="License has been revoked by the licensor.",
            details={"revoked_at": license_obj.updated_at.isoformat()},
        )

    if license_obj.status == LicenseStatus.SUSPENDED:
        return ValidationReport(
            result=ValidationResult.INVALID,
            license_id=license_id,
            usage=usage,
            message="License is currently suspended pending review.",
        )

    if license_obj.status == LicenseStatus.PENDING:
        return ValidationReport(
            result=ValidationResult.INVALID,
            license_id=license_id,
            usage=usage,
            message="License is pending activation. Please try again later.",
        )

    # Check temporal validity
    now = datetime.now(timezone.utc)
    if license_obj.terms.valid_until and now > license_obj.terms.valid_until:
        license_obj.status = LicenseStatus.EXPIRED
        return ValidationReport(
            result=ValidationResult.EXPIRED,
            license_id=license_id,
            usage=usage,
            message=f"License expired on {license_obj.terms.valid_until.isoformat()}.",
            details={"expired_at": license_obj.terms.valid_until.isoformat()},
        )

    # Check usage count limit
    if (
        license_obj.terms.max_usage_count is not None
        and license_obj.usage_count >= license_obj.terms.max_usage_count
    ):
        return ValidationReport(
            result=ValidationResult.LIMIT_EXCEEDED,
            license_id=license_id,
            usage=usage,
            message=(
                f"Usage limit exceeded: {license_obj.usage_count}/"
                f"{license_obj.terms.max_usage_count}."
            ),
            details={
                "current_usage": license_obj.usage_count,
                "max_usage": license_obj.terms.max_usage_count,
            },
        )

    # Check if the specific usage type is allowed
    if license_obj.terms.allowed_usages and usage not in license_obj.terms.allowed_usages:
        return ValidationReport(
            result=ValidationResult.USAGE_NOT_PERMITTED,
            license_id=license_id,
            usage=usage,
            message=(
                f"Usage '{usage.value}' is not permitted under this license. "
                f"Allowed usages: {[u.value for u in license_obj.terms.allowed_usages]}."
            ),
            details={
                "requested_usage": usage.value,
                "allowed_usages": [u.value for u in license_obj.terms.allowed_usages],
            },
        )

    # All checks passed — increment usage counter
    license_obj.usage_count += 1
    license_obj.updated_at = now

    return ValidationReport(
        result=ValidationResult.VALID,
        license_id=license_id,
        usage=usage,
        message=f"License validated successfully for '{usage.value}'.",
        details={
            "usage_count": license_obj.usage_count,
            "remaining_uses": (
                license_obj.terms.max_usage_count - license_obj.usage_count
                if license_obj.terms.max_usage_count is not None
                else "unlimited"
            ),
            "license_type": license_obj.terms.license_type.value,
            "content_id": license_obj.content_id,
        },
    )


# ---------------------------------------------------------------------------
# Convenience / Demo
# ---------------------------------------------------------------------------

def _demo() -> None:
    """Run a quick demonstration of the licensing engine."""
    print("=" * 60)
    print("UGC Marketplace — Licensing Engine Demo")
    print("=" * 60)

    # Create a commercial license
    terms = LicenseTerms(
        license_type=LicenseType.COMMERCIAL,
        max_usage_count=100,
        allowed_usages=[
            UsageType.VIEW,
            UsageType.DOWNLOAD,
            UsageType.COMMERCIAL_USE,
        ],
        requires_attribution=True,
        allows_modification=False,
        allows_redistribution=False,
        valid_until=datetime.now(timezone.utc) + timedelta(days=365),
        royalty_percentage=5.0,
    )

    license_obj = create_license("content_001", terms)
    print(f"\n[CREATED] License ID: {license_obj.license_id}")
    print(f"  Content: {license_obj.content_id}")
    print(f"  Type: {license_obj.terms.license_type.value}")
    print(f"  Status: {license_obj.status.value}")
    print(f"  Hash: {license_obj.license_hash[:16]}...")

    # Validate a permitted usage
    report = validate_license(license_obj.license_id, UsageType.DOWNLOAD)
    print(f"\n[VALIDATE] {UsageType.DOWNLOAD.value} -> {report.result.value}")
    print(f"  Message: {report.message}")
    print(f"  Details: {report.details}")

    # Validate a non-permitted usage
    report2 = validate_license(license_obj.license_id, UsageType.REDISTRIBUTE)
    print(f"\n[VALIDATE] {UsageType.REDISTRIBUTE.value} -> {report2.result.value}")
    print(f"  Message: {report2.message}")

    # Validate a non-existent license
    report3 = validate_license("LIC-NONEXISTENT", UsageType.VIEW)
    print(f"\n[VALIDATE] non-existent -> {report3.result.value}")
    print(f"  Message: {report3.message}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    _demo()
