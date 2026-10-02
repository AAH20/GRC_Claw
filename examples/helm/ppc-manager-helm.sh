#!/usr/bin/env bash
set -euo pipefail

# Ppc Manager - Helm Chart Example
# Production-grade deployment script with install, upgrade, rollback, and uninstall

readonly CHART_NAME="ppc-manager"
readonly NAMESPACE="grc-claw"
readonly RELEASE_NAME="ppc-manager"
readonly CHART_VERSION="1.0.0"
readonly VALUES_FILE="values-ppc-manager.yaml"
readonly TIMEOUT="5m"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_debug() { echo -e "${BLUE}[DEBUG]${NC} $*"; }

cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Script failed with exit code $exit_code"
    fi
    exit $exit_code
}
trap cleanup EXIT

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v helm >/dev/null 2>&1; then
        log_error "Helm is not installed. Install from https://helm.sh/docs/intro/install/"
        exit 1
    fi
    
    if ! command -v kubectl >/dev/null 2>&1; then
        log_error "kubectl is not installed. Install from https://kubernetes.io/docs/tasks/tools/"
        exit 1
    fi
    
    # Verify cluster connectivity
    if ! kubectl cluster-info >/dev/null 2>&1; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Verify helm can talk to cluster
    if ! helm version --short >/dev/null 2>&1; then
        log_error "Helm is not functioning correctly"
        exit 1
    fi
    
    log_info "All prerequisites met"
}

ensure_namespace() {
    if ! kubectl get namespace "${NAMESPACE}" >/dev/null 2>&1; then
        log_info "Creating namespace: ${NAMESPACE}"
        kubectl create namespace "${NAMESPACE}"
    else
        log_debug "Namespace ${NAMESPACE} already exists"
    fi
}

validate_values() {
    if [[ ! -f "${VALUES_FILE}" ]]; then
        log_warn "Values file ${VALUES_FILE} not found, using defaults"
        echo "image:" > "${VALUES_FILE}"
        echo "  repository: grc-claw/${CHART_NAME}" >> "${VALUES_FILE}"
        echo "  tag: latest" >> "${VALUES_FILE}"
        echo "  pullPolicy: IfNotPresent" >> "${VALUES_FILE}"
        echo "replicaCount: 2" >> "${VALUES_FILE}"
        echo "service:" >> "${VALUES_FILE}"
        echo "  type: ClusterIP" >> "${VALUES_FILE}"
        echo "  port: 8080" >> "${VALUES_FILE}"
        echo "resources:" >> "${VALUES_FILE}"
        echo "  limits:" >> "${VALUES_FILE}"
        echo "    cpu: 500m" >> "${VALUES_FILE}"
        echo "    memory: 512Mi" >> "${VALUES_FILE}"
        echo "  requests:" >> "${VALUES_FILE}"
        echo "    cpu: 250m" >> "${VALUES_FILE}"
        echo "    memory: 256Mi" >> "${VALUES_FILE}"
        echo "autoscaling:" >> "${VALUES_FILE}"
        echo "  enabled: true" >> "${VALUES_FILE}"
        echo "  minReplicas: 2" >> "${VALUES_FILE}"
        echo "  maxReplicas: 10" >> "${VALUES_FILE}"
        echo "  targetCPUUtilizationPercentage: 70" >> "${VALUES_FILE}"
        echo "  targetMemoryUtilizationPercentage: 80" >> "${VALUES_FILE}"
        echo "ingress:" >> "${VALUES_FILE}"
        echo "  enabled: true" >> "${VALUES_FILE}"
        echo "  className: nginx" >> "${VALUES_FILE}"
        echo "  hosts:" >> "${VALUES_FILE}"
        echo "    - host: ppc-manager.grc-claw.local" >> "${VALUES_FILE}"
        echo "      paths:" >> "${VALUES_FILE}"
        echo "        - path: /" >> "${VALUES_FILE}"
        echo "          pathType: Prefix" >> "${VALUES_FILE}"
        envsubst < "${VALUES_FILE}" > "${VALUES_FILE}.tmp" && mv "${VALUES_FILE}.tmp" "${VALUES_FILE}"
    fi
}

