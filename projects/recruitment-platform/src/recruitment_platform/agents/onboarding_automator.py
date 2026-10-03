"""Onboarding Automator Agent for the Recruitment Platform.

Generates structured onboarding checklists for new hires and tracks
their completion progress across all onboarding stages.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums & Data Classes
# ---------------------------------------------------------------------------


class OnboardingStage(str, Enum):
    """Stages every new hire passes through during onboarding."""

    PRE_BOARDING = "pre_boarding"
    FIRST_DAY = "first_day"
    FIRST_WEEK = "first_week"
    FIRST_MONTH = "first_month"
    COMPLETION = "completion"


class TaskStatus(str, Enum):
    """Lifecycle status of an individual onboarding task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    SKIPPED = "skipped"


class Priority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class OnboardingTask:
    """A single actionable item in an onboarding checklist."""

    task_id: str
    title: str
    description: str
    stage: OnboardingStage
    priority: Priority
    status: TaskStatus
    due_date: date | None = None
    completed_date: date | None = None
    assigned_to: str | None = None
    estimated_hours: float = 0.5
    dependencies: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class OnboardingPlan:
    """Complete onboarding plan for a single new hire."""

    plan_id: str
    hire_id: str
    hire_name: str
    role: str
    department: str
    start_date: date
    manager_name: str
    buddy_name: str | None
    tasks: list[OnboardingTask] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ProgressSummary:
    """Aggregated completion status for an onboarding plan."""

    hire_id: str
    hire_name: str
    plan_id: str
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    pending_tasks: int
    overdue_tasks: int
    skipped_tasks: int
    completion_percentage: float
    current_stage: OnboardingStage
    is_complete: bool
    stage_breakdown: dict[str, dict[str, int | float]] = field(default_factory=dict)
    overdue_task_titles: list[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Mock Data Store
# ---------------------------------------------------------------------------

# Simulated database of hire profiles keyed by hire_id.
_MOCK_HIRE_DB: dict[str, dict[str, Any]] = {
    "hire-001": {
        "name": "Aisha Rahman",
        "role": "Senior Backend Engineer",
        "department": "Engineering",
        "start_date": date(2026, 10, 12),
        "manager": "David Chen",
        "buddy": "Marcus Johnson",
    },
    "hire-002": {
        "name": "Carlos Mendez",
        "role": "Product Designer",
        "department": "Design",
        "start_date": date(2026, 10, 19),
        "manager": "Sarah Kim",
        "buddy": "Lena Fischer",
    },
    "hire-003": {
        "name": "Priya Sharma",
        "role": "Data Analyst",
        "department": "Analytics",
        "start_date": date(2026, 10, 26),
        "manager": "James O'Brien",
        "buddy": "Tom Bradley",
    },
    "hire-004": {
        "name": "Lars Johansson",
        "role": "DevOps Engineer",
        "department": "Infrastructure",
        "start_date": date(2026, 11, 2),
        "manager": "David Chen",
        "buddy": "Nina Petrova",
    },
    "hire-005": {
        "name": "Fatima Al-Hassan",
        "role": "Marketing Manager",
        "department": "Marketing",
        "start_date": date(2026, 11, 9),
        "manager": "Rachel Green",
        "buddy": "Omar Farouk",
    },
}

# Template task definitions per stage. Each entry:
#   (title, description, priority, estimated_hours, dependencies)
_STAGE_TEMPLATES: dict[OnboardingStage, list[tuple[str, str, Priority, float, list[str]]]] = {
    OnboardingStage.PRE_BOARDING: [
        (
            "Send welcome email",
            "Send a personalised welcome email with first-day logistics, dress code, and parking info.",
            Priority.HIGH,
            0.5,
            [],
        ),
        (
            "Prepare workstation",
            "Set up desk, monitor(s), laptop, and peripherals. Ensure building access badge is printed.",
            Priority.CRITICAL,
            1.0,
            [],
        ),
        (
            "Create accounts & credentials",
            "Provision email, Slack, GitHub, Jira, and any role-specific SaaS accounts.",
            Priority.CRITICAL,
            1.5,
            [],
        ),
        (
            "Sign employment paperwork",
            "Collect signed contract, NDA, tax forms, and benefits enrolment documents.",
            Priority.CRITICAL,
            1.0,
            [],
        ),
        (
            "Order equipment & accessories",
            "Order any specialised equipment (e.g. design hardware, standing desk) if requested.",
            Priority.MEDIUM,
            0.5,
            [],
        ),
        (
            "Schedule orientation sessions",
            "Book HR orientation, IT security training, and team intro meetings for the first week.",
            Priority.HIGH,
            0.5,
            [],
        ),
    ],
    OnboardingStage.FIRST_DAY: [
        (
            "Office tour & introductions",
            "Walk the new hire around the office and introduce them to immediate team members.",
            Priority.HIGH,
            1.0,
            [],
        ),
        (
            "IT setup & login verification",
            "Verify all accounts work, VPN connects, and development environment is accessible.",
            Priority.CRITICAL,
            1.0,
            ["Create accounts & credentials"],
        ),
        (
            "Team lunch",
            "Organise a team lunch to help the new hire build rapport.",
            Priority.LOW,
            1.0,
            [],
        ),
        (
            "Review employee handbook",
            "Walk through the company handbook, code of conduct, and key policies.",
            Priority.MEDIUM,
            1.0,
            [],
        ),
        (
            "Set up development environment",
            "Clone repositories, install dependencies, and verify the build pipeline runs locally.",
            Priority.HIGH,
            2.0,
            ["IT setup & login verification"],
        ),
    ],
    OnboardingStage.FIRST_WEEK: [
        (
            "Complete security awareness training",
            "Finish the mandatory e-learning module on information security and data handling.",
            Priority.CRITICAL,
            2.0,
            [],
        ),
        (
            "Shadow buddy on daily tasks",
            "Pair with the assigned buddy to observe stand-ups, code reviews, and workflows.",
            Priority.MEDIUM,
            4.0,
            [],
        ),
        (
            "Review team OKRs & roadmap",
            "Read the team's quarterly OKRs and product roadmap to understand priorities.",
            Priority.MEDIUM,
            1.0,
            [],
        ),
        (
            "First 1:1 with manager",
            "Have a dedicated 1:1 to discuss expectations, goals, and any early questions.",
            Priority.HIGH,
            0.5,
            [],
        ),
        (
            "Submit first pull request / deliverable",
            "Make a small first contribution — a bug fix, design mock, or analysis — to build confidence.",
            Priority.HIGH,
            4.0,
            ["Set up development environment"],
        ),
        (
            "Enrol in benefits programme",
            "Finalise health insurance, retirement plan, and other benefits elections.",
            Priority.MEDIUM,
            1.0,
            ["Sign employment paperwork"],
        ),
    ],
    OnboardingStage.FIRST_MONTH: [
        (
            "Complete role-specific training",
            "Finish any deep-dive training modules relevant to the role (e.g. design system, data stack).",
            Priority.HIGH,
            8.0,
            [],
        ),
        (
            "Lead a team meeting or demo",
            "Present a short demo, retrospective, or knowledge-sharing session to the team.",
            Priority.MEDIUM,
            2.0,
            [],
        ),
        (
            "30-day feedback session",
            "Manager and new hire discuss what's going well and areas for improvement.",
            Priority.HIGH,
            1.0,
            ["First 1:1 with manager"],
        ),
        (
            "Set 90-day goals",
            "Collaboratively define measurable goals for the next 60 days.",
            Priority.HIGH,
            1.0,
            ["30-day feedback session"],
        ),
        (
            "Cross-functional introductions",
            "Meet key stakeholders in adjacent teams (Product, Design, Data, etc.).",
            Priority.MEDIUM,
            2.0,
            [],
        ),
    ],
    OnboardingStage.COMPLETION: [
        (
            "Final onboarding survey",
            "Complete the anonymous onboarding experience survey.",
            Priority.LOW,
            0.5,
            [],
        ),
        (
            "Archive onboarding documentation",
            "Ensure all signed documents, training certificates, and feedback are filed in HRIS.",
            Priority.MEDIUM,
            0.5,
            [],
        ),
        (
            "Transition to regular 1:1 cadence",
            "Move from onboarding-specific check-ins to the standard team 1:1 rhythm.",
            Priority.MEDIUM,
            0.5,
            ["30-day feedback session"],
        ),
        (
            "Celebrate onboarding completion",
            "Acknowledge the milestone — team shout-out, small gift, or coffee treat.",
            Priority.LOW,
            0.5,
            [],
        ),
    ],
}

# In-memory plan store (simulates a database table).
_PLAN_STORE: dict[str, OnboardingPlan] = {}


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def _generate_task_id() -> str:
    """Return a unique task identifier."""
    return f"task-{uuid.uuid4().hex[:12]}"


def _resolve_hire(hire_id: str) -> dict[str, Any]:
    """Look up a hire profile from the mock database.

    Raises:
        ValueError: If the hire_id is not found.
    """
    if hire_id not in _MOCK_HIRE_DB:
        available = ", ".join(sorted(_MOCK_HIRE_DB.keys()))
        raise ValueError(
            f"Hire '{hire_id}' not found. Available mock hires: {available}"
        )
    return _MOCK_HIRE_DB[hire_id]


def _build_stage_breakdown(
    tasks: list[OnboardingTask],
) -> dict[str, dict[str, int | float]]:
    """Compute per-stage task counts and completion percentages."""
    breakdown: dict[str, dict[str, int | float]] = {}
    for stage in OnboardingStage:
        stage_tasks = [t for t in tasks if t.stage == stage]
        total = len(stage_tasks)
        completed = sum(1 for t in stage_tasks if t.status == TaskStatus.COMPLETED)
        pct = round((completed / total) * 100, 1) if total > 0 else 0.0
        breakdown[stage.value] = {
            "total": total,
            "completed": completed,
            "completion_percentage": pct,
        }
    return breakdown


def _determine_current_stage(tasks: list[OnboardingTask]) -> OnboardingStage:
    """Return the earliest stage that still has incomplete tasks."""
    for stage in OnboardingStage:
        stage_tasks = [t for t in tasks if t.stage == stage]
        if any(t.status != TaskStatus.COMPLETED for t in stage_tasks):
            return stage
    return OnboardingStage.COMPLETION


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def create_onboarding_plan(hire_id: str) -> OnboardingPlan:
    """Generate a complete onboarding checklist for a new hire.

    Creates an :class:`OnboardingPlan` populated with stage-appropriate
    tasks derived from the onboarding templates. The plan is persisted
    in the in-memory store so that :func:`track_onboarding_progress`
    can later retrieve it.

    Args:
        hire_id: Unique identifier of the new hire (e.g. ``"hire-001"``).

    Returns:
        The fully populated :class:`OnboardingPlan`.

    Raises:
        ValueError: If ``hire_id`` does not exist in the mock database.

    Example:
        >>> plan = create_onboarding_plan("hire-001")
        >>> len(plan.tasks) > 0
        True
    """
    hire = _resolve_hire(hire_id)
    start_date: date = hire["start_date"]

    tasks: list[OnboardingTask] = []
    for stage, templates in _STAGE_TEMPLATES.items():
        for title, description, priority, est_hours, deps in templates:
            # Stagger due dates: pre-boarding tasks are due before start,
            # first-day tasks on start date, first-week within 5 days, etc.
            if stage == OnboardingStage.PRE_BOARDING:
                due = start_date - timedelta(days=2)
            elif stage == OnboardingStage.FIRST_DAY:
                due = start_date
            elif stage == OnboardingStage.FIRST_WEEK:
                due = start_date + timedelta(days=5)
            elif stage == OnboardingStage.FIRST_MONTH:
                due = start_date + timedelta(days=30)
            else:  # COMPLETION
                due = start_date + timedelta(days=45)

            task = OnboardingTask(
                task_id=_generate_task_id(),
                title=title,
                description=description,
                stage=stage,
                priority=priority,
                status=TaskStatus.PENDING,
                due_date=due,
                assigned_to=hire.get("manager") if priority == Priority.CRITICAL else None,
                estimated_hours=est_hours,
                dependencies=deps,
            )
            tasks.append(task)

    plan = OnboardingPlan(
        plan_id=f"plan-{uuid.uuid4().hex[:10]}",
        hire_id=hire_id,
        hire_name=hire["name"],
        role=hire["role"],
        department=hire["department"],
        start_date=start_date,
        manager_name=hire["manager"],
        buddy_name=hire.get("buddy"),
        tasks=tasks,
    )

    _PLAN_STORE[hire_id] = plan
    return plan


def track_onboarding_progress(hire_id: str) -> ProgressSummary:
    """Return the completion status of a new hire's onboarding plan.

    Aggregates task-level statuses into a high-level
    :class:`ProgressSummary` including per-stage breakdowns and a list
    of overdue task titles.

    Args:
        hire_id: Unique identifier of the new hire.

    Returns:
        A :class:`ProgressSummary` with completion metrics.

    Raises:
        ValueError: If no onboarding plan exists for ``hire_id``.
            Call :func:`create_onboarding_plan` first.

    Example:
        >>> create_onboarding_plan("hire-001")
        >>> summary = track_onboarding_progress("hire-001")
        >>> summary.total_tasks > 0
        True
    """
    if hire_id not in _PLAN_STORE:
        raise ValueError(
            f"No onboarding plan found for hire '{hire_id}'. "
            "Call create_onboarding_plan() first."
        )

    plan = _PLAN_STORE[hire_id]
    tasks = plan.tasks

    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
    in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
    pending = sum(1 for t in tasks if t.status == TaskStatus.PENDING)
    overdue = sum(1 for t in tasks if t.status == TaskStatus.OVERDUE)
    skipped = sum(1 for t in tasks if t.status == TaskStatus.SKIPPED)

    completion_pct = round((completed / total) * 100, 1) if total > 0 else 0.0

    overdue_titles = [t.title for t in tasks if t.status == TaskStatus.OVERDUE]

    return ProgressSummary(
        hire_id=hire_id,
        hire_name=plan.hire_name,
        plan_id=plan.plan_id,
        total_tasks=total,
        completed_tasks=completed,
        in_progress_tasks=in_progress,
        pending_tasks=pending,
        overdue_tasks=overdue,
        skipped_tasks=skipped,
        completion_percentage=completion_pct,
        current_stage=_determine_current_stage(tasks),
        is_complete=completed == total,
        stage_breakdown=_build_stage_breakdown(tasks),
        overdue_task_titles=overdue_titles,
    )


# ---------------------------------------------------------------------------
# Convenience / Demo
# ---------------------------------------------------------------------------


def _demo() -> None:
    """Quick smoke-test that exercises both public functions."""
    print("=" * 60)
    print("  Onboarding Automator — Demo")
    print("=" * 60)

    # 1. Create a plan
    hire_id = "hire-001"
    plan = create_onboarding_plan(hire_id)
    print(f"\nCreated plan for {plan.hire_name} ({plan.role})")
    print(f"  Plan ID : {plan.plan_id}")
    print(f"  Tasks   : {len(plan.tasks)}")
    print(f"  Manager : {plan.manager_name}")
    print(f"  Buddy   : {plan.buddy_name}")

    # 2. Simulate some progress
    for task in plan.tasks[:5]:
        task.status = TaskStatus.COMPLETED
        task.completed_date = date.today()
    plan.tasks[5].status = TaskStatus.IN_PROGRESS
    plan.tasks[6].status = TaskStatus.OVERDUE

    # 3. Track progress
    summary = track_onboarding_progress(hire_id)
    print(f"\nProgress for {summary.hire_name}:")
    print(f"  Total tasks     : {summary.total_tasks}")
    print(f"  Completed       : {summary.completed_tasks}")
    print(f"  In progress     : {summary.in_progress_tasks}")
    print(f"  Pending         : {summary.pending_tasks}")
    print(f"  Overdue         : {summary.overdue_tasks}")
    print(f"  Completion      : {summary.completion_percentage}%")
    print(f"  Current stage   : {summary.current_stage.value}")
    print(f"  Is complete     : {summary.is_complete}")
    if summary.overdue_task_titles:
        print(f"  Overdue tasks   : {', '.join(summary.overdue_task_titles)}")

    print("\nStage breakdown:")
    for stage_name, data in summary.stage_breakdown.items():
        print(
            f"  {stage_name:15s} — {data['completed']}/{data['total']} "
            f"({data['completion_percentage']}%)"
        )

    print("\n" + "=" * 60)


if __name__ == "__main__":
    _demo()
