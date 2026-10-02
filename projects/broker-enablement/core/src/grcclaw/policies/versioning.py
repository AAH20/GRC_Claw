"""
Policy Versioning for GRC_Claw.

Provides semantic versioning, version comparison, diffing, and rollback.
"""

from __future__ import annotations

import copy
import logging
from datetime import UTC, datetime
from enum import Enum

from .models import (
    ChangeType,
    Policy,
    PolicyChange,
    PolicyVersion,
)

logger = logging.getLogger(__name__)


class VersionBumpType(str, Enum):
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


class PolicyVersioning:
    """Manages policy version lifecycle."""

    def __init__(self) -> None:
        self._versions: dict[str, list[PolicyVersion]] = {}

    def _bump_version(self, current: str, bump_type: str) -> str:
        """Bump a semantic version string."""
        parts = current.split(".")
        if len(parts) != 3:
            parts = ["1", "0", "0"]
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
        if bump_type == VersionBumpType.MAJOR:
            major += 1
            minor = 0
            patch = 0
        elif bump_type == VersionBumpType.MINOR:
            minor += 1
            patch = 0
        else:
            patch += 1
        return f"{major}.{minor}.{patch}"

    def create_version(
        self,
        policy: Policy,
        change_summary: str,
        created_by: str,
        bump_type: str = VersionBumpType.MINOR,
    ) -> PolicyVersion:
        """Create a new version of a policy."""
        new_version_str = self._bump_version(policy.metadata.version, bump_type)

        version = PolicyVersion(
            policy_id=policy.id,
            version=new_version_str,
            sections=copy.deepcopy(policy.sections),
            metadata_snapshot={
                "title": policy.metadata.title,
                "description": policy.metadata.description,
                "category": policy.metadata.category.value,
                "priority": policy.metadata.priority.value,
                "framework": policy.metadata.framework,
                "owner": policy.metadata.owner,
                "approver": policy.metadata.approver,
                "department": policy.metadata.department,
                "jurisdiction": policy.metadata.jurisdiction,
                "effective_date": policy.metadata.effective_date,
                "review_date": policy.metadata.review_date,
                "expiry_date": policy.metadata.expiry_date,
                "tags": policy.metadata.tags.copy(),
            },
            change_summary=change_summary,
            created_by=created_by,
            is_active=True,
        )

        # Deactivate previous versions
        if policy.id in self._versions:
            for v in self._versions[policy.id]:
                v.is_active = False
            self._versions[policy.id].append(version)
        else:
            self._versions[policy.id] = [version]

        # Update policy
        policy.metadata.version = new_version_str
        policy.versions = self._versions[policy.id]
        policy.updated_at = datetime.now(UTC).isoformat()
        policy.updated_by = created_by

        change = PolicyChange(
            change_type=ChangeType.UPDATED,
            version_from=policy.metadata.version,
            version_to=new_version_str,
            changed_by=created_by,
            summary=change_summary,
        )
        policy.change_log.append(change)

        return version

    def get_version(self, policy_id: str, version: str) -> PolicyVersion | None:
        """Get a specific version."""
        versions = self._versions.get(policy_id, [])
        for v in versions:
            if v.version == version:
                return v
        return None

    def list_versions(self, policy_id: str) -> list[PolicyVersion]:
        """List all versions of a policy."""
        return self._versions.get(policy_id, [])

    def compare_versions(
        self,
        policy_id: str,
        version_a: str,
        version_b: str,
    ) -> dict:
        """Compare two versions and return a diff summary."""
        va = self.get_version(policy_id, version_a)
        vb = self.get_version(policy_id, version_b)
        if not va or not vb:
            return {"error": "One or both versions not found"}

        sections_a = {s.title: s.content for s in va.sections}
        sections_b = {s.title: s.content for s in vb.sections}

        added = [t for t in sections_b if t not in sections_a]
        removed = [t for t in sections_a if t not in sections_b]
        modified = [t for t in sections_a if t in sections_b and sections_a[t] != sections_b[t]]
        unchanged = [t for t in sections_a if t in sections_b and sections_a[t] == sections_b[t]]

        return {
            "version_a": version_a,
            "version_b": version_b,
            "added_sections": added,
            "removed_sections": removed,
            "modified_sections": modified,
            "unchanged_sections": unchanged,
            "metadata_changes": self._compare_metadata(va.metadata_snapshot, vb.metadata_snapshot),
        }

    def _compare_metadata(self, meta_a: dict, meta_b: dict) -> dict:
        """Compare two metadata snapshots."""
        changes = {}
        all_keys = set(meta_a.keys()) | set(meta_b.keys())
        for key in all_keys:
            val_a = meta_a.get(key)
            val_b = meta_b.get(key)
            if val_a != val_b:
                changes[key] = {"from": val_a, "to": val_b}
        return changes

    def rollback_to_version(
        self,
        policy: Policy,
        target_version: str,
        rolled_back_by: str,
    ) -> bool:
        """Roll back to a previous version."""
        target = self.get_version(policy.id, target_version)
        if not target:
            return False

        # Create a new version that is a copy of the target
        new_version_str = self._bump_version(policy.metadata.version, VersionBumpType.MINOR)

        version = PolicyVersion(
            policy_id=policy.id,
            version=new_version_str,
            sections=copy.deepcopy(target.sections),
            metadata_snapshot=copy.deepcopy(target.metadata_snapshot),
            change_summary=f"Rollback to version {target_version}",
            created_by=rolled_back_by,
            is_active=True,
        )

        if policy.id in self._versions:
            for v in self._versions[policy.id]:
                v.is_active = False
            self._versions[policy.id].append(version)
        else:
            self._versions[policy.id] = [version]

        # Restore policy state
        policy.sections = copy.deepcopy(target.sections)
        policy.metadata.title = target.metadata_snapshot.get("title", policy.metadata.title)
        policy.metadata.description = target.metadata_snapshot.get("description", policy.metadata.description)
        policy.metadata.version = new_version_str
        policy.versions = self._versions[policy.id]
        policy.updated_at = datetime.now(UTC).isoformat()
        policy.updated_by = rolled_back_by

        change = PolicyChange(
            change_type=ChangeType.UPDATED,
            version_from=policy.metadata.version,
            version_to=new_version_str,
            changed_by=rolled_back_by,
            summary=f"Rollback to version {target_version}",
        )
        policy.change_log.append(change)

        return True
