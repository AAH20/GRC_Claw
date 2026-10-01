#!/usr/bin/env python3
"""
GRC_Claw Automated Gap Detection Engine

Scans the codebase, specs, and gap blueprints to detect:
- New gaps not yet in the registry
- Status changes in existing gaps
- Blueprint coverage gaps
- Implementation progress signals
- Stale gaps needing attention

Usage:
    python gap_detector.py [--registry gaps.json] [--output report.json] [--verbose]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gap_model import (
    Gap, GapStatus, GapCategory, GapSeverity,
    load_gaps, save_gaps, initialize_gap_registry, CANONICAL_GAPS
)

REPO_ROOT = Path(__file__).resolve().parent.parent
BLUEPRINT_DIR = REPO_ROOT / "gap-blueprints"
SPECS_DIR = REPO_ROOT / "specs"
SCRIPTS_DIR = REPO_ROOT / "scripts"
DEFAULT_REGISTRY = SCRIPTS_DIR / "gap_registry.json"


class GapDetector:
    """Detects gaps by scanning repository artifacts."""

    def __init__(self, registry_path: Path, verbose: bool = False):
        self.registry_path = registry_path
        self.verbose = verbose
        self.gaps: list[Gap] = initialize_gap_registry(registry_path)
        self.findings: list[dict[str, Any]] = []
        self.new_gaps: list[Gap] = []
        self.status_changes: list[dict[str, Any]] = []
        self.stale_gaps: list[Gap] = []
        self.coverage_gaps: list[dict[str, Any]] = []

    def log(self, msg: str) -> None:
        if self.verbose:
            print(f"[detector] {msg}")

    def detect_blueprint_coverage(self) -> None:
        """Check which gaps have blueprint documents and which don't."""
        blueprint_files = list(BLUEPRINT_DIR.glob("*.md")) if BLUEPRINT_DIR.exists() else []
        blueprint_text = ""
        for bf in blueprint_files:
            blueprint_text += bf.read_text(errors="ignore").lower()

        for gap in self.gaps:
            # Check if gap is mentioned in any blueprint
            gap_keywords = gap.name.lower().split()[:3]  # First 3 words
            found = any(kw in blueprint_text for kw in gap_keywords if len(kw) > 3)
            if not found:
                self.coverage_gaps.append({
                    "gap_id": gap.id,
                    "gap_name": gap.name,
                    "issue": "No blueprint coverage detected",
                    "severity": "medium",
                    "recommendation": f"Create blueprint document for {gap.id}"
                })
                self.log(f"Coverage gap: {gap.id} - {gap.name}")

    def detect_implementation_signals(self) -> None:
        """Scan specs and scripts for implementation signals."""
        all_files = list(SPECS_DIR.glob("*.md")) + list(SCRIPTS_DIR.glob("*.py")) + list(SCRIPTS_DIR.glob("*.mjs"))
        file_contents: dict[str, str] = {}
        for f in all_files:
            try:
                file_contents[f.name] = f.read_text(errors="ignore").lower()
            except Exception:
                continue

        for gap in self.gaps:
            gap_keywords = [kw.lower() for kw in gap.name.split() if len(kw) > 4]
            mentions: list[str] = []
            for fname, content in file_contents.items():
                if any(kw in content for kw in gap_keywords):
                    mentions.append(fname)

            if mentions and gap.status in (GapStatus.IDENTIFIED, GapStatus.ANALYZING):
                self.status_changes.append({
                    "gap_id": gap.id,
                    "gap_name": gap.name,
                    "current_status": gap.status.value,
                    "suggested_status": GapStatus.IN_PROGRESS.value,
                    "evidence": f"Found implementation signals in: {', '.join(mentions[:5])}",
                    "confidence": min(0.9, 0.3 + 0.1 * len(mentions))
                })
                self.log(f"Implementation signal: {gap.id} mentioned in {len(mentions)} files")

    def detect_stale_gaps(self, days_threshold: int = 30) -> None:
        """Find gaps that haven't been updated recently."""
        now = datetime.now(timezone.utc)
        for gap in self.gaps:
            if gap.status in (GapStatus.CLOSED, GapStatus.MITIGATED):
                continue
            try:
                last = datetime.fromisoformat(gap.last_updated.replace("Z", "+00:00"))
                days_stale = (now - last).days
                if days_stale > days_threshold:
                    self.stale_gaps.append(gap)
                    self.log(f"Stale gap: {gap.id} ({days_stale} days)")
            except (ValueError, AttributeError):
                pass

    def detect_priority_drift(self) -> None:
        """Detect gaps whose priority may have shifted based on dependencies."""
        gap_map = {g.id: g for g in self.gaps}
        for gap in self.gaps:
            if not gap.dependencies:
                continue
            dep_scores = []
            for dep_id in gap.dependencies:
                if dep_id in gap_map:
                    dep = gap_map[dep_id]
                    if dep.status in (GapStatus.MITIGATED, GapStatus.CLOSED):
                        dep_scores.append(1.0)
                    elif dep.status == GapStatus.IN_PROGRESS:
                        dep_scores.append(0.5)
                    else:
                        dep_scores.append(0.0)
            if dep_scores and all(s > 0 for s in dep_scores):
                # All dependencies resolved — priority may increase
                self.findings.append({
                    "type": "priority_increase",
                    "gap_id": gap.id,
                    "gap_name": gap.name,
                    "message": f"All {len(dep_scores)} dependencies resolved. Consider increasing priority.",
                    "current_score": gap.priority_score,
                    "suggested_score": min(100, gap.priority_score * 1.1)
                })

    def detect_new_gaps_from_specs(self) -> None:
        """Scan specs for potential new gaps not in the registry."""
        if not SPECS_DIR.exists():
            return
        existing_names = {g.name.lower() for g in self.gaps}
        existing_ids = {g.id for g in self.gaps}

        gap_pattern = re.compile(
            r"(?:gap|missing|lack|no|without|absence of)\s+"
            r"(?:unified|standard|automated|real-time|universal|automated|cross-border|"
            r"multi-agent|governance|policy|compliance|audit|risk|bias|fairness|"
            r"incident|model|vendor|asset|edge|iot|regulatory|certification|"
            r"metrics|monitoring|enforcement|inventory|playbook|versioning|"
            r"mapping|sbom|dashboard|framework|protocol|language|engine)"
            r"[\w\s\-]{5,80}",
            re.IGNORECASE
        )

        for spec_file in SPECS_DIR.glob("*.md"):
            content = spec_file.read_text(errors="ignore")
            matches = gap_pattern.findall(content)
            for match in matches:
                match_clean = match.strip().lower()
                # Check if this is already tracked
                is_tracked = any(
                    match_clean in name or name in match_clean
                    for name in existing_names
                )
                if not is_tracked and len(match_clean) > 10:
                    new_id = f"GAP-{len(self.gaps) + len(self.new_gaps) + 1:03d}"
                    if new_id not in existing_ids:
                        self.new_gaps.append(Gap(
                            id=new_id,
                            name=match_clean.title(),
                            description=f"Auto-detected from {spec_file.name}",
                            category=GapCategory.TOOLING,
                            impact=5,
                            feasibility=5,
                            priority_score=25.0,
                            status=GapStatus.IDENTIFIED,
                            severity=GapSeverity.LOW,
                            tags=["auto-detected"],
                            blueprint_ref=spec_file.name
                        ))
                        self.log(f"New gap detected: {new_id} from {spec_file.name}")

    def detect_status_inconsistencies(self) -> None:
        """Find gaps with inconsistent status/progress combinations."""
        for gap in self.gaps:
            if gap.progress == 100 and gap.status not in (GapStatus.MITIGATED, GapStatus.CLOSED):
                self.findings.append({
                    "type": "status_inconsistency",
                    "gap_id": gap.id,
                    "gap_name": gap.name,
                    "message": f"Progress is 100% but status is {gap.status.value}",
                    "suggested_status": GapStatus.MITIGATED.value
                })
            elif gap.progress > 0 and gap.status == GapStatus.IDENTIFIED:
                self.findings.append({
                    "type": "status_inconsistency",
                    "gap_id": gap.id,
                    "gap_name": gap.name,
                    "message": f"Progress is {gap.progress}% but status is 'identified'",
                    "suggested_status": GapStatus.IN_PROGRESS.value
                })
            elif gap.progress == 0 and gap.status in (GapStatus.IN_PROGRESS, GapStatus.IMPLEMENTING):
                self.findings.append({
                    "type": "status_inconsistency",
                    "gap_id": gap.id,
                    "gap_name": gap.name,
                    "message": f"Status is {gap.status.value} but progress is 0%",
                    "suggested_status": GapStatus.PLANNED.value
                })

    def run(self) -> dict[str, Any]:
        """Execute all detection passes."""
        self.log("Starting gap detection...")

        self.detect_blueprint_coverage()
        self.detect_implementation_signals()
        self.detect_stale_gaps()
        self.detect_priority_drift()
        self.detect_new_gaps_from_specs()
        self.detect_status_inconsistencies()

        # Merge new gaps into registry
        if self.new_gaps:
            self.gaps.extend(self.new_gaps)
            save_gaps(self.gaps, self.registry_path)

        report = {
            "scan_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_gaps": len(self.gaps),
            "new_gaps_detected": len(self.new_gaps),
            "status_changes_detected": len(self.status_changes),
            "stale_gaps": len(self.stale_gaps),
            "coverage_gaps": len(self.coverage_gaps),
            "findings": self.findings,
            "new_gaps": [g.to_dict() for g in self.new_gaps],
            "status_changes": self.status_changes,
            "stale_gap_ids": [g.id for g in self.stale_gaps],
            "coverage_gaps": self.coverage_gaps,
        }

        self.log(f"Detection complete: {len(self.new_gaps)} new, {len(self.status_changes)} status changes, {len(self.stale_gaps)} stale")
        return report


