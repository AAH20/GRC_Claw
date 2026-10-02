#!/usr/bin/env bash
# lint.sh — Run ruff and mypy linting checks.
#
# Usage:
#   ./scripts/lint.sh [--fix] [--strict]
#
# Options:
#   --fix     Auto-fix linting issues where possible.
#   --strict  Enable strict mypy mode (disallow untyped defs).
#
# Exit codes:
#   0  All checks passed.
#   1  One or more checks failed.

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
FIX_MODE=false
STRICT_MODE=false

for arg in "$@"; do
    case "$arg" in
        --fix)   FIX_MODE=true ;;
        --strict) STRICT_MODE=true ;;
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
check_dependency ruff
check_dependency mypy

# ── Ruff linting ────────────────────────────────────────────────────────────
log_info "Running ruff linter..."

RUFF_ARGS=("check" ".")
if [[ "$FIX_MODE" == true ]]; then
    RUFF_ARGS+=("--fix")
    log_warn "Auto-fix mode enabled — ruff will modify files in place."
fi

if ruff "${RUFF_ARGS[@]}"; then
    log_success "Ruff: No issues found."
else
    log_error "Ruff: Linting issues detected."
    RUFF_EXIT_CODE=1
fi

# ── Ruff format check ───────────────────────────────────────────────────────
log_info "Checking code formatting with ruff format..."

if ruff format --check .; then
    log_success "Ruff format: All files properly formatted."
else
    log_error "Ruff format: Some files need reformatting. Run: ruff format ."
    RUFF_EXIT_CODE=1
fi

# ── Mypy type checking ──────────────────────────────────────────────────────
log_info "Running mypy type checker..."

MYPY_ARGS=(
    "--show-error-codes"
    "--pretty"
    "--warn-unused-configs"
    "--warn-redundant-casts"
    "--warn-unused-ignores"
    "--no-error-summary"
)

if [[ "$STRICT_MODE" == true ]]; then
    MYPY_ARGS+=("--disallow-untyped-defs" "--disallow-incomplete-defs")
    log_warn "Strict mode enabled — all functions must have type annotations."
fi

# Determine Python files to check
PYTHON_FILES=()
if [[ -d "src" ]]; then
    while IFS= read -r -d '' file; do
        PYTHON_FILES+=("$file")
    done < <(find src -name "*.py" -print0 2>/dev/null)
fi
if [[ -d "tests" ]]; then
    while IFS= read -r -d '' file; do
        PYTHON_FILES+=("$file")
    done < <(find tests -name "*.py" -print0 2>/dev/null)
fi
# Also check top-level .py files
while IFS= read -r -d '' file; do
    PYTHON_FILES+=("$file")
done < <(find . -maxdepth 1 -name "*.py" -print0 2>/dev/null)

if [[ ${#PYTHON_FILES[@]} -eq 0 ]]; then
    log_warn "No Python files found to type-check."
    MYPY_EXIT_CODE=0
else
    if mypy "${MYPY_ARGS[@]}" "${PYTHON_FILES[@]}"; then
        log_success "Mypy: No type errors found."
        MYPY_EXIT_CODE=0
    else
        log_error "Mypy: Type errors detected."
        MYPY_EXIT_CODE=1
    fi
fi

# ── Summary ─────────────────────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════════════════════"
if [[ "${RUFF_EXIT_CODE:-0}" -eq 0 && "${MYPY_EXIT_CODE:-0}" -eq 0 ]]; then
    log_success "All linting checks passed!"
    echo "══════════════════════════════════════════════════════════════"
    exit 0
else
    log_error "One or more linting checks failed."
    echo "══════════════════════════════════════════════════════════════"
    exit 1
fi
