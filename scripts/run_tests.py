#!/usr/bin/env python3
"""
GRC_Claw Unified Test Runner

Discovers and runs all tests across the monorepo:
  - Python tests (pytest) in deployment/, implementations/, sdk/
  - Node.js tests (node --test) in packages/
  - Shell-based tests in scripts/
  - Spec validation tests

Usage:
    python scripts/run_tests.py                  # Run all tests
    python scripts/run_tests.py --python        # Python tests only
    python scripts/run_tests.py --node          # Node.js tests only
    python scripts/run_tests.py --shell         # Shell tests only
    python scripts/run_tests.py --spec          # Spec validation only
    python scripts/run_tests.py --integration   # Include integration tests
    python scripts/run_tests.py --verbose       # Verbose output
    python scripts/run_tests.py --fail-fast     # Stop on first failure
    python scripts/run_tests.py --parallel      # Run suites in parallel
    python scripts/run_tests.py --coverage      # Generate coverage report
    python scripts/run_tests.py --report        # Generate JSON test report
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"


class TestStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"


@dataclass
class TestResult:
    """Result of a single test suite run."""

    suite: str
    status: TestStatus
    duration: float
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    tests_skipped: int = 0
    output: str = ""
    error: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class TestReport:
    """Aggregated test report."""

    results: list[TestResult] = field(default_factory=list)
    total_duration: float = 0.0
    total_tests: int = 0
    total_passed: int = 0
    total_failed: int = 0
    total_skipped: int = 0
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def add_result(self, result: TestResult) -> None:
        self.results.append(result)
        self.total_duration += result.duration
        self.total_tests += result.tests_run
        self.total_passed += result.tests_passed
        self.total_failed += result.tests_failed
        self.total_skipped += result.tests_skipped

    @property
    def success(self) -> bool:
        return all(
            r.status in (TestStatus.PASS, TestStatus.SKIP) for r in self.results
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "total_duration_seconds": round(self.total_duration, 2),
            "total_tests": self.total_tests,
            "total_passed": self.total_passed,
            "total_failed": self.total_failed,
            "total_skipped": self.total_skipped,
            "success": self.success,
            "suites": [
                {
                    "suite": r.suite,
                    "status": r.status.value,
                    "duration_seconds": round(r.duration, 2),
                    "tests_run": r.tests_run,
                    "tests_passed": r.tests_passed,
                    "tests_failed": r.tests_failed,
                    "tests_skipped": r.tests_skipped,
                    "error": r.error,
                }
                for r in self.results
            ],
        }


# ---------------------------------------------------------------------------
# Test Suite Runners
# ---------------------------------------------------------------------------


def run_command(
    cmd: list[str],
    cwd: Path,
    timeout: int = 300,
    env: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    """Run a command and return (exit_code, stdout, stderr)."""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=full_env,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired as e:
        return -1, e.stdout or "", f"Command timed out after {timeout}s"
    except Exception as e:
        return -2, "", str(e)


def parse_pytest_output(stdout: str, stderr: str) -> tuple[int, int, int, int]:
    """Parse pytest output to extract test counts."""
    import re

    tests_run = 0
    tests_passed = 0
    tests_failed = 0
    tests_skipped = 0

    # Match patterns like "42 passed, 3 failed, 5 skipped in 12.34s"
    pattern = r"(\d+) passed"
    match = re.search(pattern, stdout + stderr)
    if match:
        tests_passed = int(match.group(1))

    pattern = r"(\d+) failed"
    match = re.search(pattern, stdout + stderr)
    if match:
        tests_failed = int(match.group(1))

    pattern = r"(\d+) skipped"
    match = re.search(pattern, stdout + stderr)
    if match:
        tests_skipped = int(match.group(1))

    pattern = r"(\d+) error"
    match = re.search(pattern, stdout + stderr)
    if match:
        tests_failed += int(match.group(1))

    tests_run = tests_passed + tests_failed + tests_skipped
    return tests_run, tests_passed, tests_failed, tests_skipped


def run_python_tests(
    test_dir: Path,
    verbose: bool = False,
    fail_fast: bool = False,
    include_integration: bool = False,
    coverage: bool = False,
) -> TestResult:
    """Run pytest in a given directory."""
    suite_name = f"python:{test_dir.relative_to(REPO_ROOT)}"
    if not test_dir.exists():
        return TestResult(
            suite=suite_name,
            status=TestStatus.SKIP,
            duration=0.0,
            error=f"Directory not found: {test_dir}",
        )

    cmd = [sys.executable, "-m", "pytest"]
    if verbose:
        cmd.append("-v")
    if fail_fast:
        cmd.append("-x")
    if not include_integration:
        cmd.extend(["-m", "not integration"])
    if coverage:
        cmd.extend(["--cov", "--cov-report=term-missing"])
    cmd.append(str(test_dir))

    start = time.time()
    exit_code, stdout, stderr = run_command(cmd, cwd=REPO_ROOT, timeout=600)
    duration = time.time() - start

    tests_run, tests_passed, tests_failed, tests_skipped = parse_pytest_output(
        stdout, stderr
    )

    if exit_code == 0:
        status = TestStatus.PASS
    elif exit_code == 5:  # pytest: no tests collected
        status = TestStatus.SKIP
    else:
        status = TestStatus.FAIL

    return TestResult(
        suite=suite_name,
        status=status,
        duration=duration,
        tests_run=tests_run,
        tests_passed=tests_passed,
        tests_failed=tests_failed,
        tests_skipped=tests_skipped,
        output=stdout[-2000:] if len(stdout) > 2000 else stdout,
        error=stderr[-1000:] if len(stderr) > 1000 else stderr,
    )


def run_node_tests(
    package_dir: Path,
    verbose: bool = False,
    fail_fast: bool = False,
) -> TestResult:
    """Run Node.js tests in a given package directory."""
    suite_name = f"node:{package_dir.relative_to(REPO_ROOT)}"
    if not package_dir.exists():
        return TestResult(
            suite=suite_name,
            status=TestStatus.SKIP,
            duration=0.0,
            error=f"Directory not found: {package_dir}",
        )

    # Check for package.json with test script
    pkg_json = package_dir / "package.json"
    if not pkg_json.exists():
        return TestResult(
            suite=suite_name,
            status=TestStatus.SKIP,
            duration=0.0,
            error="No package.json found",
        )

    cmd = ["node", "--import", "tsx", "--test", "src/**/*.test.ts"]
    if verbose:
        cmd.append("--test-reporter=spec")

    start = time.time()
    exit_code, stdout, stderr = run_command(cmd, cwd=package_dir, timeout=300)
    duration = time.time() - start

    # Parse node test output
    import re

    tests_run = 0
    tests_passed = 0
    tests_failed = 0

    pass_match = re.search(r"# pass (\d+)", stdout)
    fail_match = re.search(r"# fail (\d+)", stdout)
    if pass_match:
        tests_passed = int(pass_match.group(1))
    if fail_match:
        tests_failed = int(fail_match.group(1))
    tests_run = tests_passed + tests_failed

    if exit_code == 0:
        status = TestStatus.PASS
    else:
        status = TestStatus.FAIL

    return TestResult(
        suite=suite_name,
        status=status,
        duration=duration,
        tests_run=tests_run,
        tests_passed=tests_passed,
        tests_failed=tests_failed,
        output=stdout[-2000:] if len(stdout) > 2000 else stdout,
        error=stderr[-1000:] if len(stderr) > 1000 else stderr,
    )


def run_shell_tests(
    script_path: Path,
    verbose: bool = False,
) -> TestResult:
    """Run a shell-based test script."""
    suite_name = f"shell:{script_path.name}"
    if not script_path.exists():
        return TestResult(
            suite=suite_name,
            status=TestStatus.SKIP,
            duration=0.0,
            error=f"Script not found: {script_path}",
        )

    cmd = ["bash", str(script_path)]
    start = time.time()
    exit_code, stdout, stderr = run_command(cmd, cwd=REPO_ROOT, timeout=300)
    duration = time.time() - start

    # Count assertions from output
    import re

    pass_match = re.search(r"pass=(\d+)", stdout)
    fail_match = re.search(r"fail=(\d+)", stdout)
    tests_passed = int(pass_match.group(1)) if pass_match else 0
    tests_failed = int(fail_match.group(1)) if fail_match else 0
    tests_run = tests_passed + tests_failed

    if exit_code == 0:
        status = TestStatus.PASS
    else:
        status = TestStatus.FAIL

    return TestResult(
        suite=suite_name,
        status=status,
        duration=duration,
        tests_run=tests_run,
        tests_passed=tests_passed,
        tests_failed=tests_failed,
        output=stdout[-2000:] if len(stdout) > 2000 else stdout,
        error=stderr[-1000:] if len(stderr) > 1000 else stderr,
    )


def run_spec_validation(
    verbose: bool = False,
) -> TestResult:
    """Run spec validation tests."""
    suite_name = "spec:validation"
    cmd = [sys.executable, "-m", "pytest", str(SCRIPTS_DIR / "test_spec_validation.py")]
    if verbose:
        cmd.append("-v")

    start = time.time()
    exit_code, stdout, stderr = run_command(cmd, cwd=REPO_ROOT, timeout=120)
    duration = time.time() - start

    tests_run, tests_passed, tests_failed, tests_skipped = parse_pytest_output(
        stdout, stderr
    )

    if exit_code == 0:
        status = TestStatus.PASS
    elif exit_code == 5:
        status = TestStatus.SKIP
    else:
        status = TestStatus.FAIL

    return TestResult(
        suite=suite_name,
        status=status,
        duration=duration,
        tests_run=tests_run,
        tests_passed=tests_passed,
        tests_failed=tests_failed,
        tests_skipped=tests_skipped,
        output=stdout[-2000:] if len(stdout) > 2000 else stdout,
        error=stderr[-1000:] if len(stderr) > 1000 else stderr,
    )


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def discover_python_test_dirs() -> list[Path]:
    """Discover all directories containing Python test files."""
    test_dirs: list[Path] = []
    search_roots = [
        REPO_ROOT / "deployment",
        REPO_ROOT / "implementations",
        REPO_ROOT / "sdk",
        REPO_ROOT / "packages",
    ]
    for root in search_roots:
        if not root.exists():
            continue
        for py_file in root.rglob("test_*.py"):
            test_dir = py_file.parent
            if test_dir not in test_dirs:
                test_dirs.append(test_dir)
    return sorted(test_dirs)


def discover_node_test_packages() -> list[Path]:
    """Discover all Node.js packages with test files."""
    packages_dir = REPO_ROOT / "packages"
    if not packages_dir.exists():
        return []
    test_packages: list[Path] = []
    for pkg_dir in packages_dir.iterdir():
        if not pkg_dir.is_dir():
            continue
        pkg_json = pkg_dir / "package.json"
        if not pkg_json.exists():
            continue
        # Check for test files
        has_tests = any(pkg_dir.rglob("*.test.ts")) or any(
            pkg_dir.rglob("*.test.js")
        )
        if has_tests:
            test_packages.append(pkg_dir)
    return sorted(test_packages)


def discover_shell_tests() -> list[Path]:
    """Discover all shell test scripts."""
    scripts_dir = REPO_ROOT / "scripts"
    if not scripts_dir.exists():
        return []
    return sorted(scripts_dir.glob("test*.sh"))


# ---------------------------------------------------------------------------
# Main Runner
# ---------------------------------------------------------------------------


def run_all_tests(
    python: bool = True,
    node: bool = True,
    shell: bool = True,
    spec: bool = True,
    verbose: bool = False,
    fail_fast: bool = False,
    parallel: bool = False,
    include_integration: bool = False,
    coverage: bool = False,
) -> TestReport:
    """Run all discovered test suites."""
    report = TestReport()
    all_suites: list[tuple[str, Any]] = []

    if python:
        for test_dir in discover_python_test_dirs():
            all_suites.append(("python", test_dir))
    if node:
        for pkg_dir in discover_node_test_packages():
            all_suites.append(("node", pkg_dir))
    if shell:
        for script in discover_shell_tests():
            all_suites.append(("shell", script))
    if spec:
        all_suites.append(("spec", None))

    if parallel and len(all_suites) > 1:
        with ThreadPoolExecutor(max_workers=min(4, len(all_suites))) as executor:
            futures = {}
            for suite_type, target in all_suites:
                if suite_type == "python":
                    future = executor.submit(
                        run_python_tests,
                        target,
                        verbose,
                        fail_fast,
                        include_integration,
                        coverage,
                    )
                elif suite_type == "node":
                    future = executor.submit(
                        run_node_tests, target, verbose, fail_fast
                    )
                elif suite_type == "shell":
                    future = executor.submit(run_shell_tests, target, verbose)
                elif suite_type == "spec":
                    future = executor.submit(run_spec_validation, verbose)
                else:
                    continue
                futures[future] = (suite_type, target)

            for future in as_completed(futures):
                result = future.result()
                report.add_result(result)
                status_icon = "✓" if result.status == TestStatus.PASS else "✗"
                print(
                    f"  {status_icon} {result.suite}: {result.status.value} "
                    f"({result.tests_passed}/{result.tests_run} passed, "
                    f"{result.duration:.1f}s)"
                )
                if fail_fast and result.status == TestStatus.FAIL:
                    break
    else:
        for suite_type, target in all_suites:
            if suite_type == "python":
                result = run_python_tests(
                    target, verbose, fail_fast, include_integration, coverage
                )
            elif suite_type == "node":
                result = run_node_tests(target, verbose, fail_fast)
            elif suite_type == "shell":
                result = run_shell_tests(target, verbose)
            elif suite_type == "spec":
                result = run_spec_validation(verbose)
            else:
                continue

            report.add_result(result)
            status_icon = "✓" if result.status == TestStatus.PASS else "✗"
            print(
                f"  {status_icon} {result.suite}: {result.status.value} "
                f"({result.tests_passed}/{result.tests_run} passed, "
                f"{result.duration:.1f}s)"
            )
            if fail_fast and result.status == TestStatus.FAIL:
                break

    return report


def print_summary(report: TestReport) -> None:
    """Print a formatted summary of the test report."""
    print("\n" + "=" * 70)
    print("  GRC_Claw Test Summary")
    print("=" * 70)
    print(f"  Total suites:  {len(report.results)}")
    print(f"  Total tests:   {report.total_tests}")
    print(f"  Passed:        {report.total_passed}")
    print(f"  Failed:        {report.total_failed}")
    print(f"  Skipped:       {report.total_skipped}")
    print(f"  Duration:      {report.total_duration:.1f}s")
    print(f"  Result:        {'✓ PASS' if report.success else '✗ FAIL'}")
    print("=" * 70)

    # Print failed suites
    failed = [r for r in report.results if r.status == TestStatus.FAIL]
    if failed:
        print("\n  Failed Suites:")
        for r in failed:
            print(f"    ✗ {r.suite}")
            if r.error:
                for line in r.error.strip().split("\n")[-5:]:
                    print(f"      {line}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="GRC_Claw Unified Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--python", action="store_true", help="Run Python tests only"
    )
    parser.add_argument("--node", action="store_true", help="Run Node.js tests only")
    parser.add_argument("--shell", action="store_true", help="Run shell tests only")
    parser.add_argument(
        "--spec", action="store_true", help="Run spec validation only"
    )
    parser.add_argument(
        "--integration", action="store_true", help="Include integration tests"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )
    parser.add_argument(
        "--fail-fast", action="store_true", help="Stop on first failure"
    )
    parser.add_argument(
        "--parallel", action="store_true", help="Run suites in parallel"
    )
    parser.add_argument(
        "--coverage", action="store_true", help="Generate coverage report"
    )
    parser.add_argument(
        "--report", type=str, help="Write JSON test report to file"
    )
    parser.add_argument(
        "--timeout", type=int, default=300, help="Per-suite timeout in seconds"
    )

    args = parser.parse_args()

    # If no specific suite selected, run all
    run_all = not any([args.python, args.node, args.shell, args.spec])

    print("=" * 70)
    print("  GRC_Claw Unified Test Runner")
    print("=" * 70)
    print(f"  Repo:    {REPO_ROOT}")
    print(f"  Time:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Mode:    {'all' if run_all else 'selected'}")
    print("=" * 70)
    print()

    report = run_all_tests(
        python=run_all or args.python,
        node=run_all or args.node,
        shell=run_all or args.shell,
        spec=run_all or args.spec,
        verbose=args.verbose,
        fail_fast=args.fail_fast,
        parallel=args.parallel,
        include_integration=args.integration,
        coverage=args.coverage,
    )

    print_summary(report)

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report.to_dict(), indent=2), encoding="utf-8"
        )
        print(f"  Report written to: {report_path}")

    return 0 if report.success else 1


if __name__ == "__main__":
    sys.exit(main())
