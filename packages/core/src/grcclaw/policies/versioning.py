"""
Policy Versioning

Manages immutable policy versions, semantic versioning, version comparison,
rollback, and version diffing.
"""

from __future__ import annotations

import copy
import re
from datetime import datetime, timezone
from typing import Any, Optional

from .models import (
    Policy,
    PolicyVersion,
    PolicySection,
    PolicyStatus,
    ChangeType,
    PolicyChange,
)


class VersionBumpType:
    """Semantic version bump types."""
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


class PolicyVersioning:
    """Manages policy version lifecycle."""

    def __init__(self) -> None:
        self._versions: dict[str, list[PolicyVersion]] = {}

    # ── Version Creation ───────────────────────────────────────────────────

    def create_version(
        self,
        policy: Policy,
        change_summary: str,
        created_by: str,
        bump_type: str = VersionBumpType.MINOR,
    ) -> PolicyVersion:
        """Create a new immutable version snapshot of a policy."""
        new_version_str = self._bump_version(policy.metadata.version, bump_type)

        # Deep copy sections for immutability
        frozen_sections = copy.deepcopy(policy.sections)

        metadata_snapshot = {
            "title": policy.metadata.title,
            "description": policy.metadata.description,
            "category": policy.metadata.category.value,
            "priority": policy.metadata.priority.value,
            "framework": policy.metadata.framework,
            "framework_mappings": policy.metadata.framework_mappings.copy(),
            "tags": policy.metadata.tags.copy(),
            "owner": policy.metadata.owner,
            "approver": policy.metadata.approver,
            "department": policy.metadata.department,
            "jurisdiction": policy.metadata.jurisdiction,
            "effective_date": policy.metadata.effective_date,
            "review_date": policy.metadata.review_date,
            "expiry_date": policy.metadata.expiry_date,
        }

        version = PolicyVersion(
            policy_id=policy.id,
            version=new_version_str,
            sections=frozen_sections,
            metadata_snapshot=metadata_snapshot,
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

        # Also store on the policy itself
        for v in policy.versions:
            v.is_active = False
        policy.versions.append(version)

        # Update policy metadata
        old_version = policy.metadata.version
        policy.metadata.version = new_version_str
        policy.updated_at = datetime.now(timezone.utc).isoformat()
        policy.updated_by = created_by

        # Log the change
        change = PolicyChange(
            change_type=ChangeType.UPDATED,
            version_from=old_version,
            version_to=new_version_str,
            changed_by=created_by,
            summary=change_summary,
            diff=self._compute_diff(old_version, new_version_str),
        )
        policy.change_log.append(change)

        return version

    # ── Version Retrieval ──────────────────────────────────────────────────

    def get_version(self, policy_id: str, version_str: str) -> Optional[PolicyVersion]:
        """Retrieve a specific version of a policy."""
        versions = self._versions.get(policy_id, [])
        for v in versions:
            if v.version == version_str:
                return v
        return None

    def get_active_version(self, policy_id: str) -> Optional[PolicyVersion]:
        """Get the currently active version of a policy."""
        versions = self._versions.get(policy_id, [])
        for v in versions:
            if v.is_active:
                return v
        return versions[-1] if versions else None

    def list_versions(self, policy_id: str) -> list[PolicyVersion]:
        """List all versions of a policy, newest first."""
        versions = self._versions.get(policy_id, [])
        return sorted(versions, key=lambda v: self._version_key(v.version), reverse=True)

    # ── Version Comparison ─────────────────────────────────────────────────

    def compare_versions(
        self,
        policy_id: str,
        version_a: str,
        version_b: str,
    ) -> dict[str, Any]:
        """Compare two versions and return differences."""
        va = self.get_version(policy_id, version_a)
        vb = self.get_version(policy_id, version_b)

        if not va or not vb:
            return {"error": "One or both versions not found"}

        diff: dict[str, Any] = {
            "version_a": version_a,
            "version_b": version_b,
            "sections_added": [],
            "sections_removed": [],
            "sections_modified": [],
            "metadata_changes": {},
        }

        # Compare sections by title
        sections_a = {s.title: s for s in va.sections}
        sections_b = {s.title: s for s in vb.sections}

        for title in sections_a:
            if title not in sections_b:
                diff["sections_removed"].append(title)
            elif sections_a[title].content != sections_b[title].content:
                diff["sections_modified"].append({
                    "title": title,
                    "content_changed": True,
                })

        for title in sections_b:
            if title not in sections_a:
                diff["sections_added"].append(title)

        # Compare metadata
        for key in va.metadata_snapshot:
            if va.metadata_snapshot.get(key) != vb.metadata_snapshot.get(key):
                diff["metadata_changes"][key] = {
                    "from": va.metadata_snapshot.get(key),
                    "to": vb.metadata_snapshot.get(key),
                }

        return diff

    # ── Rollback ───────────────────────────────────────────────────────────

    def rollback_to_version(
        self,
        policy: Policy,
        target_version: str,
        rolled_back_by: str,
    ) -> bool:
        """Roll back a policy to a previous version."""
        target = self.get_version(policy.id, target_version)
        if not target:
            return False

        # Restore sections from the target version
        policy.sections = copy.deepcopy(target.sections)

        # Restore metadata from snapshot
        snapshot = target.metadata_snapshot
        policy.metadata.title = snapshot.get("title", policy.metadata.title)
        policy.metadata.description = snapshot.get("description", policy.metadata.description)
        policy.metadata.framework = snapshot.get("framework", policy.metadata.framework)
        policy.metadata.framework_mappings = snapshot.get("framework_mappings", [])
        policy.metadata.tags = snapshot.get("tags", [])
        policy.metadata.department = snapshot.get("department", "")
        policy.metadata.jurisdiction = snapshot.get("jurisdiction", "")
        policy.metadata.effective_date = snapshot.get("effective_date", "")
        policy.metadata.review_date = snapshot.get("review_date", "")
        policy.metadata.expiry_date = snapshot.get("expiry_date", "")

        # Create a new version for the rollback
        new_version_str = self._bump_version(policy.metadata.version, VersionBumpType.PATCH)
        policy.metadata.version = new_version_str
        policy.updated_at = datetime.now(timezone.utc).isoformat()
        policy.updated_by = rolled_back_by

        # Log the rollback
        change = PolicyChange(
            change_type=ChangeType.UPDATED,
            version_from=target_version,
            version_to=new_version_str,
            changed_by=rolled_back_by,
            summary=f"Rolled back to version {target_version}",
        )
        policy.change_log.append(change)

        return True

    # ── Version History ────────────────────────────────────────────────────

    def get_version_history(self, policy_id: str) -> list[dict[str, Any]]:
        """Get a summarized version history for a policy."""
        versions = self.list_versions(policy_id)
        return [
            {
                "version": v.version,
                "change_summary": v.change_summary,
                "created_by": v.created_by,
                "created_at": v.created_at,
                "is_active": v.is_active,
                "section_count": len(v.sections),
            }
            for v in versions
        ]

    # ── Internal Helpers ───────────────────────────────────────────────────

    def _bump_version(self, current: str, bump_type: str) -> str:
        """Bump a semantic version string."""
        parts = self._parse_version(current)
        if bump_type == VersionBumpType.MAJOR:
            parts[0] += 1
            parts[1] = 0
            parts[2] = 0
        elif bump_type == VersionBumpType.MINOR:
            parts[1] += 1
            parts[2] = 0
        else:  # PATCH
            parts[2] += 1
        return ".".join(str(p) for p in parts)

    def _parse_version(self, version: str) -> list[int]:
        """Parse a version string into numeric components."""
        clean = version.strip().lstrip("v")
        parts = clean.split(".")
        result = []
        for p in parts[:3]:
            try:
                result.append(int(p))
            except ValueError:
                result.append(0)
        while len(result) < 3:
            result.append(0)
        return result

    def _version_key(self, version: str) -> tuple[int, int, int]:
        """Create a sortable key from a version string."""
        parts = self._parse_version(version)
        return (parts[0], parts[1], parts[2])

    def _compute_diff(self, old: str, new: str) -> dict[str, str]:
        """Compute a simple version diff."""
        return {"from": old, "to": new}
