#!/usr/bin/env bash
# =============================================================================
# backup-cron.sh — Cron Job for Scheduled Backups
# =============================================================================
# Designed to be called by crontab. Performs scheduled backups with
# configurable schedule, logging, and alerting.
#
# Crontab examples:
#   # Every day at 2:00 AM
#   0 2 * * * /path/to/backup-cron.sh --daily
#
#   # Every 6 hours
#   0 */6 * * * /path/to/backup-cron.sh --hourly
#
#   # Weekly (Sunday at 3:00 AM)
#   0 3 * * 0 /path/to/backup-cron.sh --weekly
#
#   # Monthly (1st of month at 4:00 AM)
#   0 4 1 * * /path/to/backup-cron.sh --monthly
# =============================================================================

set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env"

if [[ -f "${ENV_FILE}" ]]; then
    set -a
    source "${ENV_FILE}"
    set +a
fi

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-gated_communities}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"
BACKUP_DIR="${BACKUP_DIR:-${SCRIPT_DIR}/backups}"
S3_BUCKET="${S3_BUCKET:-}"
S3_PREFIX="${S3_PREFIX:-gated-communities/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
ENCRYPTION_KEY="${ENCRYPTION_KEY:-}"
AWS_PROFILE="${AWS_PROFILE:-default}"
AWS_REGION="${AWS_REGION:-us-east-1}"

LOG_DIR="${LOG_DIR:-${SCRIPT_DIR}/logs}"
LOG_FILE="${LOG_DIR}/cron-$(date +%Y%m%d-%H%M%S).log"
LOCK_FILE="${SCRIPT_DIR}/.backup.lock"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "${timestamp} [${level}] ${message}" | tee -a "${LOG_FILE}"
}

log_info()  { log "INFO"  "$@"; }
log_warn()  { log "WARN"  "$@"; }
log_error() { log "ERROR" "$@"; }

die() {
    log_error "$@"
    send_alert "BACKUP FAILED" "$@"
    exit 1
}

send_alert() {
    local subject="$1"
    local message="$2"
    
    # Email alert
    if [[ -n "${ALERT_EMAIL:-}" ]] && command -v "mail" &>/dev/null; then
        echo "${message}" | mail -s "[Gated Communities] ${subject}" "${ALERT_EMAIL}"
    fi
    
    # Slack webhook
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]] && command -v "curl" &>/dev/null; then
        curl -s -X POST "${SLACK_WEBHOOK_URL}" \
            -H 'Content-type: application/json' \
            -d "{\"text\": \"${subject}: ${message}\"}" &>/dev/null || true
    fi
    
    # PagerDuty
    if [[ -n "${PAGERDUTY_KEY:-}" ]] && command -v "curl" &>/dev/null; then
        curl -s -X POST "https://events.pagerduty.com/v2/enqueue" \
            -H 'Content-type: application/json' \
            -d "{
                \"routing_key\": \"${PAGERDUTY_KEY}\",
                \"event_action\": \"trigger\",
                \"payload\": {
                    \"summary\": \"${subject}: ${message}\",
                    \"severity\": \"critical\"
                }
            }" &>/dev/null || true
    fi
}

acquire_lock() {
    if [[ -f "${LOCK_FILE}" ]]; then
        local pid
        pid=$(cat "${LOCK_FILE}")
        if kill -0 "${pid}" 2>/dev/null; then
            die "Another backup process is already running (PID: ${pid})"
        else
            log_warn "Removing stale lock file"
            rm -f "${LOCK_FILE}"
        fi
    fi
    
    echo $$ > "${LOCK_FILE}"
}

release_lock() {
    rm -f "${LOCK_FILE}"
}

cleanup() {
    release_lock
    # Clean up old log files (keep 30 days)
    find "${LOG_DIR}" -type f -name "*.log" -mtime +30 -delete 2>/dev/null || true
}

trap cleanup EXIT ERR

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Options:
  --daily       Daily backup (full)
  --hourly      Hourly backup (incremental)
  --weekly      Weekly backup (full + verify)
  --monthly     Monthly backup (full + verify + archive)
  --verify      Verify last backup integrity
  --alert-test  Send test alert
  -h, --help    Show this help message
EOF
}

perform_daily_backup() {
    log_info "Starting daily backup..."
    
    local backup_script="${SCRIPT_DIR}/backup.sh"
    
    if [[ ! -f "${backup_script}" ]]; then
        die "Backup script not found: ${backup_script}"
    fi
    
    bash "${backup_script}" --full --encrypt --upload --retention "${RETENTION_DAYS}"
    
    log_info "Daily backup completed"
}

