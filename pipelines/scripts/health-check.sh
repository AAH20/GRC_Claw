#!/usr/bin/env bash
# health-check.sh — Perform HTTP health checks against a service endpoint.
#
# Usage:
#   ./scripts/health-check.sh --url URL [--retries N] [--delay SECONDS] [--timeout SECONDS]
#
# Options:
#   --url URL           Health check endpoint URL. Required.
#   --retries N         Number of retry attempts (default: 5).
#   --delay SECONDS     Delay between retries in seconds (default: 10).
#   --timeout SECONDS   Request timeout in seconds (default: 30).
#   --expected-status N Expected HTTP status code (default: 200).
#   --json-key KEY      JSON key to check in response body (optional).
#   --json-value VAL    Expected value for the JSON key (optional).
#
# Exit codes:
#   0  Health check passed.
#   1  Health check failed after all retries.

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
HEALTH_URL=""
MAX_RETRIES=5
RETRY_DELAY=10
REQUEST_TIMEOUT=30
EXPECTED_STATUS=200
JSON_KEY=""
JSON_VALUE=""

for arg in "$@"; do
    case "$arg" in
        --url)
            shift
            HEALTH_URL="${1:-}"
            ;;
        --retries)
            shift
            MAX_RETRIES="${1:-5}"
            ;;
        --delay)
            shift
            RETRY_DELAY="${1:-10}"
            ;;
        --timeout)
            shift
            REQUEST_TIMEOUT="${1:-30}"
            ;;
        --expected-status)
            shift
            EXPECTED_STATUS="${1:-200}"
            ;;
        --json-key)
            shift
            JSON_KEY="${1:-}"
            ;;
        --json-value)
            shift
            JSON_VALUE="${1:-}"
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

# ── Validate required arguments ──────────────────────────────────────────────
if [[ -z "$HEALTH_URL" ]]; then
    log_error "--url is required."
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
check_dependency curl
check_dependency jq

# ── Health check logic ──────────────────────────────────────────────────────
log_info "Health check configuration:"
log_info "  URL:            $HEALTH_URL"
log_info "  Max retries:    $MAX_RETRIES"
log_info "  Retry delay:    ${RETRY_DELAY}s"
log_info "  Timeout:        ${REQUEST_TIMEOUT}s"
log_info "  Expected status: $EXPECTED_STATUS"
if [[ -n "$JSON_KEY" ]]; then
    log_info "  JSON key:       $JSON_KEY"
    if [[ -n "$JSON_VALUE" ]]; then
        log_info "  JSON value:     $JSON_VALUE"
    fi
fi

attempt=0
while [[ $attempt -lt $MAX_RETRIES ]]; do
    attempt=$((attempt + 1))
    log_info "Health check attempt $attempt/$MAX_RETRIES..."

    # Perform the HTTP request
    HTTP_RESPONSE=$(curl -s -w "\n%{http_code}" \
        --max-time "$REQUEST_TIMEOUT" \
        --connect-timeout 10 \
        "$HEALTH_URL" 2>/dev/null) || true

    # Extract status code and body
    HTTP_STATUS=$(echo "$HTTP_RESPONSE" | tail -n1)
    HTTP_BODY=$(echo "$HTTP_RESPONSE" | sed '$d')

    # Check if curl succeeded
    if [[ -z "$HTTP_STATUS" || "$HTTP_STATUS" == "000" ]]; then
        log_warn "Connection failed (curl error)."
        if [[ $attempt -lt $MAX_RETRIES ]]; then
            log_info "Waiting ${RETRY_DELAY}s before retry..."
            sleep "$RETRY_DELAY"
        fi
        continue
    fi

    log_info "HTTP status: $HTTP_STATUS"

    # Check HTTP status code
    if [[ "$HTTP_STATUS" != "$EXPECTED_STATUS" ]]; then
        log_warn "Unexpected status code: $HTTP_STATUS (expected: $EXPECTED_STATUS)"
        if [[ $attempt -lt $MAX_RETRIES ]]; then
            log_info "Waiting ${RETRY_DELAY}s before retry..."
            sleep "$RETRY_DELAY"
        fi
        continue
    fi

    # Check JSON key/value if specified
    if [[ -n "$JSON_KEY" ]]; then
        log_info "Checking JSON response for key: $JSON_KEY"

        # Validate JSON response
        if ! echo "$HTTP_BODY" | jq . &>/dev/null; then
            log_warn "Response is not valid JSON."
            if [[ $attempt -lt $MAX_RETRIES ]]; then
                log_info "Waiting ${RETRY_DELAY}s before retry..."
                sleep "$RETRY_DELAY"
            fi
            continue
        fi

        ACTUAL_VALUE=$(echo "$HTTP_BODY" | jq -r ".$JSON_KEY" 2>/dev/null || echo "null")
        log_info "  $JSON_KEY = $ACTUAL_VALUE"

        if [[ -n "$JSON_VALUE" ]]; then
            if [[ "$ACTUAL_VALUE" != "$JSON_VALUE" ]]; then
                log_warn "JSON value mismatch: got '$ACTUAL_VALUE', expected '$JSON_VALUE'"
                if [[ $attempt -lt $MAX_RETRIES ]]; then
                    log_info "Waiting ${RETRY_DELAY}s before retry..."
                    sleep "$RETRY_DELAY"
                fi
                continue
            fi
        fi
    fi

    # All checks passed
    log_success "Health check passed!"
    echo ""
    echo "══════════════════════════════════════════════════════════════"
    log_success "Service is healthy at $HEALTH_URL"
    echo "══════════════════════════════════════════════════════════════"
    exit 0
done

# All retries exhausted
log_error "Health check failed after $MAX_RETRIES attempts."
echo ""
echo "══════════════════════════════════════════════════════════════"
log_error "Service is NOT healthy at $HEALTH_URL"
echo "══════════════════════════════════════════════════════════════"
exit 1
