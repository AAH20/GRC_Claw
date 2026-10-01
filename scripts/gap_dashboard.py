#!/usr/bin/env python3
"""
GRC_Claw Gap Tracking Dashboard

Generates an interactive HTML dashboard for visualizing gap status,
progress, priority distribution, and trends. Self-contained — no external
dependencies required.

Usage:
    python gap_dashboard.py [--registry gaps.json] [--output dashboard.html]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gap_model import (
    Gap, GapStatus, GapCategory, GapSeverity,
    load_gaps, initialize_gap_registry
)

DEFAULT_REGISTRY = Path(__file__).resolve().parent / "gap_registry.json"


def _status_color(status: str) -> str:
    colors = {
        "identified": "#6c757d", "analyzing": "#17a2b8", "planned": "#007bff",
        "in_progress": "#ffc107", "implementing": "#fd7e14", "validating": "#6f42c1",
        "mitigated": "#28a745", "closed": "#20c997", "deferred": "#dc3545",
        "accepted": "#6c757d"
    }
    return colors.get(status, "#6c757d")


def _severity_color(severity: str) -> str:
    colors = {
        "critical": "#dc3545", "high": "#fd7e14", "medium": "#ffc107",
        "low": "#28a745", "info": "#17a2b8"
    }
    return colors.get(severity, "#6c757d")


def generate_dashboard(gaps: list[Gap], output_path: Path) -> None:
    """Generate a self-contained HTML dashboard."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Compute stats
    total = len(gaps)
    status_counts = Counter(g.status.value for g in gaps)
    category_counts = Counter(g.category.value for g in gaps)
    severity_counts = Counter(g.severity.value for g in gaps)
    avg_progress = sum(g.progress for g in gaps) / total if total else 0
    avg_priority = sum(g.priority_score for g in gaps) / total if total else 0
    critical_open = sum(1 for g in gaps if g.severity == GapSeverity.CRITICAL and g.status not in (GapStatus.CLOSED, GapStatus.MITIGATED))
    high_open = sum(1 for g in gaps if g.severity == GapSeverity.HIGH and g.status not in (GapStatus.CLOSED, GapStatus.MITIGATED))

    # Build gap rows
    gap_rows = []
    for g in sorted(gaps, key=lambda x: -x.priority_score):
        sc = _status_color(g.status.value)
        sev_c = _severity_color(g.severity.value)
        prog_color = "#28a745" if g.progress >= 75 else "#ffc107" if g.progress >= 40 else "#dc3545"
        gap_rows.append(f"""
        <tr data-status="{g.status.value}" data-category="{g.category.value}" data-severity="{g.severity.value}">
            <td><span class="gap-id">{g.id}</span></td>
            <td>{g.name}</td>
            <td><span class="badge" style="background:{sc}">{g.status.value.replace('_', ' ').title()}</span></td>
            <td><span class="badge" style="background:{sev_c}">{g.severity.value.upper()}</span></td>
            <td>{g.category.value.title()}</td>
            <td class="priority-cell">{g.priority_score:.0f}</td>
            <td>
                <div class="progress-bar-container">
                    <div class="progress-bar" style="width:{g.progress}%;background:{prog_color}">{g.progress}%</div>
                </div>
            </td>
            <td>{g.owner or '—'}</td>
            <td>{g.target_date or '—'}</td>
        </tr>""")

    # Status distribution chart data
    status_labels = list(status_counts.keys())
    status_values = list(status_counts.values())
    status_colors = [_status_color(s) for s in status_labels]

    # Category distribution
    cat_labels = list(category_counts.keys())
    cat_values = list(category_counts.values())

    # Severity distribution
    sev_labels = list(severity_counts.keys())
    sev_values = list(severity_counts.values())
    sev_colors = [_severity_color(s) for s in sev_labels]

    # Priority top 10
    top_gaps = sorted(gaps, key=lambda x: -x.priority_score)[:10]
    top_gap_names = [g.name[:30] + "..." if len(g.name) > 30 else g.name for g in top_gaps]
    top_gap_scores = [g.priority_score for g in top_gaps]

    # Phase grouping
    phases = {
        "Phase 1 — Foundation": [g for g in gaps if g.id in ("GAP-008", "GAP-005", "GAP-015", "GAP-010")],
        "Phase 2 — Core Platform": [g for g in gaps if g.id in ("GAP-001", "GAP-003", "GAP-004", "GAP-012")],
        "Phase 3 — Advanced": [g for g in gaps if g.id in ("GAP-002", "GAP-006", "GAP-016", "GAP-007", "GAP-013")],
        "Phase 4 — Ecosystem": [g for g in gaps if g.id in ("GAP-009", "GAP-011", "GAP-017", "GAP-018", "GAP-019", "GAP-014", "GAP-020")],
    }
    phase_cards = []
    for phase_name, phase_gaps in phases.items():
        phase_progress = sum(g.progress for g in phase_gaps) / len(phase_gaps) if phase_gaps else 0
        phase_open = sum(1 for g in phase_gaps if g.status not in (GapStatus.CLOSED, GapStatus.MITIGATED))
        phase_done = sum(1 for g in phase_gaps if g.status in (GapStatus.CLOSED, GapStatus.MITIGATED))
        phase_cards.append(f"""
        <div class="phase-card">
            <h4>{phase_name}</h4>
            <div class="phase-stats">
                <span>{len(phase_gaps)} gaps</span>
                <span>{phase_done} done</span>
                <span>{phase_open} open</span>
            </div>
            <div class="progress-bar-container">
                <div class="progress-bar" style="width:{phase_progress:.0f}%;background:#007bff">{phase_progress:.0f}%</div>
            </div>
        </div>""")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GRC_Claw Gap Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px; }}
        .dashboard {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ color: #58a6ff; margin-bottom: 5px; font-size: 28px; }}
        .subtitle {{ color: #8b949e; margin-bottom: 20px; font-size: 14px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 24px; }}
        .stat-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; text-align: center; }}
        .stat-value {{ font-size: 32px; font-weight: 700; color: #58a6ff; }}
        .stat-label {{ font-size: 12px; color: #8b949e; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; }}
        .stat-card.critical .stat-value {{ color: #f85149; }}
        .stat-card.warning .stat-value {{ color: #d29922; }}
        .stat-card.success .stat-value {{ color: #3fb950; }}
        .section {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
        .section h2 {{ color: #58a6ff; margin-bottom: 16px; font-size: 18px; }}
        .charts-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }}
        .chart-container {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; }}
        .chart-container h3 {{ color: #8b949e; font-size: 14px; margin-bottom: 12px; }}
        .bar-chart {{ display: flex; flex-direction: column; gap: 6px; }}
        .bar-row {{ display: flex; align-items: center; gap: 8px; }}
        .bar-label {{ width: 100px; font-size: 11px; color: #8b949e; text-align: right; flex-shrink: 0; }}
        .bar-track {{ flex: 1; background: #21262d; border-radius: 4px; height: 20px; overflow: hidden; }}
        .bar-fill {{ height: 100%; border-radius: 4px; display: flex; align-items: center; justify-content: flex-end; padding-right: 6px; font-size: 10px; color: #fff; font-weight: 600; min-width: 20px; }}
        .phase-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; }}
        .phase-card {{ background: #21262d; border: 1px solid #30363d; border-radius: 6px; padding: 14px; }}
        .phase-card h4 {{ color: #c9d1d9; font-size: 13px; margin-bottom: 8px; }}
        .phase-stats {{ display: flex; gap: 12px; font-size: 11px; color: #8b949e; margin-bottom: 8px; }}
        .progress-bar-container {{ background: #21262d; border-radius: 4px; height: 18px; overflow: hidden; }}
        .progress-bar {{ height: 100%; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 10px; color: #fff; font-weight: 600; min-width: 30px; transition: width 0.3s; }}
        .gap-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        .gap-table th {{ text-align: left; padding: 10px 12px; border-bottom: 2px solid #30363d; color: #8b949e; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }}
        .gap-table td {{ padding: 10px 12px; border-bottom: 1px solid #21262d; }}
        .gap-table tr:hover {{ background: #1c2128; }}
        .gap-id {{ font-family: monospace; color: #58a6ff; font-size: 12px; }}
        .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; color: #fff; font-weight: 600; }}
        .priority-cell {{ font-weight: 700; color: #d29922; }}
        .filters {{ display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }}
        .filter-btn {{ padding: 6px 14px; border: 1px solid #30363d; border-radius: 6px; background: #21262d; color: #8b949e; cursor: pointer; font-size: 12px; }}
        .filter-btn:hover, .filter-btn.active {{ background: #1f6feb; color: #fff; border-color: #1f6feb; }}
        .timestamp {{ color: #8b949e; font-size: 12px; margin-top: 20px; text-align: center; }}
    </style>
</head>
<body>
    <div class="dashboard">
        <h1>GRC_Claw Gap Dashboard</h1>
        <p class="subtitle">AI Governance Gap Tracking &bull; {total} gaps tracked</p>

        <div class="stats-grid">
            <div class="stat-card"><div class="stat-value">{total}</div><div class="stat-label">Total Gaps</div></div>
            <div class="stat-card critical"><div class="stat-value">{critical_open}</div><div class="stat-label">Critical Open</div></div>
            <div class="stat-card warning"><div class="stat-value">{high_open}</div><div class="stat-label">High Open</div></div>
            <div class="stat-card success"><div class="stat-value">{status_counts.get('mitigated', 0) + status_counts.get('closed', 0)}</div><div class="stat-label">Resolved</div></div>
            <div class="stat-card"><div class="stat-value">{avg_progress:.0f}%</div><div class="stat-label">Avg Progress</div></div>
            <div class="stat-card"><div class="stat-value">{avg_priority:.0f}</div><div class="stat-label">Avg Priority</div></div>
        </div>

        <div class="charts-grid">
            <div class="chart-container">
                <h3>Status Distribution</h3>
                <div class="bar-chart">
                    {''.join(f'<div class="bar-row"><div class="bar-label">{s.replace("_", " ").title()}</div><div class="bar-track"><div class="bar-fill" style="width:{v/total*100:.0f}%;background:{_status_color(s)}">{v}</div></div></div>' for s, v in status_counts.most_common())}
                </div>
            </div>
            <div class="chart-container">
                <h3>Category Distribution</h3>
                <div class="bar-chart">
                    {''.join(f'<div class="bar-row"><div class="bar-label">{c.title()}</div><div class="bar-track"><div class="bar-fill" style="width:{v/total*100:.0f}%;background:#58a6ff">{v}</div></div></div>' for c, v in category_counts.most_common())}
                </div>
            </div>
            <div class="chart-container">
                <h3>Severity Distribution</h3>
                <div class="bar-chart">
                    {''.join(f'<div class="bar-row"><div class="bar-label">{s.upper()}</div><div class="bar-track"><div class="bar-fill" style="width:{v/total*100:.0f}%;background:{_severity_color(s)}">{v}</div></div></div>' for s, v in severity_counts.most_common())}
                </div>
            </div>
            <div class="chart-container">
                <h3>Top 10 Priority Gaps</h3>
                <div class="bar-chart">
                    {''.join(f'<div class="bar-row"><div class="bar-label">{n}</div><div class="bar-track"><div class="bar-fill" style="width:{s/100*100:.0f}%;background:#d29922">{s:.0f}</div></div></div>' for n, s in zip(top_gap_names, top_gap_scores))}
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Implementation Phases</h2>
            <div class="phase-grid">
                {''.join(phase_cards)}
            </div>
        </div>

        <div class="section">
            <h2>Gap Registry</h2>
            <div class="filters">
                <button class="filter-btn active" onclick="filterTable('all')">All</button>
                <button class="filter-btn" onclick="filterTable('critical')">Critical</button>
                <button class="filter-btn" onclick="filterTable('high')">High</button>
                <button class="filter-btn" onclick="filterTable('in_progress')">In Progress</button>
                <button class="filter-btn" onclick="filterTable('mitigated')">Mitigated</button>
                <button class="filter-btn" onclick="filterTable('closed')">Closed</button>
            </div>
            <table class="gap-table" id="gapTable">
                <thead>
                    <tr>
                        <th>ID</th><th>Gap Name</th><th>Status</th><th>Severity</th>
                        <th>Category</th><th>Priority</th><th>Progress</th>
                        <th>Owner</th><th>Target Date</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(gap_rows)}
                </tbody>
            </table>
        </div>

        <p class="timestamp">Generated: {now} &bull; GRC_Claw Gap Management Framework</p>
    </div>

    <script>
        function filterTable(filter) {{
            const rows = document.querySelectorAll('#gapTable tbody tr');
            const buttons = document.querySelectorAll('.filter-btn');
            buttons.forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');
            rows.forEach(row => {{
                if (filter === 'all' || row.dataset.status === filter || row.dataset.severity === filter) {{
                    row.style.display = '';
                }} else {{
                    row.style.display = 'none';
                }}
            }});
        }}
    </script>
</body>
</html>"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"Dashboard generated: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="GRC_Claw Gap Dashboard Generator")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY, help="Path to gap registry JSON")
    parser.add_argument("--output", "-o", type=Path, default=Path("gap_dashboard.html"), help="Output HTML path")
    args = parser.parse_args()

    gaps = initialize_gap_registry(args.registry)
    generate_dashboard(gaps, args.output)


if __name__ == "__main__":
    main()
