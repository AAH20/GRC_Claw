#!/usr/bin/env python3
"""
GRC_Claw Progress Reporting Generator

Generates comprehensive progress reports in multiple formats:
- Markdown (for documentation)
- JSON (for programmatic consumption)
- HTML (for web viewing)
- Slack/Teams summary (for chat notifications)

Usage:
    python gap_reporter.py [--registry gaps.json] [--format markdown|json|html|slack] [--output report.md]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gap_model import (
    Gap, GapStatus, GapCategory, GapSeverity,
    load_gaps, load_actions, initialize_gap_registry, save_actions
)

DEFAULT_REGISTRY = Path(__file__).resolve().parent / "gap_registry.json"
DEFAULT_ACTIONS = Path(__file__).resolve().parent / "gap_actions.json"


def generate_markdown_report(gaps: list[Gap], actions: list) -> str:
    """Generate a Markdown progress report."""
    now = datetime.now(timezone.utc)
    total = len(gaps)
    status_counts = Counter(g.status.value for g in gaps)
    category_counts = Counter(g.category.value for g in gaps)
    severity_counts = Counter(g.severity.value for g in gaps)
    avg_progress = sum(g.progress for g in gaps) / total if total else 0
    avg_priority = sum(g.priority_score for g in gaps) / total if total else 0

    resolved = status_counts.get("mitigated", 0) + status_counts.get("closed", 0)
    in_flight = status_counts.get("in_progress", 0) + status_counts.get("implementing", 0) + status_counts.get("validating", 0)
    not_started = status_counts.get("identified", 0) + status_counts.get("analyzing", 0) + status_counts.get("planned", 0)

    # Phase progress
    phases = {
        "Phase 1 — Foundation (Months 1-6)": ["GAP-008", "GAP-005", "GAP-015", "GAP-010"],
        "Phase 2 — Core Platform (Months 4-10)": ["GAP-001", "GAP-003", "GAP-004", "GAP-012"],
        "Phase 3 — Advanced Capabilities (Months 8-14)": ["GAP-002", "GAP-006", "GAP-016", "GAP-007", "GAP-013"],
        "Phase 4 — Ecosystem (Months 12-18)": ["GAP-009", "GAP-011", "GAP-017", "GAP-018", "GAP-019", "GAP-014", "GAP-020"],
    }
    gap_map = {g.id: g for g in gaps}

    lines = [
        "# GRC_Claw Gap Progress Report",
        "",
        f"**Generated:** {now.strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Period:** {now.strftime('%B %Y')}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Gaps | {total} |",
        f"| Resolved (Mitigated/Closed) | {resolved} |",
        f"| In Flight (In Progress/Implementing/Validating) | {in_flight} |",
        f"| Not Started (Identified/Analyzing/Planned) | {not_started} |",
        f"| Deferred | {status_counts.get('deferred', 0)} |",
        f"| Accepted Risk | {status_counts.get('accepted', 0)} |",
        f"| Average Progress | {avg_progress:.1f}% |",
        f"| Average Priority Score | {avg_priority:.1f} |",
        "",
        "### Status Distribution",
        "",
    ]
    for status, count in status_counts.most_common():
        pct = count / total * 100
        lines.append(f"- **{status.replace('_', ' ').title()}:** {count} ({pct:.0f}%)")

    lines.extend(["", "### Category Distribution", ""])
    for cat, count in category_counts.most_common():
        lines.append(f"- **{cat.title()}:** {count}")

    lines.extend(["", "### Severity Distribution", ""])
    for sev, count in severity_counts.most_common():
        lines.append(f"- **{sev.upper()}:** {count}")

    lines.extend(["", "---", "", "## Phase Progress", ""])
    for phase_name, phase_ids in phases.items():
        phase_gaps = [gap_map[gid] for gid in phase_ids if gid in gap_map]
        if not phase_gaps:
            continue
        phase_progress = sum(g.progress for g in phase_gaps) / len(phase_gaps)
        phase_resolved = sum(1 for g in phase_gaps if g.status in (GapStatus.MITIGATED, GapStatus.CLOSED))
        lines.append(f"### {phase_name}")
        lines.append(f"- **Progress:** {phase_progress:.0f}%")
        lines.append(f"- **Resolved:** {phase_resolved}/{len(phase_gaps)}")
        lines.append("")
        for g in phase_gaps:
            status_icon = "✅" if g.status in (GapStatus.MITIGATED, GapStatus.CLOSED) else "🔄" if g.status in (GapStatus.IN_PROGRESS, GapStatus.IMPLEMENTING) else "⏳"
            lines.append(f"  - {status_icon} **{g.id}** {g.name} — {g.progress}% ({g.status.value.replace('_', ' ').title()})")
        lines.append("")

    lines.extend(["---", "", "## Top 10 Priority Gaps", ""])
    lines.append("| Rank | ID | Gap | Priority | Status | Progress | Severity |")
    lines.append("|------|-----|-----|----------|--------|----------|----------|")
    for i, g in enumerate(sorted(gaps, key=lambda x: -x.priority_score)[:10], 1):
        lines.append(f"| {i} | {g.id} | {g.name} | {g.priority_score:.0f} | {g.status.value.replace('_', ' ').title()} | {g.progress}% | {g.severity.value.upper()} |")

    lines.extend(["", "---", "", "## Remediation Actions", ""])
    if actions:
        action_status_counts = Counter(a.status.value for a in actions)
        lines.append(f"**Total Actions:** {len(actions)}")
        lines.append("")
        for status, count in action_status_counts.most_common():
            lines.append(f"- **{status.replace('_', ' ').title()}:** {count}")
        lines.append("")
        lines.append("| Action | Gap | Title | Status | Progress | Owner |")
        lines.append("|--------|-----|-------|--------|----------|-------|")
        for a in sorted(actions, key=lambda x: x.gap_id):
            lines.append(f"| {a.id} | {a.gap_id} | {a.title} | {a.status.value.replace('_', ' ').title()} | {a.progress}% | {a.owner or '—'} |")
    else:
        lines.append("No remediation actions tracked yet.")

    lines.extend(["", "---", "", "## Risks and Blockers", ""])
    critical_open = [g for g in gaps if g.severity == GapSeverity.CRITICAL and g.status not in (GapStatus.CLOSED, GapStatus.MITIGATED)]
    if critical_open:
        lines.append("### Critical Open Gaps")
        for g in critical_open:
            lines.append(f"- **{g.id}** {g.name} — {g.progress}% complete")
    else:
        lines.append("No critical open gaps.")

    lines.extend(["", "---", "", "## Recommendations", ""])
    if avg_progress < 30:
        lines.append("1. **Accelerate Phase 1** — Focus on high-feasibility gaps (GAP-008, GAP-005) for quick wins.")
    if critical_open:
        lines.append(f"2. **Address Critical Gaps** — {len(critical_open)} critical gaps remain open. Prioritize agentic AI governance (GAP-002).")
    lines.append(f"3. **Maintain Momentum** — {in_flight} gaps are in flight. Ensure weekly progress updates.")
    lines.append(f"4. **Review Deferred** — {status_counts.get('deferred', 0)} gaps are deferred. Reassess quarterly.")

    lines.extend(["", "---", "", f"*Report generated by GRC_Claw Gap Management Framework*"])
    return "\n".join(lines)


def generate_slack_summary(gaps: list[Gap], actions: list) -> str:
    """Generate a concise Slack/Teams summary."""
    now = datetime.now(timezone.utc)
    total = len(gaps)
    status_counts = Counter(g.status.value for g in gaps)
    resolved = status_counts.get("mitigated", 0) + status_counts.get("closed", 0)
    in_flight = status_counts.get("in_progress", 0) + status_counts.get("implementing", 0)
    avg_progress = sum(g.progress for g in gaps) / total if total else 0
    critical_open = sum(1 for g in gaps if g.severity == GapStatus.CRITICAL and g.status not in (GapStatus.CLOSED, GapStatus.MITIGATED))

    lines = [
        f"*GRC_Claw Gap Report — {now.strftime('%Y-%m-%d')}*",
        f"",
        f"• Total gaps: *{total}*",
        f"• Resolved: *{resolved}* ({resolved/total*100:.0f}%)",
        f"• In flight: *{in_flight}*",
        f"• Avg progress: *{avg_progress:.0f}%*",
        f"• Critical open: *{critical_open}*",
    ]

    if critical_open:
        lines.append(f"")
        lines.append(f"*Critical gaps needing attention:*")
        for g in sorted(gaps, key=lambda x: -x.priority_score):
            if g.severity == GapStatus.CRITICAL and g.status not in (GapStatus.CLOSED, GapStatus.MITIGATED):
                lines.append(f"  • {g.id}: {g.name} ({g.progress}%)")

    return "\n".join(lines)


def generate_html_report(gaps: list[Gap], actions: list) -> str:
    """Generate an HTML progress report."""
    now = datetime.now(timezone.utc)
    total = len(gaps)
    status_counts = Counter(g.status.value for g in gaps)
    avg_progress = sum(g.progress for g in gaps) / total if total else 0
    resolved = status_counts.get("mitigated", 0) + status_counts.get("closed", 0)

    rows = []
    for g in sorted(gaps, key=lambda x: -x.priority_score):
        status_color = "#28a745" if g.status in (GapStatus.MITIGATED, GapStatus.CLOSED) else "#ffc107" if g.status in (GapStatus.IN_PROGRESS, GapStatus.IMPLEMENTING) else "#6c757d"
        rows.append(f"<tr><td>{g.id}</td><td>{g.name}</td><td><span style='color:{status_color};font-weight:600'>{g.status.value.replace('_', ' ').title()}</span></td><td>{g.priority_score:.0f}</td><td>{g.progress}%</td><td>{g.severity.value.upper()}</td></tr>")

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>GRC_Claw Gap Report</title>
<style>
body {{ font-family: -apple-system, sans-serif; background: #f5f5f5; padding: 20px; }}
.container {{ max-width: 1000px; margin: 0 auto; background: #fff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
h1 {{ color: #1a1a2e; }}
.summary {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 20px 0; }}
.summary-card {{ background: #f8f9fa; border-radius: 6px; padding: 16px; text-align: center; }}
.summary-value {{ font-size: 28px; font-weight: 700; color: #1a1a2e; }}
.summary-label {{ font-size: 12px; color: #6c757d; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 13px; }}
th {{ text-align: left; padding: 10px; border-bottom: 2px solid #dee2e6; }}
td {{ padding: 8px 10px; border-bottom: 1px solid #eee; }}
tr:hover {{ background: #f8f9fa; }}
</style></head><body>
<div class="container">
<h1>GRC_Claw Gap Progress Report</h1>
<p>Generated: {now.strftime('%Y-%m-%d %H:%M UTC')}</p>
<div class="summary">
<div class="summary-card"><div class="summary-value">{total}</div><div class="summary-label">Total Gaps</div></div>
<div class="summary-card"><div class="summary-value">{resolved}</div><div class="summary-label">Resolved</div></div>
<div class="summary-card"><div class="summary-value">{avg_progress:.0f}%</div><div class="summary-label">Avg Progress</div></div>
<div class="summary-card"><div class="summary-value">{total - resolved}</div><div class="summary-label">Open</div></div>
</div>
<table><thead><tr><th>ID</th><th>Gap</th><th>Status</th><th>Priority</th><th>Progress</th><th>Severity</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
</div></body></html>"""
    return html


