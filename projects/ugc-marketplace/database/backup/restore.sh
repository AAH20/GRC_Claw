#!/usr/bin/env bash
# ============================================================
# UGC Marketplace — Database Restore Script
# Restores PostgreSQL and Redis from local or S3 backups.
# Supports point-in-time selection and dry-run mode.
# ============================================================
set -euo pipefail
IFS=$'\n\t'

# ── Configuration ──────────────────────────────────────────
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "$0")"

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

# S3 settings
readonly S3_ENABLED="${S3_ENABLED:-false}"
readonly S3_BUCKET="${S3_BUCKET:-}"
readonly S3_PREFIX="${S3_PREFIX:-ugc-marketplace/backups}"
readonly S3_REGION="${S3_REGION:-us-east-1}"

# ── Logging ────────────────────────────────────────────────
LOG_DIR="${BACKUP_BASE_DIR}/logs"
mkdir -p "$LOG_DIR"
readonly LOG_FILE="${LOG_DIR}/restore_$(date +%Y%m%d_%H%M%S).log"

exec > >(tee -a "$LOG_FILE") 2>&1

log() {
    local level="$1"
    shift
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] $*"
}

log_info()  { log "INFO"  "$@"; }
log_warn()  { log "WARN"  "$@"; }
log_error() { log "ERROR" "$@"; }

# ── Usage ─────────────────────────────────────────────────
usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Restore UGC Marketplace databases from backup.

OPTIONS:
    -f, --file PATH          Specific backup file to restore from
    -d, --date DATE          Restore from date (YYYY-MM-DD or YYYYMMDD)
    -t, --type TYPE          Restore type: postgres|redis|all (default: all)
    -s, --s3                 Download backup from S3 first
    -n, --dry-run            Show what would be done without executing
    -y, --yes                Skip confirmation prompts
    -h, --help               Show this help message

EXAMPLES:
    $0 --type postgres --date 2024-01-15
    $0 --file /var/backups/ugc-marketplace/2024/01/15/postgresql_20240115_120000.dump
    $0 --s3 --date 2024-01-15 --type all
    $0 --dry-run --date 2024-01-15

EOF
    exit 0
}

# ── Argument Parsing ──────────────────────────────────────
BACKUP_FILE=""
BACKUP_DATE=""
RESTORE_TYPE="all"
USE_S3=false
DRY_RUN=false
AUTO_YES=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -f|--file)      BACKUP_FILE="$2"; shift 2 ;;
        -d|--date)      BACKUP_DATE="$2"; shift 2 ;;
        -t|--type)      RESTORE_TYPE="$2"; shift 2 ;;
        -s|--s3)        USE_S3=true; shift ;;
        -n|--dry-run)   DRY_RUN=true; shift ;;
        -y|--yes)       AUTO_YES=true; shift ;;
        -h|--help)      usage ;;
        *)              log_error "Unknown option: $1"; usage ;;
    esac
done

# ── Dependency Checks ─────────────────────────────────────
check_dependencies() {
    local missing=()
    for cmd in pg_restore psql redis-cli; do
        if ! command -v "$cmd" &>/dev/null; then
            missing+=("$cmd")
        fi
    done

    if [[ "$USE_S3" == "true" ]] && ! command -v aws &>/dev/null; then
        missing+=("aws")
    fi

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing dependencies: ${missing[*]}"
        exit 1
    fi
}

# ── Find Backup File ──────────────────────────────────────
find_backup_file() {
    local search_date="$1"
    local backup_type="$2"

    # Normalize date format
    search_date="${search_date//-/}"

    local pattern
    case "$backup_type" in
        postgres) pattern="postgresql_${search_date}_*.dump" ;;
        redis)    pattern="redis_${search_date}_*.rdb" ;;
        *)        log_error "Invalid backup type: $backup_type"; exit 1 ;;
    esac

    local found_file
    found_file=$(find "$BACKUP_BASE_DIR" -name "$pattern" -type f | sort -r | head -1)

    if [[ -z "$found_file" ]]; then
        log_error "No $backup_type backup found for date: $search_date"
        exit 1
    fi

    echo "$found_file"
}

