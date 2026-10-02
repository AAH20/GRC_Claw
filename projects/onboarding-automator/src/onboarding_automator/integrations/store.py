"""In-memory data store for the onboarding automator.

This module provides a simple async in-memory store that can be used
for development and testing. In production, replace with a proper
database backend (PostgreSQL, MongoDB, etc.).
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from onboarding_automator.models import (
    ComplianceCheck,
    Document,
    OnboardingPlan,
    Progress,
    Task,
    WelcomeMessage,
)

__all__ = ["InMemoryStore"]


class InMemoryStore:
    """Thread-safe in-memory data store for all entity types."""

    def __init__(self) -> None:
        """Initialize empty storage dictionaries."""
        self._plans: dict[UUID, OnboardingPlan] = {}
        self._tasks: dict[UUID, Task] = {}
        self._documents: dict[UUID, Document] = {}
        self._progress: dict[UUID, Progress] = {}
        self._compliance_checks: dict[UUID, ComplianceCheck] = {}
        self._welcome_messages: dict[UUID, WelcomeMessage] = {}

    async def close(self) -> None:
        """Clean up resources (no-op for in-memory store)."""
        pass

    # --- Plans ---

    async def save_plan(self, plan: OnboardingPlan) -> None:
        """Save or update an onboarding plan."""
        self._plans[plan.id] = plan

    async def get_plan(self, plan_id: UUID) -> Optional[OnboardingPlan]:
        """Retrieve a plan by ID."""
        return self._plans.get(plan_id)

    async def list_plans(self) -> list[OnboardingPlan]:
        """List all plans."""
        return list(self._plans.values())

    async def delete_plan(self, plan_id: UUID) -> bool:
        """Delete a plan by ID. Returns True if found and deleted."""
        if plan_id in self._plans:
            del self._plans[plan_id]
            return True
        return False

    # --- Tasks ---

    async def save_task(self, task: Task) -> None:
        """Save or update a task."""
        self._tasks[task.id] = task

    async def get_task(self, task_id: UUID) -> Optional[Task]:
        """Retrieve a task by ID."""
        return self._tasks.get(task_id)

    async def list_tasks(self, plan_id: Optional[UUID] = None) -> list[Task]:
        """List tasks, optionally filtered by plan ID."""
        tasks = list(self._tasks.values())
        if plan_id is not None:
            tasks = [t for t in tasks if t.plan_id == plan_id]
        return tasks

    async def delete_task(self, task_id: UUID) -> bool:
        """Delete a task by ID. Returns True if found and deleted."""
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    # --- Documents ---

    async def save_document(self, document: Document) -> None:
        """Save or update a document."""
        self._documents[document.id] = document

    async def get_document(self, document_id: UUID) -> Optional[Document]:
        """Retrieve a document by ID."""
        return self._documents.get(document_id)

    async def list_documents(self, plan_id: Optional[UUID] = None) -> list[Document]:
        """List documents, optionally filtered by plan ID."""
        docs = list(self._documents.values())
        if plan_id is not None:
            docs = [d for d in docs if d.plan_id == plan_id]
        return docs

    async def delete_document(self, document_id: UUID) -> bool:
        """Delete a document by ID. Returns True if found and deleted."""
        if document_id in self._documents:
            del self._documents[document_id]
            return True
        return False

    # --- Progress ---

    async def save_progress(self, progress: Progress) -> None:
        """Save or update a progress record."""
        self._progress[progress.id] = progress

    async def get_progress(self, plan_id: UUID) -> Optional[Progress]:
        """Retrieve progress by plan ID."""
        for p in self._progress.values():
            if p.plan_id == plan_id:
                return p
        return None

    async def list_progress(self) -> list[Progress]:
        """List all progress records."""
        return list(self._progress.values())

    # --- Compliance Checks ---

    async def save_compliance_check(self, check: ComplianceCheck) -> None:
        """Save or update a compliance check."""
        self._compliance_checks[check.id] = check

    async def get_compliance_check(self, check_id: UUID) -> Optional[ComplianceCheck]:
        """Retrieve a compliance check by ID."""
        return self._compliance_checks.get(check_id)

    async def list_compliance_checks(
        self, plan_id: Optional[UUID] = None
    ) -> list[ComplianceCheck]:
        """List compliance checks, optionally filtered by plan ID."""
        checks = list(self._compliance_checks.values())
        if plan_id is not None:
            checks = [c for c in checks if c.plan_id == plan_id]
        return checks

    async def delete_compliance_check(self, check_id: UUID) -> bool:
        """Delete a compliance check by ID. Returns True if found and deleted."""
        if check_id in self._compliance_checks:
            del self._compliance_checks[check_id]
            return True
        return False

    # --- Welcome Messages ---

    async def save_welcome_message(self, message: WelcomeMessage) -> None:
        """Save or update a welcome message."""
        self._welcome_messages[message.id] = message

    async def get_welcome_message(self, message_id: UUID) -> Optional[WelcomeMessage]:
        """Retrieve a welcome message by ID."""
        return self._welcome_messages.get(message_id)

    async def list_welcome_messages(self, plan_id: UUID) -> list[WelcomeMessage]:
        """List welcome messages for a plan."""
        return [m for m in self._welcome_messages.values() if m.plan_id == plan_id]