perform_hourly_backup() {
    log_info "Starting hourly backup..."
    
    local backup_script="${SCRIPT_DIR}/backup.sh"
    
    if [[ ! -f "${backup_script}" ]]; then
        die "Backup script not found: ${backup_script}"
    fi
    
    bash "${backup_script}" --incremental --upload
    
    log_info "Hourly backup completed"
}

perform_weekly_backup() {
    log_info "Starting weekly backup..."
    
    local backup_script="${SCRIPT_DIR}/backup.sh"
    
    if [[ ! -f "${backup_script}" ]]; then
        die "Backup script not found: ${backup_script}"
    fi
    
    bash "${backup_script}" --full --encrypt --upload --retention "${RETENTION_DAYS}"
    
    # Verify backup
    verify_backup
    
    log_info "Weekly backup completed"
}

perform_monthly_backup() {
    log_info "Starting monthly backup..."
    
    local backup_script="${SCRIPT_DIR}/backup.sh"
    
    if [[ ! -f "${backup_script}" ]]; then
        die "Backup script not found: ${backup_script}"
    fi
    
    bash "${backup_script}" --full --encrypt --upload --retention "${RETENTION_DAYS}"
    
    # Verify backup
    verify_backup
    
    # Archive to Glacier
    if [[ -n "${S3_BUCKET}" ]]; then
        log_info "Archiving to S3 Glacier..."
        aws s3 ls "s3://${S3_BUCKET}/${S3_PREFIX}/" \
            --profile "${AWS_PROFILE}" \
            --region "${AWS_REGION}" \
            --recursive | \
        while read -r line; do
            local file_key
            file_key=$(echo "$line" | awk '{print $4}')
            if [[ -n "${file_key}" ]]; then
                aws s3 cp "s3://${S3_BUCKET}/${file_key}" \
                    "s3://${S3_BUCKET}/${file_key}" \
                    --storage-class GLACIER \
                    --profile "${AWS_PROFILE}" \
                    --region "${AWS_REGION}" &>/dev/null || true
            fi
        done
    fi
    
    log_info "Monthly backup completed"
}

verify_backup() {
    log_info "Verifying last backup..."
    
    local latest_backup
    latest_backup=$(find "${BACKUP_DIR}" -type f \( -name "*.sql" -o -name "*.dump" -o -name "*.backup" -o -name "*.sql.gz" \) -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)
    
    if [[ -z "${latest_backup}" ]]; then
        log_warn "No backup files found to verify"
        return 1
    fi
    
    log_info "Verifying backup: ${latest_backup}"
    
    # Check file integrity
    if [[ "${latest_backup}" == *.gz ]]; then
        if ! gzip -t "${latest_backup}" 2>/dev/null; then
            die "Backup file failed gzip integrity check: ${latest_backup}"
        fi
    fi
    
    # Try to list contents (for custom format)
    if [[ "${latest_backup}" == *.dump ]] || [[ "${latest_backup}" == *.backup ]]; then
        if ! pg_restore -l "${latest_backup}" &>/dev/null; then
            die "Backup file failed pg_restore integrity check: ${latest_backup}"
        fi
    fi
    
    log_info "Backup verification passed"
}

test_alerts() {
    log_info "Sending test alerts..."
    send_alert "TEST ALERT" "This is a test alert from Gated Communities backup system."
    log_info "Test alerts sent"
}

main() {
    local action=""
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --daily)
                action="daily"
                shift
                ;;
            --hourly)
                action="hourly"
                shift
                ;;
            --weekly)
                action="weekly"
                shift
                ;;
            --monthly)
                action="monthly"
                shift
                ;;
            --verify)
                action="verify"
                shift
                ;;
            --alert-test)
                action="alert-test"
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                die "Unknown option: $1"
                ;;
        esac
    done
    
    if [[ -z "${action}" ]]; then
        usage
        exit 1
    fi
    
    mkdir -p "${LOG_DIR}"
    touch "${LOG_FILE}"
    
    log_info "=========================================="
    log_info "Gated Communities Scheduled Backup"
    log_info "Action: ${action}"
    log_info "=========================================="
    
    acquire_lock
    
    case "${action}" in
        daily)
            perform_daily_backup
            ;;
        hourly)
            perform_hourly_backup
            ;;
        weekly)
            perform_weekly_backup
            ;;
        monthly)
            perform_monthly_backup
            ;;
        verify)
            verify_backup
            ;;
        alert-test)
            test_alerts
            ;;
    esac
    
    log_info "=========================================="
    log_info "Scheduled backup completed successfully"
    log_info "=========================================="
}

main "$@"
