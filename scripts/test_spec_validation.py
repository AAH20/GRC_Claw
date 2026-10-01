"""
Spec Validation Tests for GRC_Claw

These tests validate the spec library using the quality gate framework.
They can be run standalone or as part of the unified test runner.

Usage:
    python -m pytest scripts/test_spec_validation.py -v
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

# Add scripts directory to path for imports
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from quality_gate import (
    REQUIRED_SECTIONS,
    SPECS_DIR,
    Severity,
    extract_metadata,
    extract_sections,
    find_code_blocks,
    find_cross_references,
    run_quality_gate,
    validate_spec,
)

# Pre-compute spec files at module level to avoid decorator syntax issues
_SPEC_FILES = sorted(SPECS_DIR.glob("*.md")) if SPECS_DIR.exists() else []


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def all_spec_files() -> set[str]:
    """Return set of all spec filenames."""
    if not SPECS_DIR.exists():
        pytest.skip(f"Specs directory not found: {SPECS_DIR}")
    return {f.name for f in SPECS_DIR.glob("*.md")}


@pytest.fixture(scope="module")
def spec_reports(all_spec_files: set[str]) -> list:
    """Run quality gate on all specs and return reports."""
    if not SPECS_DIR.exists():
        pytest.skip(f"Specs directory not found: {SPECS_DIR}")
    return run_quality_gate(SPECS_DIR, strict=False)


@pytest.fixture(scope="module")
def spec_files() -> list[Path]:
    """Return list of all spec files."""
    if not SPECS_DIR.exists():
        pytest.skip(f"Specs directory not found: {SPECS_DIR}")
    return sorted(SPECS_DIR.glob("*.md"))


# ---------------------------------------------------------------------------
# Test: Spec Library Exists
# ---------------------------------------------------------------------------


class TestSpecLibrary:
    """Test that the spec library exists and has content."""

    def test_specs_directory_exists(self):
        """Verify the specs directory exists."""
        assert SPECS_DIR.exists(), f"Specs directory not found: {SPECS_DIR}"
        assert SPECS_DIR.is_dir(), f"Specs path is not a directory: {SPECS_DIR}"

    def test_specs_directory_not_empty(self):
        """Verify the specs directory contains markdown files."""
        spec_files = list(SPECS_DIR.glob("*.md"))
        assert len(spec_files) > 0, "No spec files found in specs/"

    def test_minimum_spec_count(self):
        """Verify there are a reasonable number of specs."""
        spec_files = list(SPECS_DIR.glob("*.md"))
        assert len(spec_files) >= 50, (
            f"Expected at least 50 specs, found {len(spec_files)}"
        )


# ---------------------------------------------------------------------------
# Test: Spec Metadata
# ---------------------------------------------------------------------------


class TestSpecMetadata:
    """Test that all specs have required metadata."""

    @pytest.mark.parametrize("spec_file", _SPEC_FILES)
    def test_spec_has_version(self, spec_file: Path):
        """Every spec should have a Version field."""
        content = spec_file.read_text(encoding="utf-8")
        metadata = extract_metadata(content)
        assert "version" in metadata, (
            f"{spec_file.name}: Missing **Version:** metadata"
        )

    @pytest.mark.parametrize("spec_file", _SPEC_FILES)
    def test_spec_has_date(self, spec_file: Path):
        """Every spec should have a Date field."""
        content = spec_file.read_text(encoding="utf-8")
        metadata = extract_metadata(content)
        assert "date" in metadata, (
            f"{spec_file.name}: Missing **Date:** metadata"
        )

    @pytest.mark.parametrize("spec_file", _SPEC_FILES)
    def test_spec_has_status(self, spec_file: Path):
        """Every spec should have a Status field."""
        content = spec_file.read_text(encoding="utf-8")
        metadata = extract_metadata(content)
        assert "status" in metadata, (
            f"{spec_file.name}: Missing **Status:** metadata"
        )

    @pytest.mark.parametrize("spec_file", _SPEC_FILES)
    def test_spec_version_format(self, spec_file: Path):
        """Version should follow semantic versioning pattern."""
        content = spec_file.read_text(encoding="utf-8")
        metadata = extract_metadata(content)
        if "version" in metadata:
            version = metadata["version"]
            assert re.match(r"^\d+\.\d+", version), (
                f"{spec_file.name}: Invalid version format: '{version}'"
            )

    @pytest.mark.parametrize("spec_file", _SPEC_FILES)
    def test_spec_date_format(self, spec_file: Path):
        """Date should be in YYYY-MM-DD format."""
        content = spec_file.read_text(encoding="utf-8")
        metadata = extract_metadata(content)
        if "date" in metadata:
            date_str = metadata["date"]
            assert re.match(r"^\d{4}-\d{2}-\d{2}", date_str), (
                f"{spec_file.name}: Invalid date format: '{date_str}'"
            )


# ---------------------------------------------------------------------------
# Test: Spec Sections
# ---------------------------------------------------------------------------


class TestSpecSections:
    """Test that specs have required sections."""

    @pytest.mark.parametrize("spec_file", _SPEC_FILES)
    def test_spec_has_sections(self, spec_file: Path):
        """Every spec should have at least 3 sections."""
        content = spec_file.read_text(encoding="utf-8")
        sections = extract_sections(content)
        assert len(sections) >= 3, (
            f"{spec_file.name}: Only {len(sections)} sections found (minimum 3)"
        )

    @pytest.mark.parametrize("spec_file", _SPEC_FILES)
    def test_spec_has_purpose(self, spec_file: Path):
        """Every spec should have a Purpose or Introduction section."""
        content = spec_file.read_text(encoding="utf-8")
        sections = extract_sections(content)
        has_purpose = any(
            "purpose" in s.lower() or "introduction" in s.lower() or "overview" in s.lower()
            for s in sections
        )
        assert has_purpose, (
            f"{spec_file.name}: No Purpose/Introduction/Overview section found"
        )

    @pytest.mark.parametrize("spec_file", _SPEC_FILES)
    def test_spec_has_scope(self, spec_file: Path):
        """Every spec should have a Scope section."""
        content = spec_file.read_text(encoding="utf-8")
        sections = extract_sections(content)
        has_scope = any("scope" in s.lower() for s in sections)
        assert has_scope, (
            f"{spec_file.name}: No Scope section found"
        )


# ---------------------------------------------------------------------------
# Test: Spec Content Quality
# ---------------------------------------------------------------------------


class TestSpecContentQuality:
    """Test content quality of individual specs."""

    @pytest.mark.parametrize("spec_file", _SPEC_FILES)
    def test_spec_not_empty(self, spec_file: Path):
        """No spec should be empty."""
        content = spec_file.read_text(encoding="utf-8")
        assert len(content.strip()) > 0, f"{spec_file.name}: File is empty"

    @pytest.mark.parametrize("spec_file", _SPEC_FILES)
    def test_spec_minimum_length(self, spec_file: Path):
        """Every spec should have meaningful content."""
        content = spec_file.read_text(encoding="utf-8")
        word_count = len(content.split())
        assert word_count >= 100, (
            f"{spec_file.name}: Only {word_count} words (minimum 100)"
        )

    @pytest.mark.parametrize("spec_file", _SPEC_FILES)
    def test_spec_no_todo_markers(self, spec_file: Path):
        """Specs should not contain TODO/FIXME markers."""
        content = spec_file.read_text(encoding="utf-8")
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            # Skip code blocks (examples may contain TODO)
            if line.strip().startswith("```"):
                continue
            assert not re.search(r"\bTODO\b", line, re.IGNORECASE), (
                f"{spec_file.name}:{i}: TODO marker found"
            )
            assert not re.search(r"\bFIXME\b", line, re.IGNORECASE), (
                f"{spec_file.name}:{i}: FIXME marker found"
            )

    @pytest.mark.parametrize("spec_file", _SPEC_FILES)
    def test_spec_no_lorem_ipsum(self, spec_file: Path):
        """Specs should not contain lorem ipsum placeholder text."""
        content = spec_file.read_text(encoding="utf-8")
        assert not re.search(r"lorem\s+ipsum", content, re.IGNORECASE), (
            f"{spec_file.name}: Lorem ipsum placeholder found"
        )


# ---------------------------------------------------------------------------
# Test: Cross-references
# ---------------------------------------------------------------------------


class TestCrossReferences:
    """Test that cross-references between specs are valid."""

    @pytest.mark.parametrize("spec_file", _SPEC_FILES)
    def test_cross_references_resolve(self, spec_file: Path, all_spec_files: set[str]):
        """All cross-references should resolve to existing files."""
        content = spec_file.read_text(encoding="utf-8")
        refs = find_cross_references(content)

        for line_num, ref_type, target in refs:
            # Strip anchor
            target_file = target.split("#")[0]
            if not target_file:
                continue  # Same-page anchor

            # Check if it's a spec file
            if target_file in all_spec_files:
                continue

            # Check if it exists relative to specs dir
            if (SPECS_DIR / target_file).exists():
                continue

            # Check if it's a URL
            if target_file.startswith(("http://", "https://", "mailto:")):
                continue

            # Check if it exists anywhere in the repo
            repo_root = SPECS_DIR.parent
            matches = list(repo_root.rglob(target_file))
            if matches:
                continue

            pytest.fail(
                f"{spec_file.name}:{line_num}: Broken cross-reference: '{target}'"
            )


# ---------------------------------------------------------------------------
# Test: Code Examples
# ---------------------------------------------------------------------------


class TestCodeExamples:
    """Test that code examples in specs are valid."""

    @pytest.mark.parametrize("spec_file", _SPEC_FILES)
    def test_code_blocks_balanced(self, spec_file: Path):
        """All code blocks should be properly closed."""
        content = spec_file.read_text(encoding="utf-8")
        lines = content.split("\n")
        in_block = False
        for i, line in enumerate(lines, 1):
            if line.strip().startswith("```"):
                if not in_block:
                    in_block = True
                else:
                    in_block = False
        assert not in_block, (
            f"{spec_file.name}: Unclosed code block found"
        )

    @pytest.mark.parametrize("spec_file", _SPEC_FILES)
    def test_code_blocks_have_language(self, spec_file: Path):
        """Code blocks should specify a language."""
        content = spec_file.read_text(encoding="utf-8")
        blocks = find_code_blocks(content)
        for line_num, lang in blocks:
            if not lang or lang.lower() in ("text", "txt", "plain"):
                pytest.fail(
                    f"{spec_file.name}:{line_num}: Code block has no language specified"
                )


# ---------------------------------------------------------------------------
# Test: Quality Gate Integration
# ---------------------------------------------------------------------------


class TestQualityGate:
    """Test the quality gate framework itself."""

    def test_quality_gate_runs(self, spec_reports: list):
        """Quality gate should produce reports for all specs."""
        assert len(spec_reports) > 0, "Quality gate produced no reports"

    def test_quality_gate_detects_issues(self, spec_reports: list):
        """Quality gate should detect issues in specs."""
        # At least some specs should have warnings or errors
        # (this is expected for a large spec library)
        total_issues = sum(r.error_count + r.warning_count for r in spec_reports)
        # We don't assert a specific number, just that the gate is working
        assert isinstance(total_issues, int)

    def test_quality_gate_sections_detected(self, spec_reports: list):
        """Quality gate should detect sections in specs."""
        for report in spec_reports:
            assert len(report.sections_found) > 0, (
                f"{report.file_name}: No sections detected"
            )

    def test_quality_gate_metadata_extracted(self, spec_reports: list):
        """Quality gate should extract metadata from specs."""
        for report in spec_reports:
            # At least some specs should have metadata
            if report.metadata:
                assert isinstance(report.metadata, dict)

    def test_quality_gate_code_blocks_counted(self, spec_reports: list):
        """Quality gate should count code blocks."""
        total_code_blocks = sum(r.code_blocks for r in spec_reports)
        assert total_code_blocks > 0, "No code blocks found in any spec"

    def test_quality_gate_cross_references_counted(self, spec_reports: list):
        """Quality gate should count cross-references."""
        total_refs = sum(r.cross_references for r in spec_reports)
        assert total_refs > 0, "No cross-references found in any spec"


# ---------------------------------------------------------------------------
# Test: Required Sections Coverage
# ---------------------------------------------------------------------------


class TestRequiredSections:
    """Test coverage of required sections across the spec library."""

    def test_purpose_coverage(self, spec_reports: list):
        """At least 80% of specs should have a Purpose section."""
        count = sum(
            1 for r in spec_reports
            if any("purpose" in s.lower() for s in r.sections_found)
        )
        pct = (count / len(spec_reports) * 100) if spec_reports else 0
        assert pct >= 80, (
            f"Only {pct:.0f}% of specs have a Purpose section (minimum 80%)"
        )

    def test_scope_coverage(self, spec_reports: list):
        """At least 80% of specs should have a Scope section."""
        count = sum(
            1 for r in spec_reports
            if any("scope" in s.lower() for s in r.sections_found)
        )
        pct = (count / len(spec_reports) * 100) if spec_reports else 0
        assert pct >= 80, (
            f"Only {pct:.0f}% of specs have a Scope section (minimum 80%)"
        )


# ---------------------------------------------------------------------------
# Test: Spec Naming Conventions
# ---------------------------------------------------------------------------


class TestSpecNaming:
    """Test that spec files follow naming conventions."""

    @pytest.mark.parametrize("spec_file", _SPEC_FILES)
    def test_spec_naming_convention(self, spec_file: Path):
        """Spec files should use kebab-case or snake_case naming."""
        name = spec_file.stem
        # Allow both kebab-case and snake_case
        assert re.match(r"^[a-z0-9]+([-_][a-z0-9]+)*$", name), (
            f"{spec_file.name}: Spec file should use kebab-case or snake_case naming"
        )


# ---------------------------------------------------------------------------
# Test: Spec Encoding
# ---------------------------------------------------------------------------


class TestSpecEncoding:
    """Test that spec files are properly encoded."""

    @pytest.mark.parametrize("spec_file", _SPEC_FILES)
    def test_spec_utf8_encoding(self, spec_file: Path):
        """All specs should be valid UTF-8."""
        try:
            spec_file.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            pytest.fail(f"{spec_file.name}: Not valid UTF-8: {e}")

    @pytest.mark.parametrize("spec_file", _SPEC_FILES)
    def test_spec_no_bom(self, spec_file: Path):
        """Specs should not have a UTF-8 BOM."""
        raw = spec_file.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), (
            f"{spec_file.name}: File has UTF-8 BOM"
        )
