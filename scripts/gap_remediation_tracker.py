#!/usr/bin/env python3
"""
GRC_Claw Remediation Tracker

Manages remediation actions for gaps — create, update, track, and report
on the specific steps needed to close each gap. Supports:
- Action CRUD (create, read, update, delete)
- Progress tracking with automatic gap status sync
- Dependency management between actions
- Effort tracking (estimated vs actual)
- Burndown reporting
- Action templates for common remediation patterns

Usage:
    python gap_remediation_tracker.py --action create --gap-id GAP-001 --title "Design AIGoLang spec"
    python gap_remediation_tracker.py --action update --id ACT-001 --progress 50
    python gap_remediation_tracker.py --action list --gap-id GAP-001
    python gap_remediation_tracker.py --action report
    python gap_remediation_tracker.py --action burndown
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gap_model import (
    Gap, GapStatus, GapCategory, GapSeverity,
    RemediationAction,
    load_gaps, save_gaps, load_actions, save_actions,
    initialize_gap_registry, VALID_TRANSITIONS
)

DEFAULT_REGISTRY = Path(__file__).resolve().parent / "gap_registry.json"
DEFAULT_ACTIONS = Path(__file__).resolve().parent / "gap_actions.json"


# Common remediation action templates
ACTION_TEMPLATES = {
    "design": [
        {"title": "Design {gap_name} architecture", "description": "Create detailed architecture document", "estimated_effort": "1 week"},
        {"title": "Define {gap_name} API contracts", "description": "Specify interfaces and data models", "estimated_effort": "3 days"},
        {"title": "Create {gap_name} proof of concept", "description": "Build minimal viable implementation", "estimated_effort": "2 weeks"},
    ],
    "implementation": [
        {"title": "Implement {gap_name} core components", "description": "Build the main functionality", "estimated_effort": "3 weeks"},
        {"title": "Implement {gap_name} integrations", "description": "Connect with existing systems", "estimated_effort": "2 weeks"},
        {"title": "Write {gap_name} tests", "description": "Unit, integration, and E2E tests", "estimated_effort": "1 week"},
    ],
    "validation": [
        {"title": "Validate {gap_name} against requirements", "description": "Verify all requirements are met", "estimated_effort": "1 week"},
        {"title": "Conduct {gap_name} security review", "description": "Security assessment and penetration testing", "estimated_effort": "3 days"},
        {"title": "Perform {gap_name} compliance audit", "description": "Audit against regulatory requirements", "estimated_effort": "1 week"},
    ],
    "documentation": [
        {"title": "Write {gap_name} user documentation", "description": "User guides and API documentation", "estimated_effort": "3 days"},
        {"title": "Create {gap_name} runbooks", "description": "Operational runbooks and playbooks", "estimated_effort": "2 days"},
        {"title": "Document {gap_name} lessons learned", "description": "Post-implementation review and knowledge capture", "estimated_effort": "1 day"},
    ],
}


class RemediationTracker:
    """Manages remediation actions and syncs with gap status."""

    def __init__(self, registry_path: Path, actions_path: Path, verbose: bool = False):
        self.registry_path = registry_path
        self.actions_path = actions_path
        self.verbose = verbose
        self.gaps: list[Gap] = initialize_gap_registry(registry_path)
        self.actions: list[RemediationAction] = load_actions(actions_path)
        self.gap_map = {g.id: g for g in self.gaps}

    def log(self, msg: str) -> None:
        if self.verbose:
            print(f"[tracker] {msg}")

    def _generate_id(self) -> str:
        """Generate a unique action ID."""
        existing = {a.id for a in self.actions}
        n = len(self.actions) + 1
        while f"ACT-{n:03d}" in existing:
            n += 1
        return f"ACT-{n:03d}"

    def create_action(
        self,
        gap_id: str,
        title: str,
        description: str = "",
        owner: str = "",
        priority: int = 5,
        estimated_effort: str = "",
        due_date: str = "",
        dependencies: list[str] | None = None,
        deliverables: list[str] | None = None,
    ) -> RemediationAction:
        """Create a new remediation action."""
        if gap_id not in self.gap_map:
            raise ValueError(f"Unknown gap ID: {gap_id}")

        action = RemediationAction(
            id=self._generate_id(),
            gap_id=gap_id,
            title=title,
            description=description,
            owner=owner,
            status=GapStatus.PLANNED,
            priority=priority,
            estimated_effort=estimated_effort,
            due_date=due_date,
            dependencies=dependencies or [],
            deliverables=deliverables or [],
        )
        self.actions.append(action)
        save_actions(self.actions, self.actions_path)

        # Update gap status if it was just identified
        gap = self.gap_map[gap_id]
        if gap.status == GapStatus.IDENTIFIED:
            gap.status = GapStatus.PLANNED
            gap.last_updated = datetime.now(timezone.utc).isoformat()
            save_gaps(self.gaps, self.registry_path)

        self.log(f"Created action {action.id} for {gap_id}")
        return action

    def create_from_template(self, gap_id: str, template_category: str, owner: str = "") -> list[RemediationAction]:
        """Create actions from a template category."""
        if template_category not in ACTION_TEMPLATES:
            raise ValueError(f"Unknown template: {template_category}. Choose from: {list(ACTION_TEMPLATES.keys())}")
        gap = self.gap_map.get(gap_id)
        if not gap:
            raise ValueError(f"Unknown gap ID: {gap_id}")

        created = []
        for tmpl in ACTION_TEMPLATES[template_category]:
            action = self.create_action(
                gap_id=gap_id,
                title=tmpl["title"].format(gap_name=gap.name),
                description=tmpl["description"],
                owner=owner,
                estimated_effort=tmpl["estimated_effort"],
            )
            created.append(action)
        return created

    def update_action(
        self,
        action_id: str,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
        progress: int | None = None,
        owner: str | None = None,
        actual_effort: str | None = None,
        due_date: str | None = None,
        notes: str | None = None,
    ) -> RemediationAction:
        """Update an existing action."""
        action = next((a for a in self.actions if a.id == action_id), None)
        if not action:
            raise ValueError(f"Action not found: {action_id}")

        if title is not None:
            action.title = title
        if description is not None:
            action.description = description
        if status is not None:
            new_status = GapStatus(status)
            action.status = new_status
            if new_status in (GapStatus.MITIGATED, GapStatus.CLOSED):
                action.progress = 100
                action.completed_date = datetime.now(timezone.utc).isoformat()
        if progress is not None:
            action.progress = max(0, min(100, progress))
            if action.progress == 100 and action.status not in (GapStatus.MITIGATED, GapStatus.CLOSED):
                action.status = GapStatus.MITIGATED
                action.completed_date = datetime.now(timezone.utc).isoformat()
        if owner is not None:
            action.owner = owner
        if actual_effort is not None:
            action.actual_effort = actual_effort
        if due_date is not None:
            action.due_date = due_date
        if notes is not None:
            action.notes = notes

        save_actions(self.actions, self.actions_path)
        self._sync_gap_progress(action.gap_id)
        self.log(f"Updated action {action_id}")
        return action

    def delete_action(self, action_id: str) -> bool:
        """Delete an action."""
        action = next((a for a in self.actions if a.id == action_id), None)
        if not action:
            return False
        self.actions = [a for a in self.actions if a.id != action_id]
        save_actions(self.actions, self.actions_path)
        self._sync_gap_progress(action.gap_id)
        self.log(f"Deleted action {action_id}")
        return True

    def list_actions(
        self,
        gap_id: str | None = None,
        status: str | None = None,
        owner: str | None = None,
    ) -> list[RemediationAction]:
        """List actions with optional filters."""
        result = self.actions
        if gap_id:
            result = [a for a in result if a.gap_id == gap_id]
        if status:
            result = [a for a in result if a.status.value == status]
        if owner:
            result = [a for a in result if a.owner == owner]
        return result

    def _sync_gap_progress(self, gap_id: str) -> None:
        """Sync gap progress based on its remediation actions."""
        gap = self.gap_map.get(gap_id)
        if not gap:
            return
        gap_actions = [a for a in self.actions if a.gap_id == gap_id]
        if not gap_actions:
            return

        # Compute average progress
        avg_progress = sum(a.progress for a in gap_actions) / len(gap_actions)
        gap.progress = int(avg_progress)

        # Auto-update status based on action statuses
        all_done = all(a.status in (GapStatus.MITIGATED, GapStatus.CLOSED) for a in gap_actions)
        any_in_progress = any(a.status in (GapStatus.IN_PROGRESS, GapStatus.IMPLEMENTING) for a in gap_actions)
        any_planned = any(a.status == GapStatus.PLANNED for a in gap_actions)

        if all_done and gap_actions:
            gap.status = GapStatus.MITIGATED
        elif any_in_progress:
            gap.status = GapStatus.IN_PROGRESS
        elif any_planned and gap.status == GapStatus.IDENTIFIED:
            gap.status = GapStatus.PLANNED

        gap.last_updated = datetime.now(timezone.utc).isoformat()
        save_gaps(self.gaps, self.registry_path)

    def get_burndown_data(self) -> dict[str, Any]:
        """Generate burndown chart data."""
        if not self.actions:
            return {"dates": [], "remaining": [], "completed": []}

        # Group actions by creation date
        date_counts: Counter[str] = Counter()
        for a in self.actions:
            date_counts[a.created_date[:10]] += 1

        dates = sorted(date_counts.keys())
        total = len(self.actions)
        remaining = []
        completed = []
        cumulative = 0

        for d in dates:
            cumulative += date_counts[d]
            # Count how many were completed by this date
            done_by_date = sum(
                1 for a in self.actions
                if a.completed_date and a.completed_date[:10] <= d
            )
            remaining.append(total - done_by_date)
            completed.append(done_by_date)

        return {
            "dates": dates,
            "remaining": remaining,
            "completed": completed,
            "total_actions": total,
        }

    def get_gap_summary(self, gap_id: str) -> dict[str, Any]:
        """Get a summary of remediation status for a gap."""
        gap = self.gap_map.get(gap_id)
        if not gap:
            raise ValueError(f"Unknown gap ID: {gap_id}")

        gap_actions = [a for a in self.actions if a.gap_id == gap_id]
        status_counts = Counter(a.status.value for a in gap_actions)
        total_effort = sum(
            self._parse_effort(a.estimated_effort) for a in gap_actions if a.estimated_effort
        )
        actual_effort = sum(
            self._parse_effort(a.actual_effort) for a in self.actions if a.actual_effort
        )

        return {
            "gap_id": gap_id,
            "gap_name": gap.name,
            "gap_status": gap.status.value,
            "gap_progress": gap.progress,
            "total_actions": len(gap_actions),
            "actions_by_status": dict(status_counts),
            "total_estimated_effort_hours": total_effort,
            "total_actual_effort_hours": actual_effort,
            "actions": [a.to_dict() for a in gap_actions],
        }

    def _parse_effort(self, effort_str: str) -> int:
        """Parse effort string like '2 weeks' or '40 hours' into hours."""
        effort_str = effort_str.lower().strip()
        if "week" in effort_str:
            try:
                n = int(effort_str.split()[0])
                return n * 40  # 40 hours per week
            except (ValueError, IndexError):
                return 0
        elif "day" in effort_str:
            try:
                n = int(effort_str.split()[0])
                return n * 8  # 8 hours per day
            except (ValueError, IndexError):
                return 0
        elif "hour" in effort_str:
            try:
                return int(effort_str.split()[0])
            except (ValueError, IndexError):
                return 0
        return 0

    def generate_report(self) -> str:
        """Generate a comprehensive remediation report."""
        now = datetime.now(timezone.utc)
        total_actions = len(self.actions)
        status_counts = Counter(a.status.value for a in self.actions)
        gap_ids_with_actions = set(a.gap_id for a in self.actions)
        gaps_without_actions = [g for g in self.gaps if g.id not in gap_ids_with_actions and g.status not in (GapStatus.CLOSED, GapStatus.MITIGATED)]

        lines = [
            "# GRC_Claw Remediation Tracker Report",
            "",
            f"**Generated:** {now.strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "---",
            "",
            "## Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Actions | {total_actions} |",
            f"| Gaps with Actions | {len(gap_ids_with_actions)} |",
            f"| Gaps without Actions | {len(gaps_without_actions)} |",
            "",
            "### Action Status",
            "",
        ]
        for status, count in status_counts.most_common():
            lines.append(f"- **{status.replace('_', ' ').title()}:** {count}")

        lines.extend(["", "---", "", "## Actions by Gap", ""])
        for gap_id in sorted(gap_ids_with_actions):
            summary = self.get_gap_summary(gap_id)
            lines.append(f"### {gap_id}: {summary['gap_name']}")
            lines.append(f"- Status: {summary['gap_status']} | Progress: {summary['gap_progress']}%")
            lines.append(f"- Actions: {summary['total_actions']}")
            lines.append(f"- Estimated effort: {summary['total_estimated_effort_hours']}h")
            lines.append("")

        if gaps_without_actions:
            lines.extend(["---", "", "## Gaps Needing Remediation Plans", ""])
            for g in gaps_without_actions:
                lines.append(f"- **{g.id}** {g.name} ({g.status.value})")

        lines.extend(["", "---", "", "## Upcoming Deadlines", ""])
        now_date = now.date()
        upcoming = sorted(
            [a for a in self.actions if a.due_date and a.status not in (GapStatus.MITIGATED, GapStatus.CLOSED)],
            key=lambda x: x.due_date,
        )
        for a in upcoming[:15]:
            try:
                due = datetime.fromisoformat(a.due_date.replace("Z", "+00:00")).date()
                days_left = (due - now_date).days
                overdue = " ⚠️ OVERDUE" if days_left < 0 else f" ({days_left}d left)"
            except (ValueError, AttributeError):
                overdue = ""
            lines.append(f"- **{a.id}** {a.title} — due {a.due_date}{overdue}")

        lines.extend(["", "---", "", f"*Report generated by GRC_Claw Remediation Tracker*"])
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="GRC_Claw Remediation Tracker")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--actions", type=Path, default=DEFAULT_ACTIONS)
    parser.add_argument("--verbose", "-v", action="store_true")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Create
    create_parser = subparsers.add_parser("create", help="Create a new action")
    create_parser.add_argument("--gap-id", required=True)
    create_parser.add_argument("--title", required=True)
    create_parser.add_argument("--description", default="")
    create_parser.add_argument("--owner", default="")
    create_parser.add_argument("--priority", type=int, default=5)
    create_parser.add_argument("--estimated-effort", default="")
    create_parser.add_argument("--due-date", default="")
    create_parser.add_argument("--template", choices=list(ACTION_TEMPLATES.keys()), help="Create from template")

    # Update
    update_parser = subparsers.add_parser("update", help="Update an action")
    update_parser.add_argument("--id", required=True)
    update_parser.add_argument("--title")
    update_parser.add_argument("--description")
    update_parser.add_argument("--status")
    update_parser.add_argument("--progress", type=int)
    update_parser.add_argument("--owner")
    update_parser.add_argument("--actual-effort")
    update_parser.add_argument("--due-date")
    update_parser.add_argument("--notes")

    # List
    list_parser = subparsers.add_parser("list", help="List actions")
    list_parser.add_argument("--gap-id")
    list_parser.add_argument("--status")
    list_parser.add_argument("--owner")

    # Delete
    delete_parser = subparsers.add_parser("delete", help="Delete an action")
    delete_parser.add_argument("--id", required=True)

    # Report
    subparsers.add_parser("report", help="Generate remediation report")

    # Burndown
    subparsers.add_parser("burndown", help="Show burndown data")

    # Summary
    summary_parser = subparsers.add_parser("summary", help="Get gap summary")
    summary_parser.add_argument("--gap-id", required=True)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    tracker = RemediationTracker(args.registry, args.actions, verbose=args.verbose)

    if args.command == "create":
        if args.template:
            actions = tracker.create_from_template(args.gap_id, args.template, args.owner)
            print(f"Created {len(actions)} actions from '{args.template}' template:")
            for a in actions:
                print(f"  {a.id}: {a.title}")
        else:
            action = tracker.create_action(
                gap_id=args.gap_id,
                title=args.title,
                description=args.description,
                owner=args.owner,
                priority=args.priority,
                estimated_effort=args.estimated_effort,
                due_date=args.due_date,
            )
            print(f"Created action {action.id}: {action.title}")

    elif args.command == "update":
        action = tracker.update_action(
            action_id=args.id,
            title=args.title,
            description=args.description,
            status=args.status,
            progress=args.progress,
            owner=args.owner,
            actual_effort=args.actual_effort,
            due_date=args.due_date,
            notes=args.notes,
        )
        print(f"Updated action {action.id}: {action.title} (status={action.status.value}, progress={action.progress}%)")

    elif args.command == "list":
        actions = tracker.list_actions(gap_id=args.gap_id, status=args.status, owner=args.owner)
        if not actions:
            print("No actions found.")
        for a in actions:
            print(f"  {a.id} | {a.gap_id} | {a.status.value:15s} | {a.progress:3d}% | {a.title}")

    elif args.command == "delete":
        if tracker.delete_action(args.id):
            print(f"Deleted action {args.id}")
        else:
            print(f"Action not found: {args.id}")

    elif args.command == "report":
        report = tracker.generate_report()
        print(report)

    elif args.command == "burndown":
        data = tracker.get_burndown_data()
        print(json.dumps(data, indent=2))

    elif args.command == "summary":
        summary = tracker.get_gap_summary(args.gap_id)
        print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