# ── Download from S3 ──────────────────────────────────────
download_from_s3() {
    local search_date="$1"
    local backup_type="$2"

    if [[ "$USE_S3" != "true" ]]; then
        return 0
    fi

    if [[ -z "$S3_BUCKET" ]]; then
        log_error "S3_BUCKET is not set"
        exit 1
    fi

    local date_path="${search_date:0:4}/${search_date:4:2}/${search_date:6:2}"
    local s3_url="s3://${S3_BUCKET}/${S3_PREFIX}/${date_path}/"

    log_info "Downloading backups from S3: $s3_url"

    local download_dir="${BACKUP_BASE_DIR}/${date_path}"
    mkdir -p "$download_dir"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would download from $s3_url to $download_dir"
        return 0
    fi

    if ! aws s3 sync "$s3_url" "$download_dir" --region "$S3_REGION" --only-show-errors; then
        log_error "S3 download failed"
        exit 1
    fi

    log_info "S3 download completed"
}

# ── Verify Checksum ───────────────────────────────────────
verify_checksum() {
    local backup_file="$1"

    local checksum_file="${backup_file}.sha256"
    if [[ ! -f "$checksum_file" ]]; then
        log_warn "No checksum file found for $backup_file, skipping verification"
        return 0
    fi

    log_info "Verifying checksum for $(basename "$backup_file")..."

    if ! sha256sum -c "$checksum_file" &>/dev/null; then
        log_error "Checksum verification FAILED for $backup_file"
        return 1
    fi

    log_info "Checksum verified"
}

# ── Restore PostgreSQL ────────────────────────────────────
restore_postgres() {
    local backup_file="$1"

    log_info "=========================================="
    log_info "Restoring PostgreSQL from: $backup_file"
    log_info "Target: ${PG_HOST}:${PG_PORT}/${PG_DB}"
    log_info "=========================================="

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would restore PostgreSQL from $backup_file"
        return 0
    fi

    # Verify checksum
    verify_checksum "$backup_file" || {
        log_error "Checksum verification failed, aborting restore"
        exit 1
    }

    # Terminate existing connections
    log_info "Terminating existing connections..."
    PGPASSWORD="$PG_PASSWORD" psql \
        -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d postgres \
        -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${PG_DB}' AND pid<>pg_backend_pid();" \
        &>/dev/null || true

    # Drop and recreate database
    log_info "Dropping and recreating database..."
    PGPASSWORD="$PG_PASSWORD" psql \
        -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d postgres \
        -c "DROP DATABASE IF EXISTS ${PG_DB};" &>/dev/null

    PGPASSWORD="$PG_PASSWORD" psql \
        -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d postgres \
        -c "CREATE DATABASE ${PG_DB} OWNER ${PG_USER};" &>/dev/null

    # Restore
    log_info "Restoring database..."
    local restore_opts=(-h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DB" --verbose)

    # Detect format and use appropriate tool
    if file "$backup_file" | grep -q "PostgreSQL custom database dump"; then
        if ! PGPASSWORD="$PG_PASSWORD" pg_restore "${restore_opts[@]}" "$backup_file" 2>>"$LOG_FILE"; then
            log_error "PostgreSQL restore failed"
            return 1
        fi
    elif file "$backup_file" | grep -q "ASCII text"; then
        if ! PGPASSWORD="$PG_PASSWORD" psql "${restore_opts[@]}" -f "$backup_file" >> "$LOG_FILE" 2>&1; then
            log_error "PostgreSQL restore failed"
            return 1
        fi
    else
        # Try pg_restore as default
        if ! PGPASSWORD="$PG_PASSWORD" pg_restore "${restore_opts[@]}" "$backup_file" 2>>"$LOG_FILE"; then
            log_error "PostgreSQL restore failed"
            return 1
        fi
    fi

    log_info "PostgreSQL restore completed successfully"
}

# ── Restore Redis ─────────────────────────────────────────
restore_redis() {
    local backup_file="$1"

    log_info "=========================================="
    log_info "Restoring Redis from: $backup_file"
    log_info "Target: ${REDIS_HOST}:${REDIS_PORT}"
    log_info "=========================================="

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY-RUN] Would restore Redis from $backup_file"
        return 0
    fi

    # Verify checksum
    verify_checksum "$backup_file" || {
        log_error "Checksum verification failed, aborting restore"
        exit 1
    }

    local redis_auth=()
    if [[ -n "$REDIS_PASSWORD" ]]; then
        redis_auth=(-a "$REDIS_PASSWORD" --no-auth-warning)
    fi

    # Get Redis RDB path
    local rdb_dir rdb_filename
    rdb_dir=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" "${redis_auth[@]}" CONFIG GET dir | tail -1)
    rdb_filename=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" "${redis_auth[@]}" CONFIG GET dbfilename | tail -1)

    if [[ -z "$rdb_dir" || -z "$rdb_filename" ]]; then
        log_error "Could not determine Redis RDB path"
        return 1
    fi

    # Flush current data
    log_info "Flushing current Redis data..."
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" "${redis_auth[@]}" FLUSHALL &>/dev/null

    # Copy backup to Redis directory
    local rdb_path="${rdb_dir}/${rdb_filename}"
    log_info "Copying backup to $rdb_path..."
    cp "$backup_file" "$rdb_path"

    # Restart Redis to load the RDB file
    log_info "Restarting Redis to load backup..."
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" "${redis_auth[@]}" SHUTDOWN NOSAVE &>/dev/null || true
    sleep 2

    # Start Redis (assumes systemd or supervisor)
    if command -v systemctl &>/dev/null; then
        systemctl restart redis || systemctl restart redis-server || true
    elif command -v service &>/dev/null; then
        service redis restart || service redis-server restart || true
    else
        log_warn "Could not restart Redis automatically. Please restart manually."
    fi

    # Wait for Redis to come back
    local max_wait=30
    local waited=0
    while ! redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" "${redis_auth[@]}" PING &>/dev/null; do
        sleep 1
        ((waited++)) || true
        if [[ $waited -ge $max_wait ]]; then
            log_error "Redis did not come back online after ${max_wait}s"
            return 1
        fi
    done

    log_info "Redis restore completed successfully"
}

