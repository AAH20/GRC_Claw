#!/usr/bin/env bash
# security-scan.sh — Run bandit and safety security scans.
#
# Usage:
#   ./scripts/security-scan.sh [--severity-level LEVEL] [--confidence-level LEVEL]
#
# Options:
#   --severity-level LEVEL    Minimum severity to report: low, medium, high (default: low).
#   --confidence-level LEVEL  Minimum confidence to report: low, medium, high (default: low).
#   --fail-on-issue           Exit with error code if any issues are found.
#   --skip-safety             Skip the safety dependency check.
#   --skip-bandit             Skip the bandit static analysis.
#
# Exit codes:
#   0  No critical issues found (or issues below threshold).
#   1  Security issues detected or scan failed.

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
SEVERITY_LEVEL="low"
CONFIDENCE_LEVEL="low"
FAIL_ON_ISSUE=false
SKIP_SAFETY=false
SKIP_BANDIT=false

for arg in "$@"; do
    case "$arg" in
        --severity-level)
            shift
            SEVERITY_LEVEL="${1:-low}"
            ;;
        --confidence-level)
            shift
            CONFIDENCE_LEVEL="${1:-low}"
            ;;
        --fail-on-issue)
            FAIL_ON_ISSUE=true
            ;;
        --skip-safety)
            SKIP_SAFETY=true
            ;;
        --skip-bandit)
            SKIP_BANDIT=true
            ;;
        -h|--help)
            grep '^#' "$0" | head -n 12 | sed 's/^# //'
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

OVERALL_EXIT_CODE=0

# ── Bandit static analysis ──────────────────────────────────────────────────
if [[ "$SKIP_BANDIT" == false ]]; then
    log_info "Running bandit static analysis..."
    check_dependency bandit

    BANDIT_ARGS=(
        "-r" "."
        "-f" "json"
        "-o" "bandit-report.json"
        "-ll"  # Report medium and high severity
        "-ii"  # Report medium and high confidence
    )

    # Override with user-specified levels
    case "$SEVERITY_LEVEL" in
        high)   BANDIT_ARGS=("-r" "." "-f" "json" "-o" "bandit-report.json" "-lll") ;;
        medium) BANDIT_ARGS=("-r" "." "-f" "json" "-o" "bandit-report.json" "-ll") ;;
        low)    BANDIT_ARGS=("-r" "." "-f" "json" "-o" "bandit-report.json" "-l") ;;
    esac

    # Exclude common non-project directories
    BANDIT_ARGS+=("--exclude" "./.venv,./venv,./node_modules,./.git,./dist,./build,./.tox")

    BANDIT_EXIT_CODE=0
    bandit "${BANDIT_ARGS[@]}" || BANDIT_EXIT_CODE=$?

    if [[ "$BANDIT_EXIT_CODE" -eq 0 ]]; then
        log_success "Bandit: No security issues found."
    elif [[ "$BANDIT_EXIT_CODE" -eq 1 ]]; then
        log_warn "Bandit: Security issues detected. See bandit-report.json for details."
        if [[ "$FAIL_ON_ISSUE" == true ]]; then
            OVERALL_EXIT_CODE=1
        fi
    else
        log_error "Bandit: Scan failed with exit code $BANDIT_EXIT_CODE."
        OVERALL_EXIT_CODE=1
    fi

    # Also generate a human-readable text report
    bandit -r . -f txt -o bandit-report.txt \
        --exclude "./.venv,./venv,./node_modules,./.git,./dist,./build,./.tox" \
        2>/dev/null || true
else
    log_warn "Bandit scan skipped."
fi

# ── Safety dependency check ─────────────────────────────────────────────────
if [[ "$SKIP_SAFETY" == false ]]; then
    log_info "Running safety dependency vulnerability check..."
    check_dependency safety

    SAFETY_EXIT_CODE=0
    safety check --json --output safety-report.json || SAFETY_EXIT_CODE=$?

    if [[ "$SAFETY_EXIT_CODE" -eq 0 ]]; then
        log_success "Safety: No known vulnerabilities in dependencies."
    elif [[ "$SAFETY_EXIT_CODE" -eq 255 ]]; then
        log_warn "Safety: Vulnerabilities detected. See safety-report.json for details."
        if [[ "$FAIL_ON_ISSUE" == true ]]; then
            OVERALL_EXIT_CODE=1
        fi
    else
        log_error "Safety: Scan failed with exit code $SAFETY_EXIT_CODE."
        OVERALL_EXIT_CODE=1
    fi

    # Also generate a human-readable text report
    safety check --output safety-report.txt 2>/dev/null || true
else
    log_warn "Safety scan skipped."
fi

# ── Summary ─────────────────────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════════════════════"
if [[ "$OVERALL_EXIT_CODE" -eq 0 ]]; then
    log_success "Security scan completed successfully!"
    echo "══════════════════════════════════════════════════════════════"
    exit 0
else
    log_error "Security scan found issues. Review the reports for details."
    echo "══════════════════════════════════════════════════════════════"
    exit 1
fi
