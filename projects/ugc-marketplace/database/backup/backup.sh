#!/usr/bin/env bash
# ============================================================
# UGC Marketplace — Database Backup Script
# Backs up PostgreSQL and Redis with S3 upload, rotation,
# checksums, and comprehensive error handling.
# ============================================================
set -euo pipefail
IFS=$'\n\t'

# ── Configuration ──────────────────────────────────────────
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "$0")"
readonly TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
readonly DATE_PREFIX="$(date +%Y/%m/%d)"

# Load environment variables from .env if present
ENV_FILE="${ENV_FILE:-${SCRIPT_DIR}/../docker/.env}"
if [[ -f "$ENV_FILE" ]]; then
    # shellcheck disable=SC1090
    set -a
    source "$ENV_FILE"
    set +a
fi

# PostgreSQL settings
readonly PG_HOST="${POSTGRES_HOST:-localhost}"
readonly PG_PORT="${POSTGRES_PORT:-5432}"
readonly PG_DB="${POSTGRES_DB:-ugc_marketplace}"
readonly PG_USER="${POSTGRES_USER:-ugc_user}"
readonly PG_PASSWORD="${POSTGRES_PASSWORD:-}"

# Redis settings
readonly REDIS_HOST="${REDIS_HOST:-localhost}"
readonly REDIS_PORT="${REDIS_PORT:-6379}"
readonly REDIS_PASSWORD="${REDIS_PASSWORD:-}"

# Backup settings
readonly BACKUP_BASE_DIR="${BACKUP_BASE_DIR:-/var/backups/ugc-marketplace}"
readonly BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
readonly BACKUP_FORMAT="${BACKUP_FORMAT:-custom}"  # custom | plain | directory
readonly COMPRESSION_LEVEL="${COMPRESSION_LEVEL:-6}"

# S3 settings
readonly S3_ENABLED="${S3_ENABLED:-false}"
readonly S3_BUCKET="${S3_BUCKET:-}"
readonly S3_PREFIX="${S3_PREFIX:-ugc-marketplace/backups}"
readonly S3_REGION="${S3_REGION:-us-east-1}"
readonly S3_STORAGE_CLASS="${S3_STORAGE_CLASS:-STANDARD_IA}"

# Notification settings
readonly SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"
readonly NOTIFY_ON_SUCCESS="${NOTIFY_ON_SUCCESS:-false}"

# Lock file
readonly LOCK_FILE="/tmp/${SCRIPT_NAME%.sh}.lock"

# ── Logging ────────────────────────────────────────────────
LOG_DIR="${BACKUP_BASE_DIR}/logs"
mkdir -p "$LOG_DIR"
readonly LOG_FILE="${LOG_DIR}/backup_${TIMESTAMP}.log"

exec > >(tee -a "$LOG_FILE") 2>&1

log() {
    local level="$1"
    shift
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] $*"
}

log_info()  { log "INFO"  "$@"; }
log_warn()  { log "WARN"  "$@"; }
log_error() { log "ERROR" "$@"; }
log_debug() { [[ "${DEBUG:-false}" == "true" ]] && log "DEBUG" "$@"; }

# ── Cleanup & Trap ─────────────────────────────────────────
cleanup() {
    local exit_code=$?
    rm -f "$LOCK_FILE"
    if [[ $exit_code -ne 0 ]]; then
        log_error "Backup failed with exit code $exit_code"
        send_notification "failure" "Backup failed with exit code $exit_code. See $LOG_FILE"
    fi
    exit $exit_code
}
trap cleanup EXIT INT TERM

# ── Lock Mechanism ─────────────────────────────────────────
acquire_lock() {
    if [[ -f "$LOCK_FILE" ]]; then
        local lock_pid
        lock_pid=$(cat "$LOCK_FILE" 2>/dev/null) || true
        if [[ -n "$lock_pid" ]] && kill -0 "$lock_pid" 2>/dev/null; then
            log_error "Another backup process is running (PID: $lock_pid)"
            exit 1
        else
            log_warn "Removing stale lock file"
            rm -f "$LOCK_FILE"
        fi
    fi
    echo $$ > "$LOCK_FILE"
    log_info "Lock acquired (PID: $$)"
}

# ── Dependency Checks ─────────────────────────────────────
check_dependencies() {
    local missing=()
    for cmd in pg_dump psql redis-cli date sha256sum; do
        if ! command -v "$cmd" &>/dev/null; then
            missing+=("$cmd")
        fi
    done

    if [[ "$S3_ENABLED" == "true" ]]; then
        if ! command -v aws &>/dev/null; then
            missing+=("aws")
        fi
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing dependencies: ${missing[*]}"
        exit 1
    fi
    log_info "All dependencies satisfied"
}

