"""
Policy Definition Engine for GRC_Claw.

Provides policy CRUD operations, template management, and validation.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from .models import (
    ChangeType,
    EnforcementMode,
    Policy,
    PolicyCategory,
    PolicyChange,
    PolicyMetadata,
    PolicyPriority,
    PolicySection,
    PolicyStatus,
    PolicyTemplate,
)

logger = logging.getLogger(__name__)


class PolicyValidationError(Exception):
    """Raised when a policy fails validation."""
    pass


class PolicyDefinitionEngine:
    """Core engine for policy definition and management."""

    def __init__(self) -> None:
        self._policies: dict[str, Policy] = {}
        self._templates: dict[str, PolicyTemplate] = {}

    def create_from_template(
        self,
        template_id: str,
        owner: str,
        approver: str,
        overrides: dict | None = None,
    ) -> Policy:
        """Create a policy from a registered template."""
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
            tags=overrides.get("tags", template.required_sections.copy()),
            owner=owner,
            approver=approver,
            department=overrides.get("department", ""),
            jurisdiction=overrides.get("jurisdiction", ""),
            version="1.0.0",
            effective_date=overrides.get("effective_date", ""),
            review_date=overrides.get("review_date", ""),
            expiry_date=overrides.get("expiry_date", ""),
        )

        sections = [
            PolicySection(
                title=section_title,
                content="",
                order=i,
                required=True,
            )
            for i, section_title in enumerate(template.required_sections)
        ]

        policy = Policy(
            metadata=metadata,
            sections=sections,
            status=PolicyStatus.DRAFT,
            enforcement_mode=EnforcementMode.ADVISORY,
            created_by=owner,
            updated_by=owner,
        )

        change = PolicyChange(
            change_type=ChangeType.CREATED,
            version_from="",
            version_to="1.0.0",
            changed_by=owner,
            summary=f"Policy created from template '{template.name}'",
        )
        policy.change_log.append(change)
        self._policies[policy.id] = policy
        return policy

    def create_policy(
        self,
        metadata: PolicyMetadata,
        sections: list[PolicySection] | None = None,
        created_by: str = "",
    ) -> Policy:
        """Create a policy from scratch."""
        policy = Policy(
            metadata=metadata,
            sections=sections or [],
            status=PolicyStatus.DRAFT,
            enforcement_mode=EnforcementMode.ADVISORY,
            created_by=created_by,
            updated_by=created_by,
        )
        change = PolicyChange(
            change_type=ChangeType.CREATED,
            version_from="",
            version_to=metadata.version,
            changed_by=created_by,
            summary="Policy created",
        )
        policy.change_log.append(change)
        self._policies[policy.id] = policy
        return policy

    def get_policy(self, policy_id: str) -> Policy | None:
        """Retrieve a policy by ID."""
        return self._policies.get(policy_id)

    def update_policy(
        self,
        policy_id: str,
        updates: dict,
        updated_by: str = "",
    ) -> Policy | None:
        """Update a policy."""
        policy = self._policies.get(policy_id)
        if not policy:
            return None

        if "title" in updates:
            policy.metadata.title = updates["title"]
        if "description" in updates:
            policy.metadata.description = updates["description"]
        if "category" in updates:
            policy.metadata.category = updates["category"]
        if "priority" in updates:
            policy.metadata.priority = updates["priority"]
        if "framework" in updates:
            policy.metadata.framework = updates["framework"]
        if "tags" in updates:
            policy.metadata.tags = updates["tags"]
        if "owner" in updates:
            policy.metadata.owner = updates["owner"]
        if "approver" in updates:
            policy.metadata.approver = updates["approver"]
        if "department" in updates:
            policy.metadata.department = updates["department"]
        if "jurisdiction" in updates:
            policy.metadata.jurisdiction = updates["jurisdiction"]
        if "effective_date" in updates:
            policy.metadata.effective_date = updates["effective_date"]
        if "review_date" in updates:
            policy.metadata.review_date = updates["review_date"]
        if "expiry_date" in updates:
            policy.metadata.expiry_date = updates["expiry_date"]
        if "sections" in updates:
            policy.sections = updates["sections"]
        if "enforcement_mode" in updates:
            policy.enforcement_mode = updates["enforcement_mode"]

        policy.updated_at = datetime.now(UTC).isoformat()
        policy.updated_by = updated_by

        change = PolicyChange(
            change_type=ChangeType.UPDATED,
            version_from=policy.metadata.version,
            version_to=policy.metadata.version,
            changed_by=updated_by,
            summary=updates.get("change_summary", "Policy updated"),
        )
        policy.change_log.append(change)
        return policy

    def delete_policy(self, policy_id: str) -> bool:
        """Delete a policy."""
        if policy_id in self._policies:
            del self._policies[policy_id]
            return True
        return False

    def list_policies(
        self,
        status: PolicyStatus | None = None,
        category: PolicyCategory | None = None,
        framework: str | None = None,
        owner: str | None = None,
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

    def validate_policy(self, policy: Policy) -> list[str]:
        """Validate a policy definition and return a list of errors."""
        errors: list[str] = []
        if not policy.metadata.title:
            errors.append("Policy title is required")
        if not policy.metadata.owner:
            errors.append("Policy owner is required")
        if not policy.metadata.category:
            errors.append("Policy category is required")
        if not policy.sections:
            errors.append("Policy must have at least one section")
        for section in policy.sections:
            if not section.title:
                errors.append(f"Section at order {section.order} has no title")
            if section.required and not section.content:
                errors.append(f"Required section '{section.title}' has no content")
        if policy.metadata.effective_date and policy.metadata.review_date:
            try:
                eff = datetime.fromisoformat(policy.metadata.effective_date)
                rev = datetime.fromisoformat(policy.metadata.review_date)
                if rev <= eff:
                    errors.append("Review date must be after effective date")
            except ValueError:
                errors.append("Invalid date format for effective_date or review_date")
        return errors

    def register_template(self, template: PolicyTemplate) -> PolicyTemplate:
        """Register a policy template."""
        self._templates[template.id] = template
        return template

    def list_templates(
        self,
        category: PolicyCategory | None = None,
        framework: str | None = None,
    ) -> list[PolicyTemplate]:
        """List available templates."""
        templates = list(self._templates.values())
        if category:
            templates = [t for t in templates if t.category == category]
        if framework:
            templates = [t for t in templates if t.framework == framework]
        return templates
