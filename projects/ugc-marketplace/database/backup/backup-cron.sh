#!/usr/bin/env bash
# ============================================================
# UGC Marketplace — Cron Wrapper for Scheduled Backups
# Designed to be called by cron. Handles environment setup,
# logging, and error reporting.
#
# Cron examples:
#   Every 6 hours:  0 */6 * * * /path/to/backup-cron.sh
#   Daily at 2 AM:  0 2 * * *   /path/to/backup-cron.sh
#   Weekly (Sun):   0 3 * * 0   /path/to/backup-cron.sh --weekly
# ============================================================
set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly BACKUP_SCRIPT="${SCRIPT_DIR}/backup.sh"
readonly CRON_LOG_DIR="${SCRIPT_DIR}/../logs/cron"
readonly CRON_LOG_FILE="${CRON_LOG_DIR}/cron_$(date +%Y%m%d).log"
readonly PID_FILE="/tmp/ugc-backup-cron.pid"

# Ensure log directory exists
mkdir -p "$CRON_LOG_DIR"

# ── Logging ────────────────────────────────────────────────
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [CRON] $*" >> "$CRON_LOG_FILE"
}

# ── Lock ───────────────────────────────────────────────────
if [[ -f "$PID_FILE" ]]; then
    old_pid=$(cat "$PID_FILE" 2>/dev/null) || true
    if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
        log "ERROR: Another cron backup is running (PID: $old_pid)"
        exit 1
    fi
fi
echo $$ > "$PID_FILE"
trap 'rm -f "$PID_FILE"' EXIT

# ── Environment Setup ─────────────────────────────────────
# Load .env if present
ENV_FILE="${SCRIPT_DIR}/../docker/.env"
if [[ -f "$ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
fi

# Ensure PATH includes common locations
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin:$PATH"

# Set umask for secure file creation
umask 0077

# ── Parse Arguments ───────────────────────────────────────
BACKUP_ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --weekly)
            # Weekly: full backup with S3 upload
            BACKUP_ARGS+=()
            export S3_ENABLED="${S3_ENABLED:-true}"
            shift
            ;;
        --daily)
            # Daily: local backup only
            BACKUP_ARGS+=()
            export S3_ENABLED="${S3_ENABLED:-false}"
            shift
            ;;
        --s3)
            export S3_ENABLED=true
            shift
            ;;
        *)
            BACKUP_ARGS+=("$1")
            shift
            ;;
    esac
done

# ── Run Backup ────────────────────────────────────────────
log "Starting scheduled backup..."
log "Arguments: ${BACKUP_ARGS[*]:-none}"
log "S3_ENABLED: ${S3_ENABLED:-false}"

if [[ ! -x "$BACKUP_SCRIPT" ]]; then
    log "ERROR: Backup script not found or not executable: $BACKUP_SCRIPT"
    exit 1
fi

# Run the backup script
if "$BACKUP_SCRIPT" "${BACKUP_ARGS[@]}"; then
    log "Backup completed successfully"
    exit_code=0
else
    exit_code=$?
    log "ERROR: Backup failed with exit code $exit_code"
fi

# ── Cleanup Old Cron Logs ─────────────────────────────────
# Keep cron logs for 90 days
find "$CRON_LOG_DIR" -name "cron_*.log" -type f -mtime +90 -delete 2>/dev/null || true

exit $exit_code