# ── Pre-flight Checks ─────────────────────────────────────
preflight_checks() {
    # Check PostgreSQL connectivity
    if ! PGPASSWORD="$PG_PASSWORD" psql \
        -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" \
        -c "SELECT 1;" &>/dev/null; then
        log_error "Cannot connect to PostgreSQL at ${PG_HOST}:${PG_PORT}"
        exit 1
    fi
    log_info "PostgreSQL connection verified"

    # Check Redis connectivity
    local redis_auth=()
    if [[ -n "$REDIS_PASSWORD" ]]; then
        redis_auth=(-a "$REDIS_PASSWORD" --no-auth-warning)
    fi
    if ! redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" "${redis_auth[@]}" PING &>/dev/null; then
        log_error "Cannot connect to Redis at ${REDIS_HOST}:${REDIS_PORT}"
        exit 1
    fi
    log_info "Redis connection verified"

    # Check S3 bucket if enabled
    if [[ "$S3_ENABLED" == "true" ]]; then
        if [[ -z "$S3_BUCKET" ]]; then
            log_error "S3_ENABLED=true but S3_BUCKET is not set"
            exit 1
        fi
        if ! aws s3 ls "s3://${S3_BUCKET}" &>/dev/null; then
            log_error "Cannot access S3 bucket: ${S3_BUCKET}"
            exit 1
        fi
        log_info "S3 bucket verified: ${S3_BUCKET}"
    fi

    # Check disk space (need at least 1GB free)
    local available_kb
    available_kb=$(df -k "$BACKUP_BASE_DIR" | awk 'NR==2 {print $4}')
    if [[ $available_kb -lt 1048576 ]]; then
        log_error "Insufficient disk space: ${available_kb}KB available (need 1GB)"
        exit 1
    fi
    log_info "Disk space check passed"
}

# ── PostgreSQL Backup ─────────────────────────────────────
backup_postgres() {
    local backup_dir="$1"
    local pg_backup_file="${backup_dir}/postgresql_${TIMESTAMP}.dump"
    local start_time end_time duration

    log_info "Starting PostgreSQL backup..."
    start_time=$(date +%s)

    local dump_opts=(-h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB")
    case "$BACKUP_FORMAT" in
        custom)    dump_opts+=(-Fc) ;;
        plain)     dump_opts+=(-Fp) ;;
        directory) dump_opts+=(-Fd -j 4) ;;
    esac

    # Add verbose and other safety options
    dump_opts+=(--verbose --no-owner --no-privileges)

    if ! PGPASSWORD="$PG_PASSWORD" pg_dump "${dump_opts[@]}" \
        -f "$pg_backup_file" 2>>"$LOG_FILE"; then
        log_error "PostgreSQL backup failed"
        return 1
    fi

    end_time=$(date +%s)
    duration=$((end_time - start_time))

    # Generate checksum
    sha256sum "$pg_backup_file" > "${pg_backup_file}.sha256"

    local file_size
    file_size=$(du -h "$pg_backup_file" | cut -f1)
    log_info "PostgreSQL backup completed: ${pg_backup_file} (${file_size}, ${duration}s)"

    echo "$pg_backup_file"
}

# ── Redis Backup ──────────────────────────────────────────
backup_redis() {
    local backup_dir="$1"
    local redis_backup_file="${backup_dir}/redis_${TIMESTAMP}.rdb"
    local start_time end_time duration

    log_info "Starting Redis backup..."
    start_time=$(date +%s)

    local redis_auth=()
    if [[ -n "$REDIS_PASSWORD" ]]; then
        redis_auth=(-a "$REDIS_PASSWORD" --no-auth-warning)
    fi

    # Use BGSAVE for non-blocking backup, then copy the RDB file
    if ! redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" "${redis_auth[@]}" BGSAVE &>/dev/null; then
        log_error "Redis BGSAVE failed"
        return 1
    fi

    # Wait for BGSAVE to complete
    local max_wait=300
    local waited=0
    while true; do
        local last_save
        last_save=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" "${redis_auth[@]}" LASTSAVE)
        sleep 2
        local new_save
        new_save=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" "${redis_auth[@]}" LASTSAVE)
        if [[ "$new_save" != "$last_save" ]]; then
            break
        fi
        waited=$((waited + 2))
        if [[ $waited -ge $max_wait ]]; then
            log_warn "Redis BGSAVE wait timeout, proceeding with current RDB"
            break
        fi
    done

    # Find and copy the RDB file
    local rdb_dir rdb_filename
    rdb_dir=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" "${redis_auth[@]}" CONFIG GET dir | tail -1)
    rdb_filename=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" "${redis_auth[@]}" CONFIG GET dbfilename | tail -1)

    if [[ -z "$rdb_dir" || -z "$rdb_filename" ]]; then
        log_error "Could not determine Redis RDB path"
        return 1
    fi

    local rdb_path="${rdb_dir}/${rdb_filename}"
    if [[ ! -f "$rdb_path" ]]; then
        log_error "Redis RDB file not found: $rdb_path"
        return 1
    fi

    cp "$rdb_path" "$redis_backup_file"

    end_time=$(date +%s)
    duration=$((end_time - start_time))

    # Generate checksum
    sha256sum "$redis_backup_file" > "${redis_backup_file}.sha256"

    local file_size
    file_size=$(du -h "$redis_backup_file" | cut -f1)
    log_info "Redis backup completed: ${redis_backup_file} (${file_size}, ${duration}s)"

    echo "$redis_backup_file"
}