install() {
    log_info "Installing ${RELEASE_NAME}..."
    check_prerequisites
    ensure_namespace
    validate_values
    
    helm install "${RELEASE_NAME}" "./charts/${CHART_NAME}" \
        --namespace "${NAMESPACE}" \
        --create-namespace \
        --values "${VALUES_FILE}" \
        --version "${CHART_VERSION}" \
        --atomic \
        --wait \
        --timeout "${TIMEOUT}" \
        --description "${CHART_NAME} deployment"
    
    log_info "${RELEASE_NAME} installed successfully"
    log_info "Run 'kubectl get pods -n ${NAMESPACE}' to verify"
}

upgrade() {
    log_info "Upgrading ${RELEASE_NAME}..."
    check_prerequisites
    ensure_namespace
    validate_values
    
    # Verify release exists
    if ! helm status "${RELEASE_NAME}" --namespace "${NAMESPACE}" >/dev/null 2>&1; then
        log_error "Release ${RELEASE_NAME} not found in namespace ${NAMESPACE}"
        exit 1
    fi
    
    helm upgrade "${RELEASE_NAME}" "./charts/${CHART_NAME}" \
        --namespace "${NAMESPACE}" \
        --values "${VALUES_FILE}" \
        --version "${CHART_VERSION}" \
        --atomic \
        --wait \
        --timeout "${TIMEOUT}" \
        --description "${CHART_NAME} upgrade"
    
    log_info "${RELEASE_NAME} upgraded successfully"
}

rollback() {
    log_info "Rolling back ${RELEASE_NAME}..."
    check_prerequisites
    
    # Verify release exists
    if ! helm status "${RELEASE_NAME}" --namespace "${NAMESPACE}" >/dev/null 2>&1; then
        log_error "Release ${RELEASE_NAME} not found in namespace ${NAMESPACE}"
        exit 1
    fi
    
    # Get previous revision
    local history
    history=$(helm history "${RELEASE_NAME}" --namespace "${NAMESPACE}" --max 1 -o json 2>/dev/null || echo "[]")
    local revision
    revision=$(echo "${history}" | jq -r '.[0].revision // "0"')
    
    if [[ "${revision}" -le 1 ]]; then
        log_error "No previous revision to roll back to"
        exit 1
    fi
    
    local prev_revision=$((revision - 1))
    log_info "Rolling back to revision ${prev_revision}"
    
    helm rollback "${RELEASE_NAME}" "${prev_revision}" \
        --namespace "${NAMESPACE}" \
        --wait \
        --timeout "${TIMEOUT}" \
        --cleanup-on-fail
    
    log_info "${RELEASE_NAME} rolled back to revision ${prev_revision} successfully"
}

uninstall() {
    log_info "Uninstalling ${RELEASE_NAME}..."
    check_prerequisites
    
    # Verify release exists
    if ! helm status "${RELEASE_NAME}" --namespace "${NAMESPACE}" >/dev/null 2>&1; then
        log_warn "Release ${RELEASE_NAME} not found in namespace ${NAMESPACE}"
        return 0
    fi
    
    helm uninstall "${RELEASE_NAME}" \
        --namespace "${NAMESPACE}" \
        --wait \
        --timeout "${TIMESPACE:-${TIMEOUT}}" \
        --no-hooks
    
    log_info "${RELEASE_NAME} uninstalled successfully"
}

status() {
    log_info "Checking status of ${RELEASE_NAME}..."
    helm status "${RELEASE_NAME}" --namespace "${NAMESPACE}"
    echo ""
    kubectl get pods,svc,ingress -n "${NAMESPACE}" -l "app.kubernetes.io/instance=${RELEASE_NAME}"
}

usage() {
    cat <<EOF
Usage: $(basename "$0") <command>

Commands:
  install     Install the ${RELEASE_NAME} Helm chart
  upgrade     Upgrade the ${RELEASE_NAME} Helm chart
  rollback    Rollback ${RELEASE_NAME} to previous revision
  uninstall   Uninstall the ${RELEASE_NAME} Helm chart
  status      Show deployment status

Examples:
  $(basename "$0") install
  $(basename "$0") upgrade
  $(basename "$0") rollback
  $(basename "$0") uninstall
EOF
}

main() {
    if [[ $# -eq 0 ]]; then
        usage
        exit 1
    fi
    
    case "${1:-}" in
        install)
            install
            ;;
        upgrade)
            upgrade
            ;;
        rollback)
            rollback
            ;;
        uninstall)
            uninstall
            ;;
        status)
            status
            ;;
        -h|--help|help)
            usage
            ;;
        *)
            log_error "Unknown command: $1"
            usage
            exit 1
            ;;
    esac
}

main "$@"
