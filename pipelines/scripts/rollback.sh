#!/usr/bin/env bash
# rollback.sh — Rollback a Kubernetes deployment to the previous revision.
#
# Usage:
#   ./scripts/rollback.sh --environment ENV [--namespace NS] [--deployment NAME] [--to-revision N]
#
# Options:
#   --environment ENV     Target environment (staging or production). Required.
#   --namespace NS        Kubernetes namespace (default: derived from environment).
#   --deployment NAME     Deployment name (default: app).
#   --to-revision N       Rollback to a specific revision number.
#   --dry-run             Show what would be rolled back without executing.
#
# Exit codes:
#   0  Rollback succeeded.
#   1  Rollback failed.

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
ENVIRONMENT=""
NAMESPACE=""
DEPLOYMENT_NAME="app"
TO_REVISION=""
DRY_RUN=false

for arg in "$@"; do
    case "$arg" in
        --environment)
            shift
            ENVIRONMENT="${1:-}"
            ;;
        --namespace)
            shift
            NAMESPACE="${1:-}"
            ;;
        --deployment)
            shift
            DEPLOYMENT_NAME="${1:-app}"
            ;;
        --to-revision)
            shift
            TO_REVISION="${1:-}"
            ;;
        --dry-run)
            DRY_RUN=true
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

# ── Validate required arguments ──────────────────────────────────────────────
if [[ -z "$ENVIRONMENT" ]]; then
    log_error "--environment is required (staging or production)."
    exit 1
fi

if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
    log_error "Invalid environment: $ENVIRONMENT. Must be 'staging' or 'production'."
    exit 1
fi

# ── Determine project root ──────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$PROJECT_ROOT"

# ── Check dependencies ──────────────────────────────────────────────────────
check_dependency() {
    local cmd="$1"
    if ! command -v "$cmd" &>/dev/null; then
        log_error "'$cmd' is not installed."
        exit 1
    fi
}

log_info "Checking dependencies..."
check_dependency kubectl

# ── Set defaults ─────────────────────────────────────────────────────────────
if [[ -z "$NAMESPACE" ]]; then
    NAMESPACE="$ENVIRONMENT"
fi

log_info "Rollback configuration:"
log_info "  Environment: $ENVIRONMENT"
log_info "  Namespace:   $NAMESPACE"
log_info "  Deployment:  $DEPLOYMENT_NAME"
if [[ -n "$TO_REVISION" ]]; then
    log_info "  Revision:    $TO_REVISION"
fi

# ── Verify deployment exists ────────────────────────────────────────────────
if ! kubectl get "deployment/${DEPLOYMENT_NAME}" --namespace "$NAMESPACE" &>/dev/null; then
    log_error "Deployment '$DEPLOYMENT_NAME' not found in namespace '$NAMESPACE'."
    exit 1
fi

# ── Show rollout history ────────────────────────────────────────────────────
log_info "Rollout history:"
kubectl rollout history "deployment/${DEPLOYMENT_NAME}" --namespace "$NAMESPACE"

# ── Perform rollback ────────────────────────────────────────────────────────
if [[ "$DRY_RUN" == true ]]; then
    log_warn "Dry run mode — no changes will be made."
    log_info "Would execute: kubectl rollout undo deployment/$DEPLOYMENT_NAME --namespace $NAMESPACE"
    exit 0
fi

ROLLBACK_ARGS=(
    "rollout" "undo"
    "deployment/${DEPLOYMENT_NAME}"
    "--namespace" "$NAMESPACE"
)

if [[ -n "$TO_REVISION" ]]; then
    ROLLBACK_ARGS+=("--to-revision" "$TO_REVISION")
    log_info "Rolling back to revision $TO_REVISION..."
else
    log_info "Rolling back to previous revision..."
fi

ROLLBACK_EXIT_CODE=0
kubectl "${ROLLBACK_ARGS[@]}" || ROLLBACK_EXIT_CODE=$?

if [[ "$ROLLBACK_EXIT_CODE" -ne 0 ]]; then
    log_error "Rollback failed with exit code: $ROLLBACK_EXIT_CODE"
    exit 1
fi

log_success "Rollback command executed successfully."

# ── Wait for rollback to complete ───────────────────────────────────────────
log_info "Waiting for rollback to complete..."
kubectl rollout status "deployment/${DEPLOYMENT_NAME}" \
    --namespace "$NAMESPACE" \
    --timeout=300s

log_success "Rollback completed."

# ── Verify rollback ─────────────────────────────────────────────────────────
log_info "Current deployment status:"
kubectl get "deployment/${DEPLOYMENT_NAME}" --namespace "$NAMESPACE" -o wide
kubectl get pods --namespace "$NAMESPACE" -l "app=${DEPLOYMENT_NAME}"

# ── Summary ─────────────────────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════════════════════"
log_success "Rollback to $ENVIRONMENT completed successfully!"
echo "══════════════════════════════════════════════════════════════"
exit 0
