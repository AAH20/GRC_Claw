"""Task Automation Agent.

Automates repetitive CRM tasks and workflows to improve
sales team productivity and reduce manual data entry.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


class TaskPriority(StrEnum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(StrEnum):
    """Task status values."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskTemplate(BaseModel):
    """Task template model."""

    name: str
    description: str
    priority: TaskPriority
    due_in_days: int = 1
    auto_assign: bool = True
    assignee: str | None = None
    tags: list[str] = Field(default_factory=list)


class AutomatedTask(BaseModel):
    """Automated task model."""

    task_id: str
    template: TaskTemplate
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    due_date: datetime | None = None
    completed_at: datetime | None = None
    assigned_to: str | None = None
    crm_record_id: str | None = None
    crm_record_type: str | None = None


class TaskAutomationAgent:
    """Agent for automating CRM tasks and workflows.

    This agent creates, assigns, and tracks automated tasks based on
    triggers, templates, and business rules to reduce manual work
    for sales teams.
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the Task Automation Agent.

        Args:
            config: Optional configuration dictionary.
        """
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.max_concurrent = self.config.get("max_concurrent_tasks", 10)
        self.default_priority = self.config.get("default_priority", "medium")
        self.auto_assign = self.config.get("auto_assign", True)
        self._task_counter = 0
        logger.info("TaskAutomationAgent initialized", enabled=self.enabled)

    def _generate_task_id(self) -> str:
        """Generate a unique task ID.

        Returns:
            Unique task identifier.
        """
        self._task_counter += 1
        return f"task_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{self._task_counter}"

    async def create_task(
        self,
        template: TaskTemplate,
        crm_record_id: str | None = None,
        crm_record_type: str | None = None,
    ) -> AutomatedTask:
        """Create a new automated task.

        Args:
            template: Task template to use.
            crm_record_id: Optional CRM record ID to link.
            crm_record_type: Optional CRM record type.

        Returns:
            The created automated task.

        Raises:
            ValueError: If template is invalid.
        """
        if not template.name:
            raise ValueError("Task template must have a name")

        task_id = self._generate_task_id()
        due_date = datetime.utcnow() + timedelta(days=template.due_in_days)

        task = AutomatedTask(
            task_id=task_id,
            template=template,
            due_date=due_date,
            assigned_to=template.assignee if template.auto_assign else None,
            crm_record_id=crm_record_id,
            crm_record_type=crm_record_type,
        )

        logger.info(
            "Task created",
            task_id=task_id,
            name=template.name,
            priority=template.priority,
        )
        return task

    async def create_follow_up_task(
        self,
        contact_email: str,
        deal_id: str | None = None,
        notes: str = "",
    ) -> AutomatedTask:
        """Create a follow-up task for a contact.

        Args:
            contact_email: Email of the contact to follow up with.
            deal_id: Optional related deal ID.
            notes: Optional notes for the task.

        Returns:
            The created follow-up task.
        """
        template = TaskTemplate(
            name=f"Follow up with {contact_email}",
            description=notes or f"Follow up with contact {contact_email}",
            priority=TaskPriority.MEDIUM,
            due_in_days=1,
            auto_assign=self.auto_assign,
            tags=["follow-up", "contact"],
        )
        return await self.create_task(
            template=template,
            crm_record_id=deal_id,
            crm_record_type="deal",
        )

    async def create_deal_stage_task(
        self,
        deal_id: str,
        stage: str,
        contact_email: str,
    ) -> AutomatedTask:
        """Create a task for deal stage progression.

        Args:
            deal_id: The deal ID.
            stage: Current deal stage.
            contact_email: Contact email for the deal.

        Returns:
            The created stage task.
        """
        template = TaskTemplate(
            name=f"Move deal {deal_id} from {stage}",
            description=f"Progress deal {deal_id} past {stage} stage",
            priority=TaskPriority.HIGH,
            due_in_days=2,
            auto_assign=self.auto_assign,
            tags=["deal", "stage-progression"],
        )
        return await self.create_task(
            template=template,
            crm_record_id=deal_id,
            crm_record_type="deal",
        )

    async def complete_task(self, task: AutomatedTask) -> AutomatedTask:
        """Mark a task as completed.

        Args:
            task: The task to complete.

        Returns:
            The updated task.
        """
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        logger.info("Task completed", task_id=task.task_id)
        return task

    async def fail_task(self, task: AutomatedTask, reason: str) -> AutomatedTask:
        """Mark a task as failed.

        Args:
            task: The task to fail.
            reason: Reason for failure.

        Returns:
            The updated task.
        """
        task.status = TaskStatus.FAILED
        logger.warning("Task failed", task_id=task.task_id, reason=reason)
        return task

    async def get_overdue_tasks(self, tasks: list[AutomatedTask]) -> list[AutomatedTask]:
        """Get all overdue tasks.

        Args:
            tasks: List of tasks to check.

        Returns:
            List of overdue tasks.
        """
        now = datetime.utcnow()
        return [
            task
            for task in tasks
            if task.status == TaskStatus.PENDING
            and task.due_date is not None
            and task.due_date < now
        ]

    async def auto_assign_task(self, task: AutomatedTask, team_members: list[str]) -> AutomatedTask:
        """Auto-assign a task to a team member using round-robin.

        Args:
            task: The task to assign.
            team_members: List of team member identifiers.

        Returns:
            The updated task.

        Raises:
            ValueError: If no team members are available.
        """
        if not team_members:
            raise ValueError("No team members available for assignment")

        # Simple round-robin assignment
        index = self._task_counter % len(team_members)
        task.assigned_to = team_members[index]
        logger.info("Task auto-assigned", task_id=task.task_id, assignee=task.assigned_to)
        return task
