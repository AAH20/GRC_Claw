"""
Policy Definition Engine

Creates, validates, and manages policy definitions with structured sections,
metadata, and template-based instantiation.
"""

from __future__ import annotations

import copy
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from .models import (
    Policy,
    PolicyMetadata,
    PolicySection,
    PolicyTemplate,
    PolicyCategory,
    PolicyStatus,
    PolicyPriority,
    EnforcementMode,
    ChangeType,
    PolicyChange,
)


class PolicyValidationError(Exception):
    """Raised when a policy fails validation."""
    pass


class PolicyDefinitionEngine:
    """Engine for creating and managing policy definitions."""

    def __init__(self) -> None:
        self._policies: dict[str, Policy] = {}
        self._templates: dict[str, PolicyTemplate] = {}

    # ── Template Management ────────────────────────────────────────────────

    def register_template(self, template: PolicyTemplate) -> PolicyTemplate:
        """Register a policy template for reuse."""
        self._templates[template.id] = template
        return template

    def get_template(self, template_id: str) -> Optional[PolicyTemplate]:
        """Retrieve a template by ID."""
        return self._templates.get(template_id)

    def list_templates(
        self,
        category: Optional[PolicyCategory] = None,
        framework: Optional[str] = None,
    ) -> list[PolicyTemplate]:
        """List available templates with optional filtering."""
        templates = list(self._templates.values())
        if category:
            templates = [t for t in templates if t.category == category]
        if framework:
            templates = [t for t in templates if t.framework == framework]
        return templates

    def create_from_template(
        self,
        template_id: str,
        owner: str,
        approver: str,
        overrides: Optional[dict[str, Any]] = None,
    ) -> Policy:
        """Create a new policy from a registered template."""
        template = self._templates.get(template_id)
        if not template:
            raise PolicyValidationError(f"Template '{template_id}' not found")

        overrides = overrides or {}
        metadata = PolicyMetadata(
            title=overrides.get("title", template.name),
            description=overrides.get("description", template.description),
            category=overrides.get("category", template.category),
            priority=overrides.get("priority", PolicyPriority.MEDIUM),
            framework=overrides.get("framework", template.framework),
            framework_mappings=overrides.get("framework_mappings", template.framework_mappings.copy()),
            tags=overrides.get("tags", []),
            owner=owner,
            approver=approver,
            department=overrides.get("department", ""),
            jurisdiction=overrides.get("jurisdiction", ""),
        )

        sections = self._build_sections_from_template(template, overrides)

        policy = Policy(
            metadata=metadata,
            sections=sections,
            status=PolicyStatus.DRAFT,
            enforcement_mode=EnforcementMode.ADVISORY,
            created_by=owner,
            updated_by=owner,
        )

        # Copy default enforcement rules from template
        for rule in template.default_rules:
            new_rule = copy.deepcopy(rule)
            new_rule.id = str(uuid.uuid4())
            new_rule.policy_id = policy.id
            policy.enforcement_rules.append(new_rule)

        self._policies[policy.id] = policy
        self._log_change(policy, ChangeType.CREATED, "1.0.0", "1.0.0", owner, "Policy created from template")
        return policy

    # ── Policy CRUD ────────────────────────────────────────────────────────

    def create_policy(
        self,
        metadata: PolicyMetadata,
        sections: Optional[list[PolicySection]] = None,
        created_by: str = "",
    ) -> Policy:
        """Create a new policy from scratch."""
        policy = Policy(
            metadata=metadata,
            sections=sections or [],
            status=PolicyStatus.DRAFT,
            enforcement_mode=EnforcementMode.ADVISORY,
            created_by=created_by,
            updated_by=created_by,
        )
        self._policies[policy.id] = policy
        self._log_change(policy, ChangeType.CREATED, "1.0.0", "1.0.0", created_by, "Policy created")
        return policy

    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Retrieve a policy by ID."""
        return self._policies.get(policy_id)

    def update_policy(
        self,
        policy_id: str,
        updates: dict[str, Any],
        updated_by: str = "",
    ) -> Optional[Policy]:
        """Update policy fields."""
        policy = self._policies.get(policy_id)
        if not policy:
            return None

        if "metadata" in updates:
            for key, value in updates["metadata"].items():
                if hasattr(policy.metadata, key):
                    setattr(policy.metadata, key, value)

        if "sections" in updates:
            policy.sections = updates["sections"]

        if "enforcement_mode" in updates:
            policy.enforcement_mode = updates["enforcement_mode"]

        policy.updated_at = datetime.now(timezone.utc).isoformat()
        policy.updated_by = updated_by
        self._log_change(policy, ChangeType.UPDATED, policy.metadata.version, policy.metadata.version, updated_by, "Policy updated")
        return policy

    def delete_policy(self, policy_id: str) -> bool:
        """Remove a policy from the registry."""
        if policy_id in self._policies:
            del self._policies[policy_id]
            return True
        return False

    def list_policies(
        self,
        status: Optional[PolicyStatus] = None,
        category: Optional[PolicyCategory] = None,
        framework: Optional[str] = None,
        owner: Optional[str] = None,
    ) -> list[Policy]:
        """List policies with optional filtering."""
        policies = list(self._policies.values())
        if status:
            policies = [p for p in policies if p.status == status]
        if category:
            policies = [p for p in policies if p.metadata.category == category]
        if framework:
            policies = [p for p in policies if p.metadata.framework == framework]
        if owner:
            policies = [p for p in policies if p.metadata.owner == owner]
        return policies

    # ── Validation ─────────────────────────────────────────────────────────

    def validate_policy(self, policy: Policy) -> list[str]:
        """Validate a policy and return a list of validation errors."""
        errors: list[str] = []

        if not policy.metadata.title or len(policy.metadata.title.strip()) < 3:
            errors.append("Policy title must be at least 3 characters")

        if not policy.metadata.owner:
            errors.append("Policy owner is required")

        if not policy.metadata.approver:
            errors.append("Policy approver is required")

        if not policy.sections:
            errors.append("Policy must have at least one section")

        for i, section in enumerate(policy.sections):
            if not section.title:
                errors.append(f"Section {i + 1} must have a title")
            if section.required and not section.content.strip():
                errors.append(f"Required section '{section.title}' has no content")

        if policy.metadata.effective_date and policy.metadata.review_date:
            if policy.metadata.effective_date >= policy.metadata.review_date:
                errors.append("Effective date must be before review date")

        return errors

    def is_valid(self, policy: Policy) -> bool:
        """Check if a policy passes all validation rules."""
        return len(self.validate_policy(policy)) == 0

    # ── Section Helpers ────────────────────────────────────────────────────

    def add_section(
        self,
        policy_id: str,
        title: str,
        content: str = "",
        order: int = -1,
        required: bool = True,
    ) -> Optional[PolicySection]:
        """Add a section to an existing policy."""
        policy = self._policies.get(policy_id)
        if not policy:
            return None

        section = PolicySection(
            title=title,
            content=content,
            order=order if order >= 0 else len(policy.sections),
            required=required,
        )
        policy.sections.append(section)
        policy.sections.sort(key=lambda s: s.order)
        policy.updated_at = datetime.now(timezone.utc).isoformat()
        return section

    def remove_section(self, policy_id: str, section_id: str) -> bool:
        """Remove a section from a policy."""
        policy = self._policies.get(policy_id)
        if not policy:
            return False

        original_len = len(policy.sections)
        policy.sections = [s for s in policy.sections if s.id != section_id]
        if len(policy.sections) < original_len:
            policy.updated_at = datetime.now(timezone.utc).isoformat()
            return True
        return False

    # ── Internal Helpers ───────────────────────────────────────────────────

    def _build_sections_from_template(
        self,
        template: PolicyTemplate,
        overrides: dict[str, Any],
    ) -> list[PolicySection]:
        """Build policy sections from a template's required sections."""
        sections: list[PolicySection] = []
        content = overrides.get("content", template.default_content)

        for i, section_title in enumerate(template.required_sections):
            section_content = self._extract_section_content(content, section_title)
            sections.append(PolicySection(
                title=section_title,
                content=section_content,
                order=i,
                required=True,
            ))

        return sections

    def _extract_section_content(self, full_content: str, section_title: str) -> str:
        """Extract content for a specific section from markdown content."""
        lines = full_content.split("\n")
        section_lines: list[str] = []
        capturing = False
        target_header = f"## {section_title}"

        for line in lines:
            if line.strip() == target_header:
                capturing = True
                continue
            if capturing:
                if line.startswith("## ") and line.strip() != target_header:
                    break
                section_lines.append(line)

        return "\n".join(section_lines).strip()

    def _log_change(
        self,
        policy: Policy,
        change_type: ChangeType,
        version_from: str,
        version_to: str,
        changed_by: str,
        summary: str,
    ) -> None:
        """Add a change log entry to a policy."""
        change = PolicyChange(
            change_type=change_type,
            version_from=version_from,
            version_to=version_to,
            changed_by=changed_by,
            summary=summary,
        )
        policy.change_log.append(change)
