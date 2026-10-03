#!/usr/bin/env bash
# =============================================================================
# backup-cron.sh — Cron wrapper for scheduled database backups
#
# This script is designed to be called by cron. It sets up the environment,
# runs the backup, and handles cron-specific concerns like PATH and locking.
#
# Cron examples:
#   # Every day at 2:00 AM
#   0 2 * * * /path/to/backup-cron.sh >> /var/log/recruitment-backup-cron.log 2>&1
#
#   # Every 6 hours
#   0 */6 * * * /path/to/backup-cron.sh >> /var/log/recruitment-backup-cron.log 2>&1
#
#   # Weekly full backup (Sunday at 3 AM) with S3 upload
#   0 3 * * 0 S3_BUCKET=my-bucket /path/to/backup-cron.sh >> /var/log/recruitment-backup-cron.log 2>&1
#
#   # Daily incremental (using WAL archiving, requires archive_command config)
#   0 2 * * * BACKUP_TYPE=incremental /path/to/backup-cron.sh
# =============================================================================

set -euo pipefail
IFS=$'\n\t'

# ─── Cron-safe environment ──────────────────────────────────────────────────
export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export HOME="${HOME:-/root}"
export LANG="en_US.UTF-8"
export LC_ALL="en_US.UTF-8"

# ─── Configuration ──────────────────────────────────────────────────────────
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly BACKUP_SCRIPT="${SCRIPT_DIR}/backup.sh"
readonly LOCK_DIR="/var/lock/recruitment-platform"
readonly LOCK_FILE="${LOCK_DIR}/backup.lock"
readonly PID_FILE="${LOCK_DIR}/backup.pid"
readonly LOG_DIR="/var/log/recruitment-platform"
readonly LOG_FILE="${LOG_DIR}/backup-cron.log"

# Database defaults (override via environment or .env file)
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-recruitment}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-}"

# S3 defaults
S3_BUCKET="${S3_BUCKET:-}"
S3_PREFIX="${S3_PREFIX:-backups/database}"
AWS_PROFILE="${AWS_PROFILE:-default}"
AWS_REGION="${AWS_REGION:-us-east-1}"

# Backup defaults
BACKUP_DIR="${BACKUP_DIR:-/var/backups/recruitment-platform}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"

# ─── Load .env if present ────────────────────────────────────────────────────
ENV_FILE="${SCRIPT_DIR}/.env"
if [[ -f "${ENV_FILE}" ]]; then
    # Source env file, ignoring comments and empty lines
    while IFS='=' read -r key value; do
        [[ "${key}" =~ ^[[:space:]]*# ]] && continue
        [[ -z "${key}" ]] && continue
        key="$(echo "${key}" | tr -d '[:space:]')"
        value="$(echo "${value}" | tr -d '[:space:]')"
        # Remove surrounding quotes
        value="${value#\"}"
        value="${value%\"}"
        value="${value#\'}"
        value="${value%\'}"
        export "${key}=${value}"
    done < "${ENV_FILE}"
fi

# ─── Logging ─────────────────────────────────────────────────────────────────
mkdir -p "${LOG_DIR}" "${LOCK_DIR}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [CRON] $*" | tee -a "${LOG_FILE}"
}

# ─── Lock management ─────────────────────────────────────────────────────────
acquire_lock() {
    if [[ -f "${LOCK_FILE}" ]]; then
        local old_pid
        old_pid=$(cat "${LOCK_FILE}" 2>/dev/null || echo "")

        if [[ -n "${old_pid}" ]] && kill -0 "${old_pid}" 2>/dev/null; then
            log "Another backup process is already running (PID: ${old_pid}). Exiting."
            exit 0
        else
            log "Removing stale lock file"
            rm -f "${LOCK_FILE}"
        fi
    fi

    mkdir -p "${LOCK_DIR}"
    echo $$ > "${LOCK_FILE}"
    echo $$ > "${PID_FILE}"
}

release_lock() {
    rm -f "${LOCK_FILE}" "${PID_FILE}"
}

# ─── Cleanup trap ────────────────────────────────────────────────────────────
cleanup() {
    local exit_code=$?
    release_lock
    if [[ $exit_code -ne 0 ]]; then
        log "Backup cron job failed with exit code ${exit_code}"
    fi
}
trap cleanup EXIT

# ─── Health check ────────────────────────────────────────────────────────────
health_check() {
    # Check if PostgreSQL is running
    if ! pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" &>/dev/null; then
        log "WARNING: PostgreSQL is not ready at ${DB_HOST}:${DB_PORT}"
        # Don't exit — might be a temporary issue, backup.sh will handle it
    fi

    # Check disk space
    local available_space
    available_space=$(df -P "${BACKUP_DIR}" 2>/dev/null | awk 'NR==2 {print $4}' || echo "0")
    if [[ "${available_space}" -lt 1048576 ]]; then  # Less than 1GB
        log "WARNING: Low disk space on backup volume: ${available_space}KB available"
    fi
}

# ─── Run backup ──────────────────────────────────────────────────────────────
run_backup() {
    log "Starting scheduled backup..."

    local backup_opts=()

    # Add verbose flag for cron logging
    backup_opts+=(--verbose)

    # Run the main backup script
    if "${BACKUP_SCRIPT}" "${backup_opts[@]}"; then
        log "Scheduled backup completed successfully"
        return 0
    else
        log "Scheduled backup FAILED"
        return 1
    fi
}

# ─── Install cron job ────────────────────────────────────────────────────────
install_cron() {
    local schedule="${1:-0 2 * * *}"

    # Check if already installed
    if crontab -l 2>/dev/null | grep -q "backup-cron.sh"; then
        echo "Cron job already installed. Current entry:"
        crontab -l | grep "backup-cron.sh"
        return 0
    fi

    # Add to crontab
    (crontab -l 2>/dev/null; echo "${schedule} ${SCRIPT_DIR}/backup-cron.sh >> ${LOG_FILE} 2>&1") | crontab -

    echo "Cron job installed: ${schedule}"
    echo "Logs: ${LOG_FILE}"
}

# ─── Uninstall cron job ──────────────────────────────────────────────────────
uninstall_cron() {
    crontab -l 2>/dev/null | grep -v "backup-cron.sh" | crontab -
    echo "Cron job removed"
}

# ─── Main ────────────────────────────────────────────────────────────────────
main() {
    case "${1:-run}" in
        install)
            install_cron "${2:-0 2 * * *}"
            ;;
        uninstall)
            uninstall_cron
            ;;
        run)
            acquire_lock
            health_check
            run_backup
            ;;
        *)
            echo "Usage: $0 {run|install [schedule]|uninstall}"
            echo ""
            echo "Examples:"
            echo "  $0 run                              # Run backup once"
            echo "  $0 install '0 2 * * *'              # Install daily at 2 AM"
            echo "  $0 install '0 */6 * * *'            # Install every 6 hours"
            echo "  $0 uninstall                        # Remove cron job"
            exit 1
            ;;
    esac
}

main "$@"