# ── Confirmation ──────────────────────────────────────────
confirm_restore() {
    if [[ "$AUTO_YES" == "true" ]] || [[ "$DRY_RUN" == "true" ]]; then
        return 0
    fi

    echo ""
    echo "WARNING: This will DESTROY existing data and restore from backup."
    echo "Backup file: ${BACKUP_FILE:-<to be determined>}"
    echo "Restore type: $RESTORE_TYPE"
    echo ""
    read -rp "Are you sure you want to continue? (yes/no): " response

    if [[ "$response" != "yes" ]]; then
        log_info "Restore cancelled by user"
        exit 0
    fi
}

# ── Main ──────────────────────────────────────────────────
main() {
    log_info "=========================================="
    log_info "UGC Marketplace Restore Started"
    log_info "Type: $RESTORE_TYPE"
    log_info "Dry Run: $DRY_RUN"
    log_info "=========================================="

    check_dependencies

    # Determine backup files
    local pg_backup_file="" redis_backup_file=""

    if [[ -n "$BACKUP_FILE" ]]; then
        # Specific file provided
        if [[ "$RESTORE_TYPE" == "all" ]]; then
            log_error "Cannot use --file with --type all. Specify --type postgres or --type redis."
            exit 1
        fi
        if [[ "$RESTORE_TYPE" == "postgres" ]]; then
            pg_backup_file="$BACKUP_FILE"
        else
            redis_backup_file="$BACKUP_FILE"
        fi
    elif [[ -n "$BACKUP_DATE" ]]; then
        # Find by date
        if [[ "$RESTORE_TYPE" == "postgres" || "$RESTORE_TYPE" == "all" ]]; then
            download_from_s3 "$BACKUP_DATE" "postgres"
            pg_backup_file=$(find_backup_file "$BACKUP_DATE" "postgres")
        fi
        if [[ "$RESTORE_TYPE" == "redis" || "$RESTORE_TYPE" == "all" ]]; then
            download_from_s3 "$BACKUP_DATE" "redis"
            redis_backup_file=$(find_backup_file "$BACKUP_DATE" "redis")
        fi
    else
        log_error "Either --file or --date must be specified"
        usage
    fi

    # Confirm
    confirm_restore

    # Perform restores
    if [[ -n "$pg_backup_file" ]]; then
        restore_postgres "$pg_backup_file"
    fi

    if [[ -n "$redis_backup_file" ]]; then
        restore_redis "$redis_backup_file"
    fi

    log_info "=========================================="
    log_info "Restore completed successfully"
    log_info "=========================================="
}

main "$@"
