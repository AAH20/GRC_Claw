#!/usr/bin/env bash
# test.sh — Run pytest with coverage reporting.
#
# Usage:
#   ./scripts/test.sh [--cov-fail-under N] [--markers MARKER] [--verbose]
#
# Options:
#   --cov-fail-under N  Fail if coverage is below N percent (default: 80).
#   --markers MARKER    Run only tests matching the given pytest marker.
#   --verbose           Enable verbose pytest output.
#   --no-cov            Disable coverage reporting.
#
# Exit codes:
#   0  All tests passed.
#   1  One or more tests failed or coverage threshold not met.

set -euo pipefail

# ── Colors for output ────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ── Logging helpers ─────────────────────────────────────────────────────────
log_info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }
log_success() { echo -e "${GREEN}[OK]${NC}   $*"; }

# ── Argument parsing ────────────────────────────────────────────────────────
COV_FAIL_UNDER=80
MARKER=""
VERBOSE=false
NO_COV=false

for arg in "$@"; do
    case "$arg" in
        --cov-fail-under)
            shift
            COV_FAIL_UNDER="${1:-80}"
            ;;
        --markers)
            shift
            MARKER="${1:-}"
            ;;
        --verbose|-v)
            VERBOSE=true
            ;;
        --no-cov)
            NO_COV=true
            ;;
        -h|--help)
            grep '^#' "$0" | head -n 10 | sed 's/^# //'
            exit 0
            ;;
        *)
            log_error "Unknown option: $arg"
            exit 1
            ;;
    esac
done

# ── Determine project root ──────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$PROJECT_ROOT"

# ── Check dependencies ──────────────────────────────────────────────────────
check_dependency() {
    local cmd="$1"
    if ! command -v "$cmd" &>/dev/null; then
        log_error "'$cmd' is not installed. Install it with: pip install $cmd"
        exit 1
    fi
}

log_info "Checking dependencies..."
check_dependency pytest

# ── Build pytest arguments ──────────────────────────────────────────────────
PYTEST_ARGS=(
    "--tb=short"
    "--strict-markers"
    "--strict-config"
    "-ra"
)

if [[ "$VERBOSE" == true ]]; then
    PYTEST_ARGS+=("-vv")
else
    PYTEST_ARGS+=("-v")
fi

if [[ -n "$MARKER" ]]; then
    PYTEST_ARGS+=("-m" "$MARKER")
    log_info "Running only tests matching marker: $MARKER"
fi

# ── Coverage configuration ──────────────────────────────────────────────────
if [[ "$NO_COV" == false ]]; then
    # Determine source directory
    SOURCE_DIR="."
    if [[ -d "src" ]]; then
        SOURCE_DIR="src"
    fi

    PYTEST_ARGS+=(
        "--cov=${SOURCE_DIR}"
        "--cov-report=term-missing"
        "--cov-report=xml:coverage.xml"
        "--cov-report=html:htmlcov"
        "--cov-branch"
        "--cov-fail-under=${COV_FAIL_UNDER}"
    )
    log_info "Coverage enabled (threshold: ${COV_FAIL_UNDER}%)"
else
    log_warn "Coverage disabled."
fi

# ── JUnit XML report ────────────────────────────────────────────────────────
PYTEST_ARGS+=("--junitxml=pytest-report.xml")

# ── Run tests ───────────────────────────────────────────────────────────────
log_info "Running pytest..."
echo ""

TEST_EXIT_CODE=0
pytest "${PYTEST_ARGS[@]}" || TEST_EXIT_CODE=$?

echo ""

# ── Coverage summary ────────────────────────────────────────────────────────
if [[ "$NO_COV" == false && "$TEST_EXIT_CODE" -eq 0 ]]; then
    log_info "Coverage report generated:"
    log_info "  - XML: coverage.xml"
    log_info "  - HTML: htmlcov/index.html"
fi

# ── Summary ─────────────────────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════════════════════"
if [[ "$TEST_EXIT_CODE" -eq 0 ]]; then
    log_success "All tests passed!"
    echo "══════════════════════════════════════════════════════════════"
    exit 0
else
    log_error "Tests failed with exit code: $TEST_EXIT_CODE"
    echo "══════════════════════════════════════════════════════════════"
    exit 1
fi
