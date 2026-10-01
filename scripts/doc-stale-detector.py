#!/usr/bin/env python3
"""
Stale content detector for GRC_Claw documentation.
Identifies potentially outdated documents based on multiple heuristics:
- Last modified date
- Content age indicators
- Broken or outdated references
- TODO/FIXME markers
- Version mismatches
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
DOC_EXTENSIONS = {".md", ".mdx"}
EXCLUDE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}

# Patterns indicating stale content
TODO_PATTERN = re.compile(r"\b(TODO|FIXME|HACK|XXX|NOTE:\s*deprecated|DEPRECATED)\b", re.IGNORECASE)
VERSION_PATTERN = re.compile(r"(?:version|v)?(\d+\.\d+(?:\.\d+)?)", re.IGNORECASE)
DATE_PATTERN = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
STALE_MARKERS = re.compile(
    r"\b(outdated|deprecated|obsolete|no longer|legacy|superseded|replaced by|"
    r"moved to|renamed to|will be removed|scheduled for removal)\b",
    re.IGNORECASE,
)


def find_doc_files(root: Path) -> List[Path]:
    """Recursively find all documentation files."""
    docs = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in DOC_EXTENSIONS:
            if not any(part in EXCLUDE_DIRS for part in path.parts):
                docs.append(path)
    return sorted(docs)


def get_file_age_days(filepath: Path) -> Optional[float]:
    """Get the age of a file in days based on modification time."""
    try:
        mtime = filepath.stat().st_mtime
        age = datetime.now() - datetime.fromtimestamp(mtime)
        return age.total_seconds() / 86400
    except Exception:
        return None


def extract_dates_from_content(content: str) -> List[datetime]:
    """Extract dates mentioned in content."""
    dates = []
    for match in DATE_PATTERN.finditer(content):
        try:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            if 2020 <= year <= 2030:
                dates.append(datetime(year, month, day))
        except ValueError:
            continue
    return dates


def extract_versions(content: str) -> List[str]:
    """Extract version numbers from content."""
    versions = []
    for match in VERSION_PATTERN.finditer(content):
        v = match.group(1)
        if v not in versions:
            versions.append(v)
    return versions


def count_stale_markers(content: str) -> Dict[str, int]:
    """Count various stale content markers."""
    markers = {
        "todo_fixme": len(TODO_PATTERN.findall(content)),
        "stale_references": len(STALE_MARKERS.findall(content)),
    }
    return markers


def check_content_freshness(content: str, filepath: Path) -> List[str]:
    """Check content for freshness indicators."""
    warnings = []

    # Check for TODO/FIXME markers
    todos = TODO_PATTERN.findall(content)
    if todos:
        warnings.append(f"Contains {len(todos)} TODO/FIXME marker(s)")

    # Check for stale references
    stale_refs = STALE_MARKERS.findall(content)
    if stale_refs:
        warnings.append(f"Contains {len(stale_refs)} stale reference marker(s)")

    # Check for old dates
    dates = extract_dates_from_content(content)
    if dates:
        oldest = min(dates)
        age_days = (datetime.now() - oldest).days
        if age_days > 365:
            warnings.append(f"References content from {oldest.strftime('%Y-%m-%d')} ({age_days} days old)")

    # Check for version references that might be outdated
    versions = extract_versions(content)
    if versions:
        # Flag if version is very old (heuristic: major version < 1)
        for v in versions:
            try:
                major = int(v.split(".")[0])
                if major == 0:
                    warnings.append(f"References version {v} (pre-1.0)")
            except (ValueError, IndexError):
                pass

    return warnings


def detect_stale_docs(
    root: Optional[Path] = None,
    age_threshold_days: int = 180,
    check_content: bool = True,
    check_git: bool = True,
) -> List[Dict]:
    """Detect potentially stale documents."""
    root = root or REPO_ROOT
    all_files = find_doc_files(root)
    stale_docs = []

    for doc in all_files:
        rel_path = str(doc.relative_to(root))
        issues = []
        age_days = get_file_age_days(doc)

        # Check file age
        if age_days is not None and age_days > age_threshold_days:
            issues.append(f"Last modified {int(age_days)} days ago (threshold: {age_threshold_days})")

        # Check content freshness
        if check_content:
            try:
                content = doc.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            content_warnings = check_content_freshness(content, doc)
            issues.extend(content_warnings)

            # Count stale markers
            markers = count_stale_markers(content)
            if markers["todo_fixme"] > 0:
                issues.append(f"Has {markers['todo_fixme']} TODO/FIXME marker(s)")
            if markers["stale_references"] > 0:
                issues.append(f"Has {markers['stale_references']} stale reference(s)")

        if issues:
            stale_docs.append({
                "file": rel_path,
                "age_days": int(age_days) if age_days else None,
                "issues": issues,
                "severity": "high" if len(issues) >= 3 else "medium" if len(issues) >= 2 else "low",
            })

    # Sort by severity and age
    severity_order = {"high": 0, "medium": 1, "low": 2}
    stale_docs.sort(key=lambda x: (severity_order.get(x["severity"], 3), -(x["age_days"] or 0)))

    return stale_docs


def generate_stale_report(stale_docs: List[Dict], root: Path) -> str:
    """Generate a human-readable stale content report."""
    lines = [
        "# Stale Content Detection Report",
        "",
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"Repository: {root}",
        f"Potentially stale documents: {len(stale_docs)}",
        "",
    ]

    by_severity = defaultdict(list)
    for doc in stale_docs:
        by_severity[doc["severity"]].append(doc)

    for severity in ("high", "medium", "low"):
        docs = by_severity.get(severity, [])
        if not docs:
            continue

        icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[severity]
        lines.append(f"## {icon} Severity: {severity.upper()} ({len(docs)} documents)")
        lines.append("")

        for doc in docs:
            lines.append(f"### {doc['file']}")
            if doc["age_days"]:
                lines.append(f"- Age: {doc['age_days']} days")
            for issue in doc["issues"]:
                lines.append(f"- {issue}")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Stale content detector for GRC_Claw docs")
    parser.add_argument("--root", type=Path, default=None, help="Repository root")
    parser.add_argument("--age-threshold", type=int, default=180, help="Age threshold in days")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--no-content-check", action="store_true", help="Skip content freshness checks")
    parser.add_argument("--report", type=Path, default=None, help="Write report to file")
    parser.add_argument("--severity", choices=["all", "high", "medium", "low"], default="all")

    args = parser.parse_args()

    root = args.root or REPO_ROOT

    stale_docs = detect_stale_docs(
        root=root,
        age_threshold_days=args.age_threshold,
        check_content=not args.no_content_check,
    )

    # Filter by severity
    if args.severity != "all":
        stale_docs = [d for d in stale_docs if d["severity"] == args.severity]

    if args.json:
        output = {
            "generated": datetime.utcnow().isoformat() + "Z",
            "age_threshold_days": args.age_threshold,
            "total_stale": len(stale_docs),
            "by_severity": {
                "high": sum(1 for d in stale_docs if d["severity"] == "high"),
                "medium": sum(1 for d in stale_docs if d["severity"] == "medium"),
                "low": sum(1 for d in stale_docs if d["severity"] == "low"),
            },
            "documents": stale_docs,
        }
        print(json.dumps(output, indent=2))
    else:
        report = generate_stale_report(stale_docs, root)
        print(report)

    if args.report:
        report = generate_stale_report(stale_docs, root)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report, encoding="utf-8")
        print(f"\nReport written to: {args.report}")

    # Exit with error code if high-severity stale docs found
    high_count = sum(1 for d in stale_docs if d["severity"] == "high")
    sys.exit(1 if high_count > 0 else 0)


if __name__ == "__main__":
    main()
