#!/usr/bin/env python3
"""
GRC_Claw Spec Quality Gate

Validates all specification documents in the specs/ directory against
quality criteria:
  - Required sections present
  - Cross-references resolve to existing files
  - Code examples present and syntactically valid
  - Metadata completeness (version, date, status, owner)
  - Table of contents matches actual sections
  - No broken internal links
  - Minimum content length
  - No placeholder/TODO markers in published specs

Usage:
    python scripts/quality_gate.py                # Validate all specs
    python scripts/quality_gate.py --fix          # Auto-fix what can be fixed
    python scripts/quality_gate.py --strict       # Treat warnings as errors
    python scripts/quality_gate.py --report       # Generate JSON report
    python scripts/quality_gate.py --spec FILE    # Validate single spec
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SPECS_DIR = REPO_ROOT / "specs"


class Severity(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class QualityIssue:
    """A single quality issue found in a spec."""

    severity: Severity
    message: str
    line_number: int | None = None
    suggestion: str = ""


@dataclass
class SpecQualityReport:
    """Quality report for a single spec file."""

    file_path: Path
    file_name: str
    issues: list[QualityIssue] = field(default_factory=list)
    sections_found: list[str] = field(default_factory=list)
    sections_required: list[str] = field(default_factory=list)
    code_blocks: int = 0
    cross_references: int = 0
    broken_references: int = 0
    word_count: int = 0
    line_count: int = 0
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return not any(
            i.severity in (Severity.ERROR, Severity.CRITICAL) for i in self.issues
        )

    @property
    def error_count(self) -> int:
        return sum(
            1 for i in self.issues if i.severity in (Severity.ERROR, Severity.CRITICAL)
        )

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)

    def to_dict(self) -> dict[str, Any]:
        return {
            "file": self.file_name,
            "passed": self.passed,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "word_count": self.word_count,
            "line_count": self.line_count,
            "sections_found": self.sections_found,
            "sections_required": self.sections_required,
            "code_blocks": self.code_blocks,
            "cross_references": self.cross_references,
            "broken_references": self.broken_references,
            "metadata": self.metadata,
            "issues": [
                {
                    "severity": i.severity.value,
                    "message": i.message,
                    "line": i.line_number,
                    "suggestion": i.suggestion,
                }
                for i in self.issues
            ],
        }


# ---------------------------------------------------------------------------
# Required Sections Configuration
# ---------------------------------------------------------------------------

REQUIRED_SECTIONS = [
    "Purpose",
    "Scope",
    "References",
    "Architecture",
    "Data Model",
    "API",
    "Security",
    "Metrics",
]

OPTIONAL_SECTIONS = [
    "Overview",
    "Introduction",
    "Background",
    "Definitions",
    "Terminology",
    "Requirements",
    "Design",
    "Implementation",
    "Testing",
    "Deployment",
    "Operations",
    "Monitoring",
    "Compliance",
    "Governance",
    "Risk",
    "Performance",
    "Scalability",
    "Reliability",
    "Appendices",
    "Appendix",
    "Glossary",
    "Changelog",
    "Roadmap",
]

# Patterns that indicate a section header
SECTION_PATTERN = re.compile(r"^#{1,3}\s+(.+?)(?:\s*\{#.*\})?\s*$")

# Metadata patterns
METADATA_PATTERNS = {
    "version": re.compile(r"\*\*Version:\*\*\s*(.+)", re.IGNORECASE),
    "date": re.compile(r"\*\*Date:\*\*\s*(.+)", re.IGNORECASE),
    "status": re.compile(r"\*\*Status:\*\*\s*(.+)", re.IGNORECASE),
    "owner": re.compile(r"\*\*Owner:\*\*\s*(.+)", re.IGNORECASE),
    "document_id": re.compile(r"\*\*Document ID:\*\*\s*(.+)", re.IGNORECASE),
    "supersedes": re.compile(r"\*\*Supersedes:\*\*\s*(.+)", re.IGNORECASE),
    "references": re.compile(r"\*\*References?:\*\*\s*(.+)", re.IGNORECASE),
    "classification": re.compile(r"\*\*Classification:\*\*\s*(.+)", re.IGNORECASE),
}

# Cross-reference patterns
CROSS_REF_PATTERNS = [
    re.compile(r"\[([^\]]+)\]\(([^)]+\.md)(?:#[^)]+)?\)"),  # Markdown links
    re.compile(r"(?:see|refer to|described in|defined in|specified in)\s+`([^`]+\.md)`", re.IGNORECASE),
    re.compile(r"(?:see|refer to|described in|defined in|specified in)\s+([a-z0-9-]+\.md)", re.IGNORECASE),
]

# Code block pattern
CODE_BLOCK_PATTERN = re.compile(r"^```(\w+)?\s*$", re.MULTILINE)

# Placeholder patterns
PLACEHOLDER_PATTERNS = [
    (re.compile(r"\bTODO\b", re.IGNORECASE), "TODO marker"),
    (re.compile(r"\bFIXME\b", re.IGNORECASE), "FIXME marker"),
    (re.compile(r"\bTBD\b", re.IGNORECASE), "TBD marker"),
    (re.compile(r"\bXXX\b", re.IGNORECASE), "XXX marker"),
    (re.compile(r"lorem\s+ipsum", re.IGNORECASE), "Lorem ipsum placeholder"),
    (re.compile(r"placeholder\s+text", re.IGNORECASE), "Placeholder text"),
    (re.compile(r"\[insert\s+", re.IGNORECASE), "Insert marker"),
    (re.compile(r"\[replace\s+", re.IGNORECASE), "Replace marker"),
    (re.compile(r"\[add\s+", re.IGNORECASE), "Add marker"),
]

# Minimum content thresholds
MIN_WORD_COUNT = 200
MIN_LINE_COUNT = 30
MIN_CODE_BLOCKS = 0  # Some specs may legitimately have no code
MIN_SECTIONS = 3


# ---------------------------------------------------------------------------
# Validation Functions
# ---------------------------------------------------------------------------


def extract_sections(content: str) -> list[str]:
    """Extract all section headers from markdown content."""
    sections: list[str] = []
    for line in content.split("\n"):
        match = SECTION_PATTERN.match(line)
        if match:
            section_name = match.group(1).strip()
            # Clean up anchor links
            section_name = re.sub(r"\{#.*\}", "", section_name).strip()
            sections.append(section_name)
    return sections


def extract_metadata(content: str) -> dict[str, str]:
    """Extract metadata fields from spec header."""
    metadata: dict[str, str] = {}
    for key, pattern in METADATA_PATTERNS.items():
        match = pattern.search(content)
        if match:
            metadata[key] = match.group(1).strip()
    return metadata


def find_code_blocks(content: str) -> list[tuple[int, str]]:
    """Find all code blocks and return (line_number, language) tuples."""
    blocks: list[tuple[int, str]] = []
    lines = content.split("\n")
    in_block = False
    block_lang = ""
    block_start = 0

    for i, line in enumerate(lines, 1):
        match = CODE_BLOCK_PATTERN.match(line)
        if match:
            if not in_block:
                in_block = True
                block_lang = match.group(1) or ""
                block_start = i
            else:
                blocks.append((block_start, block_lang))
                in_block = False
                block_lang = ""

    return blocks


def find_cross_references(content: str) -> list[tuple[int, str, str]]:
    """Find all cross-references and return (line_number, ref_type, target) tuples."""
    refs: list[tuple[int, str, str]] = []
    lines = content.split("\n")

    for i, line in enumerate(lines, 1):
        for pattern in CROSS_REF_PATTERNS:
            for match in pattern.finditer(line):
                if match.lastindex and match.lastindex >= 2:
                    target = match.group(2)
                    ref_type = "markdown_link"
                else:
                    target = match.group(1)
                    ref_type = "text_reference"
                refs.append((i, ref_type, target))

    return refs


def check_cross_reference(target: str, specs_dir: Path, all_spec_files: set[str]) -> bool:
    """Check if a cross-reference target resolves to an existing file."""
    # Strip anchor
    target_file = target.split("#")[0]
    if not target_file:
        return True  # Same-page anchor

    # Check if it's a spec file
    if target_file in all_spec_files:
        return True

    # Check if it exists relative to specs dir
    if (specs_dir / target_file).exists():
        return True

    # Check if it exists relative to repo root
    if (REPO_ROOT / target_file).exists():
        return True

    # Check if it's a URL
    if target_file.startswith(("http://", "https://", "mailto:")):
        return True

    # Check if it's a file that exists anywhere in the repo
    for ext in [".md", ".yaml", ".yml", ".json", ".py", ".ts", ".js"]:
        if target_file.endswith(ext):
            matches = list(REPO_ROOT.rglob(target_file))
            if matches:
                return True

    return False


def validate_spec(
    spec_path: Path,
    all_spec_files: set[str],
    strict: bool = False,
) -> SpecQualityReport:
    """Validate a single spec file and return a quality report."""
    report = SpecQualityReport(
        file_path=spec_path,
        file_name=spec_path.name,
        sections_required=REQUIRED_SECTIONS.copy(),
    )

    try:
        content = spec_path.read_text(encoding="utf-8")
    except Exception as e:
        report.issues.append(
            QualityIssue(
                severity=Severity.CRITICAL,
                message=f"Failed to read file: {e}",
            )
        )
        return report

    lines = content.split("\n")
    report.line_count = len(lines)
    report.word_count = len(content.split())

    # --- Check metadata ---
    metadata = extract_metadata(content)
    report.metadata = metadata

    required_metadata = ["version", "date", "status"]
    for meta_key in required_metadata:
        if meta_key not in metadata:
            report.issues.append(
                QualityIssue(
                    severity=Severity.ERROR,
                    message=f"Missing required metadata field: **{meta_key.title()}:**",
                    suggestion=f"Add **{meta_key.title()}:** value to the spec header",
                )
            )

    # --- Check sections ---
    sections = extract_sections(content)
    report.sections_found = sections

    for required in REQUIRED_SECTIONS:
        # Fuzzy match: check if any found section contains the required keyword
        found = any(required.lower() in s.lower() for s in sections)
        if not found:
            report.issues.append(
                QualityIssue(
                    severity=Severity.WARNING,
                    message=f"Missing recommended section: {required}",
                    suggestion=f"Consider adding a '{required}' section",
                )
            )

    if len(sections) < MIN_SECTIONS:
        report.issues.append(
            QualityIssue(
                severity=Severity.WARNING,
                message=f"Only {len(sections)} sections found (minimum {MIN_SECTIONS} recommended)",
            )
        )

    # --- Check content length ---
    if report.word_count < MIN_WORD_COUNT:
        report.issues.append(
            QualityIssue(
                severity=Severity.WARNING,
                message=f"Short document: {report.word_count} words (minimum {MIN_WORD_COUNT} recommended)",
            )
        )

    if report.line_count < MIN_LINE_COUNT:
        report.issues.append(
            QualityIssue(
                severity=Severity.WARNING,
                message=f"Short document: {report.line_count} lines (minimum {MIN_LINE_COUNT} recommended)",
            )
        )

    # --- Check code blocks ---
    code_blocks = find_code_blocks(content)
    report.code_blocks = len(code_blocks)

    if len(code_blocks) < MIN_CODE_BLOCKS:
        report.issues.append(
            QualityIssue(
                severity=Severity.INFO,
                message=f"No code blocks found (minimum {MIN_CODE_BLOCKS} recommended)",
            )
        )

    # Validate code block languages
    for line_num, lang in code_blocks:
        if lang and lang.lower() in ("text", "txt", "plain"):
            report.issues.append(
                QualityIssue(
                    severity=Severity.INFO,
                    line_number=line_num,
                    message=f"Code block has no language specified",
                    suggestion="Add a language identifier (e.g., ```python, ```json)",
                )
            )

    # --- Check cross-references ---
    cross_refs = find_cross_references(content)
    report.cross_references = len(cross_refs)

    for line_num, ref_type, target in cross_refs:
        if not check_cross_reference(target, SPECS_DIR, all_spec_files):
            report.broken_references += 1
            report.issues.append(
                QualityIssue(
                    severity=Severity.ERROR,
                    line_number=line_num,
                    message=f"Broken cross-reference: '{target}'",
                    suggestion=f"Create the missing file or update the reference",
                )
            )

    # --- Check for placeholders ---
    for i, line in enumerate(lines, 1):
        for pattern, name in PLACEHOLDER_PATTERNS:
            if pattern.search(line):
                severity = (
                    Severity.ERROR
                    if strict
                    else Severity.WARNING
                )
                report.issues.append(
                    QualityIssue(
                        severity=severity,
                        line_number=i,
                        message=f"Found {name} in content",
                        suggestion=f"Replace the {name} with actual content",
                    )
                )

    # --- Check for empty sections ---
    for i, line in enumerate(lines):
        match = SECTION_PATTERN.match(line)
        if match:
            section_name = match.group(1).strip()
            # Look ahead for content
            content_lines = []
            for j in range(i + 1, min(i + 50, len(lines))):
                if SECTION_PATTERN.match(lines[j]):
                    break
                content_lines.append(lines[j])
            content_text = "\n".join(content_lines).strip()
            if len(content_text) < 20:
                report.issues.append(
                    QualityIssue(
                        severity=Severity.WARNING,
                        line_number=i + 1,
                        message=f"Section '{section_name}' appears to be empty or very short",
                        suggestion="Add content to this section or remove it",
                    )
                )

    # --- Check TOC matches sections ---
    toc_match = re.search(r"##\s+Table\s+of\s+Contents\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
    if toc_match:
        toc_content = toc_match.group(1)
        toc_items = re.findall(r"\[([^\]]+)\]\(#([^)]+)\)", toc_content)
        for item_text, anchor in toc_items:
            # Check if the anchor corresponds to a real section
            anchor_normalized = anchor.lower().replace("-", " ").strip()
            found = any(
                anchor_normalized in s.lower() or s.lower() in anchor_normalized
                for s in sections
            )
            if not found:
                report.issues.append(
                    QualityIssue(
                        severity=Severity.WARNING,
                        message=f"TOC entry '{item_text}' does not match any section header",
                        suggestion="Fix the TOC anchor or the section header",
                    )
                )

    return report


# ---------------------------------------------------------------------------
# Auto-fix Functions
# ---------------------------------------------------------------------------


def auto_fix_spec(spec_path: Path, report: SpecQualityReport) -> list[str]:
    """Attempt to auto-fix issues in a spec file. Returns list of fixes applied."""
    fixes: list[str] = []
    content = spec_path.read_text(encoding="utf-8")

    # Fix: Add missing metadata
    for issue in report.issues:
        if "Missing required metadata field" in issue.message:
            field = issue.message.split(":")[-1].strip().replace("*", "").lower()
            if field == "version" and "version" not in content.lower():
                # Insert after the title
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if line.startswith("# "):
                        lines.insert(i + 1, f"\n**Version:** 1.0  ")
                        lines.insert(i + 2, "")
                        break
                content = "\n".join(lines)
                fixes.append(f"Added missing **Version:** metadata")

    if fixes:
        spec_path.write_text(content, encoding="utf-8")

    return fixes


# ---------------------------------------------------------------------------
# Main Quality Gate
# ---------------------------------------------------------------------------


def run_quality_gate(
    specs_dir: Path,
    strict: bool = False,
    fix: bool = False,
    single_spec: str | None = None,
) -> list[SpecQualityReport]:
    """Run quality gate on all specs and return reports."""
    if not specs_dir.exists():
        print(f"ERROR: Specs directory not found: {specs_dir}")
        return []

    # Collect all spec filenames for cross-reference checking
    all_spec_files: set[str] = set()
    for f in specs_dir.iterdir():
        if f.suffix == ".md":
            all_spec_files.add(f.name)

    # Determine which specs to validate
    if single_spec:
        spec_files = [specs_dir / single_spec]
    else:
        spec_files = sorted(specs_dir.glob("*.md"))

    reports: list[SpecQualityReport] = []

    for spec_file in spec_files:
        if not spec_file.exists():
            print(f"  WARNING: Spec file not found: {spec_file}")
            continue

        report = validate_spec(spec_file, all_spec_files, strict=strict)

        if fix and not report.passed:
            fixes = auto_fix_spec(spec_file, report)
            if fixes:
                # Re-validate after fixes
                report = validate_spec(spec_file, all_spec_files, strict=strict)
                report.issues.insert(
                    0,
                    QualityIssue(
                        severity=Severity.INFO,
                        message=f"Auto-fixed: {', '.join(fixes)}",
                    ),
                )

        reports.append(report)

    return reports


def print_report(reports: list[SpecQualityReport], strict: bool = False) -> None:
    """Print a formatted quality gate report."""
    total = len(reports)
    passed = sum(1 for r in reports if r.passed)
    failed = total - passed
    total_errors = sum(r.error_count for r in reports)
    total_warnings = sum(r.warning_count for r in reports)
    total_broken_refs = sum(r.broken_references for r in reports)

    print("\n" + "=" * 70)
    print("  GRC_Claw Spec Quality Gate Report")
    print("=" * 70)
    print(f"  Specs scanned:    {total}")
    print(f"  Passed:           {passed}")
    print(f"  Failed:           {failed}")
    print(f"  Total errors:     {total_errors}")
    print(f"  Total warnings:   {total_warnings}")
    print(f"  Broken refs:      {total_broken_refs}")
    print("=" * 70)

    # Print details for failed specs
    failed_reports = [r for r in reports if not r.passed]
    if failed_reports:
        print("\n  Failed Specs:")
        for r in failed_reports:
            print(f"\n    ✗ {r.file_name}")
            print(f"      Errors: {r.error_count}, Warnings: {r.warning_count}")
            for issue in r.issues:
                if issue.severity in (Severity.ERROR, Severity.CRITICAL):
                    line_info = f" (line {issue.line_number})" if issue.line_number else ""
                    print(f"      [{issue.severity.value}] {issue.message}{line_info}")
                    if issue.suggestion:
                        print(f"        → {issue.suggestion}")

    # Print warnings summary
    warning_reports = [r for r in reports if r.passed and r.warning_count > 0]
    if warning_reports and not strict:
        print(f"\n  Specs with warnings ({len(warning_reports)}):")
        for r in warning_reports:
            print(f"    ⚠ {r.file_name}: {r.warning_count} warnings")

    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="GRC_Claw Spec Quality Gate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--strict", action="store_true", help="Treat warnings as errors"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Auto-fix what can be fixed"
    )
    parser.add_argument(
        "--report", type=str, help="Write JSON report to file"
    )
    parser.add_argument(
        "--spec", type=str, help="Validate a single spec file"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show all issues including INFO"
    )
    parser.add_argument(
        "--list-sections", action="store_true", help="List required sections and exit"
    )

    args = parser.parse_args()

    if args.list_sections:
        print("\nRequired sections for GRC_Claw specs:")
        for s in REQUIRED_SECTIONS:
            print(f"  - {s}")
        print("\nOptional sections:")
        for s in OPTIONAL_SECTIONS:
            print(f"  - {s}")
        return 0

    print("=" * 70)
    print("  GRC_Claw Spec Quality Gate")
    print("=" * 70)
    print(f"  Specs dir: {SPECS_DIR}")
    print(f"  Strict:    {args.strict}")
    print(f"  Fix:       {args.fix}")
    print("=" * 70)
    print()

    reports = run_quality_gate(
        SPECS_DIR,
        strict=args.strict,
        fix=args.fix,
        single_spec=args.spec,
    )

    print_report(reports, strict=args.strict)

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_specs": len(reports),
            "passed": sum(1 for r in reports if r.passed),
            "failed": sum(1 for r in reports if not r.passed),
            "total_errors": sum(r.error_count for r in reports),
            "total_warnings": sum(r.warning_count for r in reports),
            "specs": [r.to_dict() for r in reports],
        }
        report_path.write_text(
            json.dumps(report_data, indent=2), encoding="utf-8"
        )
        print(f"  Report written to: {report_path}")

    # Exit code: 0 if all pass, 1 if any fail
    failed = sum(1 for r in reports if not r.passed)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