def main():
    parser = argparse.ArgumentParser(description="GRC_Claw Automated Gap Detector")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY, help="Path to gap registry JSON")
    parser.add_argument("--output", type=Path, default=None, help="Output report path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    detector = GapDetector(args.registry, verbose=args.verbose)
    report = detector.run()

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"Report saved to {args.output}")

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print(f"\n{'='*60}")
        print("GRC_Claw Gap Detection Report")
        print(f"{'='*60}")
        print(f"Scan time: {report['scan_timestamp']}")
        print(f"Total gaps in registry: {report['total_gaps']}")
        print(f"New gaps detected: {report['new_gaps_detected']}")
        print(f"Status changes detected: {report['status_changes_detected']}")
        print(f"Stale gaps: {report['stale_gaps']}")
        print(f"Coverage gaps: {report['coverage_gaps']}")
        print(f"Findings: {len(report['findings'])}")

        if report['new_gaps']:
            print(f"\n--- New Gaps ---")
            for g in report['new_gaps']:
                print(f"  {g['id']}: {g['name']}")

        if report['status_changes']:
            print(f"\n--- Status Changes ---")
            for sc in report['status_changes']:
                print(f"  {sc['gap_id']}: {sc['current_status']} -> {sc['suggested_status']} ({sc['confidence']:.0%} confidence)")

        if report['stale_gap_ids']:
            print(f"\n--- Stale Gaps ---")
            for gid in report['stale_gap_ids']:
                print(f"  {gid}")

        if report['coverage_gaps']:
            print(f"\n--- Coverage Gaps ---")
            for cg in report['coverage_gaps']:
                print(f"  {cg['gap_id']}: {cg['issue']}")

        if report['findings']:
            print(f"\n--- Findings ---")
            for f in report['findings']:
                print(f"  [{f['type']}] {f['gap_id']}: {f['message']}")


if __name__ == "__main__":
    main()