def main():
    parser = argparse.ArgumentParser(description="GRC_Claw Progress Reporter")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--actions", type=Path, default=DEFAULT_ACTIONS)
    parser.add_argument("--format", choices=["markdown", "json", "html", "slack"], default="markdown")
    parser.add_argument("--output", "-o", type=Path, default=None)
    args = parser.parse_args()

    gaps = initialize_gap_registry(args.registry)
    actions = load_actions(args.actions) if args.actions.exists() else []

    if args.format == "markdown":
        content = generate_markdown_report(gaps, actions)
        ext = ".md"
    elif args.format == "json":
        content = json.dumps({
            "generated": datetime.now(timezone.utc).isoformat(),
            "total_gaps": len(gaps),
            "gaps": [g.to_dict() for g in gaps],
            "actions": [a.to_dict() for a in actions],
        }, indent=2, default=str)
        ext = ".json"
    elif args.format == "html":
        content = generate_html_report(gaps, actions)
        ext = ".html"
    elif args.format == "slack":
        content = generate_slack_summary(gaps, actions)
        ext = ".txt"
    else:
        content = generate_markdown_report(gaps, actions)
        ext = ".md"

    if args.output:
        output_path = args.output
    else:
        output_path = Path(f"gap_report_{datetime.now(timezone.utc).strftime('%Y%m%d')}{ext}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(f"Report generated: {output_path} ({args.format})")


if __name__ == "__main__":
    main()
