#!/usr/bin/env bash
# deploy.sh — Deploy application to Kubernetes using kubectl.
#
# Usage:
#   ./scripts/deploy.sh --environment ENV --image IMAGE [--namespace NS] [--dry-run]
#
# Options:
#   --environment ENV     Target environment (staging or production). Required.
#   --image IMAGE         Docker image to deploy (e.g., registry/image:tag). Required.
#   --namespace NS        Kubernetes namespace (default: derived from environment).
#   --deployment NAME     Deployment name (default: app).
#   --container NAME      Container name in the pod (default: app).
#   --replicas N          Number of replicas (default: from k8s config).
#   --dry-run             Print the manifest without applying.
#   --timeout SECONDS     Deployment timeout in seconds (default: 300).
#   --wait                Wait for rollout to complete.
#
# Exit codes:
#   0  Deployment succeeded.
#   1  Deployment failed.

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
IMAGE=""
NAMESPACE=""
DEPLOYMENT_NAME="app"
CONTAINER_NAME="app"
REPLICAS=""
DRY_RUN=false
TIMEOUT=300
WAIT=false

for arg in "$@"; do
    case "$arg" in
        --environment)
            shift
            ENVIRONMENT="${1:-}"
            ;;
        --image)
            shift
            IMAGE="${1:-}"
            ;;
        --namespace)
            shift
            NAMESPACE="${1:-}"
            ;;
        --deployment)
            shift
            DEPLOYMENT_NAME="${1:-app}"
            ;;
        --container)
            shift
            CONTAINER_NAME="${1:-app}"
            ;;
        --replicas)
            shift
            REPLICAS="${1:-}"
            ;;
        --dry-run)
            DRY_RUN=true
            ;;
        --timeout)
            shift
            TIMEOUT="${1:-300}"
            ;;
        --wait)
            WAIT=true
            ;;
        -h|--help)
            grep '^#' "$0" | head -n 14 | sed 's/^# //'
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

if [[ -z "$IMAGE" ]]; then
    log_error "--image is required."
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

log_info "Deployment configuration:"
log_info "  Environment: $ENVIRONMENT"
log_info "  Namespace:   $NAMESPACE"
log_info "  Image:       $IMAGE"
log_info "  Deployment:  $DEPLOYMENT_NAME"
log_info "  Container:   $CONTAINER_NAME"

# ── Verify namespace exists ─────────────────────────────────────────────────
if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
    log_warn "Namespace '$NAMESPACE' does not exist. Creating it..."
    kubectl create namespace "$NAMESPACE"
fi

# ── Apply Kubernetes manifests ──────────────────────────────────────────────
K8S_DIR="k8s/${ENVIRONMENT}"
if [[ ! -d "$K8S_DIR" ]]; then
    log_warn "Kubernetes manifest directory not found: $K8S_DIR"
    log_warn "Skipping manifest application."
else
    log_info "Applying Kubernetes manifests from $K8S_DIR..."

    for manifest in "$K8S_DIR"/*.yaml "$K8S_DIR"/*.yml; do
        [[ -f "$manifest" ]] || continue

        log_info "  Applying: $(basename "$manifest")"

        if [[ "$DRY_RUN" == true ]]; then
            kubectl apply -f "$manifest" --namespace "$NAMESPACE" --dry-run=client -o yaml
        else
            kubectl apply -f "$manifest" --namespace "$NAMESPACE"
        fi
    done
fi

# ── Update deployment image ─────────────────────────────────────────────────
if [[ "$DRY_RUN" == false ]]; then
    log_info "Updating deployment image..."

    kubectl set image "deployment/${DEPLOYMENT_NAME}" \
        "${CONTAINER_NAME}=${IMAGE}" \
        --namespace "$NAMESPACE"

    # Update replica count if specified
    if [[ -n "$REPLICAS" ]]; then
        log_info "Scaling deployment to $REPLICAS replicas..."
        kubectl scale "deployment/${DEPLOYMENT_NAME}" \
            --replicas="$REPLICAS" \
            --namespace "$NAMESPACE"
    fi

    # ── Wait for rollout ────────────────────────────────────────────────────
    if [[ "$WAIT" == true ]]; then
        log_info "Waiting for rollout to complete (timeout: ${TIMEOUT}s)..."

        if kubectl rollout status "deployment/${DEPLOYMENT_NAME}" \
            --namespace "$NAMESPACE" \
            --timeout="${TIMEOUT}s"; then
            log_success "Rollout completed successfully."
        else
            log_error "Rollout failed or timed out."
            log_info "Initiating rollback..."
            "$(dirname "$0")/rollback.sh" --environment "$ENVIRONMENT" --namespace "$NAMESPACE"
            exit 1
        fi
    fi
else
    log_warn "Dry run mode — no changes applied."
fi

# ── Verify deployment ───────────────────────────────────────────────────────
if [[ "$DRY_RUN" == false ]]; then
    log_info "Verifying deployment status..."
    kubectl get "deployment/${DEPLOYMENT_NAME}" --namespace "$NAMESPACE" -o wide
    kubectl get pods --namespace "$NAMESPACE" -l "app=${DEPLOYMENT_NAME}"
fi

# ── Summary ─────────────────────────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════════════════════"
log_success "Deployment to $ENVIRONMENT completed successfully!"
echo "══════════════════════════════════════════════════════════════"
exit 0