# ── S3 Upload ─────────────────────────────────────────────
upload_to_s3() {
    local backup_dir="$1"
    local s3_key_prefix="${S3_PREFIX}/${DATE_PREFIX}"

    log_info "Uploading backups to S3..."

    # Upload all files in the backup directory
    if ! aws s3 sync "$backup_dir" "s3://${S3_BUCKET}/${s3_key_prefix}/" \
        --storage-class "$S3_STORAGE_CLASS" \
        --region "$S3_REGION" \
        --only-show-errors; then
        log_error "S3 upload failed"
        return 1
    fi

    log_info "S3 upload completed: s3://${S3_BUCKET}/${s3_key_prefix}/"
}

# ── Backup Rotation / Pruning ─────────────────────────────
prune_local_backups() {
    log_info "Pruning local backups older than ${BACKUP_RETENTION_DAYS} days..."

    local deleted=0
    while IFS= read -r -d '' file; do
        rm -f "$file"
        ((deleted++)) || true
    done < <(find "$BACKUP_BASE_DIR" -type f -mtime +"$BACKUP_RETENTION_DAYS" -print0 2>/dev/null)

    log_info "Pruned $deleted old local backup files"
}

prune_s3_backups() {
    if [[ "$S3_ENABLED" != "true" ]]; then
        return 0
    fi

    log_info "Pruning S3 backups older than ${BACKUP_RETENTION_DAYS} days..."

    local cutoff_date
    cutoff_date=$(date -d "${BACKUP_RETENTION_DAYS} days ago" +%Y-%m-%d 2>/dev/null || \
                  date -v "-${BACKUP_RETENTION_DAYS}d" +%Y-%m-%d)

    # List and delete old S3 objects
    aws s3api list-objects-v2 \
        --bucket "$S3_BUCKET" \
        --prefix "$S3_PREFIX/" \
        --query "Contents[?LastModified<='${cutoff_date}'].Key" \
        --output text 2>/dev/null | \
    while IFS= read -r key; do
        if [[ -n "$key" && "$key" != "None" ]]; then
            aws s3 rm "s3://${S3_BUCKET}/${key}" --region "$S3_REGION" &>/dev/null || true
            log_info "Deleted old S3 object: $key"
        fi
    done
}

# ── Notification ──────────────────────────────────────────
send_notification() {
    local status="$1"
    local message="$2"

    if [[ -z "$SLACK_WEBHOOK_URL" ]]; then
        return 0
    fi

    local color="danger"
    [[ "$status" == "success" ]] && color="good"

    local payload
    payload=$(cat <<EOF
{
    "attachments": [{
        "color": "${color}",
        "title": "UGC Marketplace Backup ${status}",
        "text": "${message}",
        "fields": [
            {"title": "Timestamp", "value": "${TIMESTAMP}", "short": true},
            {"title": "Host", "value": "$(hostname)", "short": true},
            {"title": "Log", "value": "${LOG_FILE}", "short": false}
        ],
        "footer": "ugc-marketplace backup",
        "ts": $(date +%s)
    }]
}
EOF
)

    curl -s -X POST -H 'Content-type: application/json' \
        --data "$payload" "$SLACK_WEBHOOK_URL" &>/dev/null || true
}

# ── Main ──────────────────────────────────────────────────
main() {
    log_info "=========================================="
    log_info "UGC Marketplace Backup Started"
    log_info "Timestamp: $TIMESTAMP"
    log_info "PostgreSQL: ${PG_HOST}:${PG_PORT}/${PG_DB}"
    log_info "Redis: ${REDIS_HOST}:${REDIS_PORT}"
    log_info "S3 Enabled: $S3_ENABLED"
    log_info "=========================================="

    acquire_lock
    check_dependencies
    preflight_checks

    # Create backup directory
    local backup_dir="${BACKUP_BASE_DIR}/${DATE_PREFIX}"
    mkdir -p "$backup_dir"

    # Perform backups
    local pg_backup redis_backup
    pg_backup=$(backup_postgres "$backup_dir")
    redis_backup=$(backup_redis "$backup_dir")

    # Upload to S3 if enabled
    if [[ "$S3_ENABLED" == "true" ]]; then
        upload_to_s3 "$backup_dir"
    fi

    # Prune old backups
    prune_local_backups
    prune_s3_backups

    # Success notification
    if [[ "$NOTIFY_ON_SUCCESS" == "true" ]]; then
        send_notification "success" "Backup completed successfully. PG: ${pg_backup}, Redis: ${redis_backup}"
    fi

    log_info "=========================================="
    log_info "Backup completed successfully"
    log_info "PostgreSQL: $pg_backup"
    log_info "Redis: $redis_backup"
    log_info "=========================================="
}

main "$@"
