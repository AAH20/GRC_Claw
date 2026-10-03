#!/usr/bin/env bash
# =============================================================================
# restore.sh — Database restore script for Recruitment Platform
#
# Restores a PostgreSQL backup from local file or S3, with pre-restore
# safety checks, automatic backup of current state, and verification.
#
# Usage:
#   ./restore.sh --file <path> [--no-verify] [--force]
#   ./restore.sh --s3 <s3-url> [--no-verify] [--force]
#   ./restore.sh --latest-s3 [--no-verify] [--force]
#
# Environment variables:
#   DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
#   BACKUP_DIR, S3_BUCKET, S3_PREFIX, AWS_PROFILE, AWS_REGION
# =============================================================================

set -euo pipefail
IFS=$'\n\t'

# ─── Defaults ────────────────────────────────────────────────────────────────
readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-recruitment}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-}"

BACKUP_DIR="${BACKUP_DIR:-/var/backups/recruitment-platform}"
S3_BUCKET="${S3_BUCKET:-}"
S3_PREFIX="${S3_PREFIX:-backups/database}"
AWS_PROFILE="${AWS_PROFILE:-default}"
AWS_REGION="${AWS_REGION:-us-east-1}"

RESTORE_FILE=""
RESTORE_SOURCE=""  # "local", "s3", "latest-s3"
VERIFY_RESTORE="${VERIFY_RESTORE:-true}"
FORCE_RESTORE="${FORCE_RESTORE:-false}"

# ─── Logging ─────────────────────────────────────────────────────────────────
LOG_FILE="${BACKUP_DIR}/logs/restore_${TIMESTAMP}.log"
mkdir -p "${BACKUP_DIR}/logs"

log() {
    local level="$1"
    shift
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] [${level}] $*"
    echo "${msg}" | tee -a "${LOG_FILE}"
}

log_info()  { log "INFO" "$@"; }
log_warn()  { log "WARN" "$@"; }
log_error() { log "ERROR" "$@"; }

# ─── Cleanup trap ────────────────────────────────────────────────────────────
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Restore failed with exit code ${exit_code}"
    fi
    # Clean up temporary download file if it exists
    if [[ -n "${TEMP_DOWNLOAD:-}" && -f "${TEMP_DOWNLOAD}" ]]; then
        rm -f "${TEMP_DOWNLOAD}"
    fi
}
trap cleanup EXIT

# ─── Usage ───────────────────────────────────────────────────────────────────
usage() {
    cat <<EOF
Usage: ${SCRIPT_NAME} [OPTIONS]

Required (one of):
  --file <path>       Restore from local backup file
  --s3 <s3-url>       Restore from S3 URL (e.g., s3://bucket/path/to/backup.dump)
  --latest-s3         Restore from the latest backup in S3

Optional:
  --no-verify         Skip post-restore verification
  --force             Skip confirmation prompt (DANGEROUS)
  --target-db <name>  Restore to a different database name
  --help              Show this help message

Examples:
  ${SCRIPT_NAME} --file /var/backups/recruitment-platform/local/recruitment_20240101_120000.dump.gz
  ${SCRIPT_NAME} --s3 s3://my-bucket/backups/database/2024/01/01/recruitment_20240101_120000.dump.gz
  ${SCRIPT_NAME} --latest-s3 --force
EOF
    exit 0
}

# ─── Argument parsing ────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --file)
            RESTORE_FILE="$2"
            RESTORE_SOURCE="local"
            shift 2
            ;;
        --s3)
            RESTORE_FILE="$2"
            RESTORE_SOURCE="s3"
            shift 2
            ;;
        --latest-s3)
            RESTORE_SOURCE="latest-s3"
            shift
            ;;
        --no-verify)
            VERIFY_RESTORE="false"
            shift
            ;;
        --force)
            FORCE_RESTORE="true"
            shift
            ;;
        --target-db)
            DB_NAME="$2"
            shift 2
            ;;
        --help|-h)
            usage
            ;;
        *)
            log_error "Unknown argument: $1"
            usage
            ;;
    esac
done

if [[ -z "${RESTORE_SOURCE}" ]]; then
    log_error "No restore source specified. Use --file, --s3, or --latest-s3"
    usage
fi

# ─── Pre-flight checks ───────────────────────────────────────────────────────
preflight() {
    log_info "Starting pre-flight checks..."

    # Check required tools
    local required_tools=("pg_restore" "psql")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &>/dev/null; then
            log_error "Required tool not found: ${tool}"
            exit 1
        fi
    done

    # Check AWS CLI if needed
    if [[ "${RESTORE_SOURCE}" == "s3" || "${RESTORE_SOURCE}" == "latest-s3" ]]; then
        if ! command -v aws &>/dev/null; then
            log_error "AWS CLI not found but S3 restore is requested"
            exit 1
        fi
    fi

    # Check database connectivity
    if ! PGPASSWORD="${DB_PASSWORD}" psql \
        -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
        -c "SELECT 1;" &>/dev/null; then
        log_error "Cannot connect to PostgreSQL at ${DB_HOST}:${DB_PORT}"
        exit 1
    fi

    # Check if target database exists and has connections
    local db_exists
    db_exists=$(PGPASSWORD="${DB_PASSWORD}" psql \
        -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
        -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}';" 2>/dev/null | tr -d '[:space:]')

    if [[ "${db_exists}" == "1" ]]; then
        local active_connections
        active_connections=$(PGPASSWORD="${DB_PASSWORD}" psql \
            -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
            -tAc "SELECT count(*) FROM pg_stat_activity WHERE datname='${DB_NAME}' AND pid <> pg_backend_pid();" 2>/dev/null | tr -d '[:space:]')

        if [[ "${active_connections}" -gt 0 ]]; then
            log_warn "Database '${DB_NAME}' has ${active_connections} active connection(s)"
            if [[ "${FORCE_RESTORE}" != "true" ]]; then
                log_error "Use --force to restore anyway, or disconnect clients first"
                exit 1
            fi
        fi
    fi

    log_info "Pre-flight checks passed"
}

# ─── Download from S3 ───────────────────────────────────────────────────────
download_from_s3() {
    local s3_url="$1"
    local filename
    filename="$(basename "${s3_url}")"
    TEMP_DOWNLOAD="${BACKUP_DIR}/.tmp_restore_${TIMESTAMP}_${filename}"

    log_info "Downloading from S3: ${s3_url}"
    if ! aws s3 cp "${s3_url}" "${TEMP_DOWNLOAD}" \
        --profile "${AWS_PROFILE}" \
        --region "${AWS_REGION}" 2>>"${LOG_FILE}"; then
        log_error "S3 download failed"
        exit 1
    fi

    echo "${TEMP_DOWNLOAD}"
}

# ─── Find latest S3 backup ──────────────────────────────────────────────────
find_latest_s3() {
    log_info "Finding latest backup in S3..."

    if [[ -z "${S3_BUCKET}" ]]; then
        log_error "S3_BUCKET not set"
        exit 1
    fi

    local latest_key
    latest_key=$(aws s3 ls "s3://${S3_BUCKET}/${S3_PREFIX}/" --recursive \
        --profile "${AWS_PROFILE}" --region "${AWS_REGION}" 2>/dev/null | \
        grep "recruitment_.*\.dump" | sort | tail -1 | awk '{print $4}')

    if [[ -z "${latest_key}" ]]; then
        log_error "No backup found in s3://${S3_BUCKET}/${S3_PREFIX}/"
        exit 1
    fi

    log_info "Latest backup: s3://${S3_BUCKET}/${latest_key}"
    echo "s3://${S3_BUCKET}/${latest_key}"
}

# ─── Safety backup ───────────────────────────────────────────────────────────
safety_backup() {
    log_info "Creating safety backup of current database state..."

    local safety_file="${BACKUP_DIR}/local/pre_restore_${TIMESTAMP}.dump.gz"

    if PGPASSWORD="${DB_PASSWORD}" pg_dump \
        --host="${DB_HOST}" --port="${DB_PORT}" --username="${DB_USER}" \
        --dbname="${DB_NAME}" --format=custom --compress=9 > "${safety_file}" 2>>"${LOG_FILE}"; then
        log_info "Safety backup created: ${safety_file}"
    else
        log_warn "Safety backup failed, proceeding anyway (use --force to suppress this warning)"
        if [[ "${FORCE_RESTORE}" != "true" ]]; then
            log_error "Aborting restore due to safety backup failure"
            exit 1
        fi
    fi
}

# ─── Perform restore ─────────────────────────────────────────────────────────
do_restore() {
    local backup_path="$1"

    log_info "Starting restore of '${DB_NAME}' from: ${backup_path}"

    # Verify backup file
    if [[ ! -f "${backup_path}" ]]; then
        log_error "Backup file not found: ${backup_path}"
        exit 1
    fi

    if [[ ! -s "${backup_path}" ]]; then
        log_error "Backup file is empty: ${backup_path}"
        exit 1
    fi

    # Check file integrity
    if [[ "${backup_path}" == *.gz ]]; then
        log_info "Verifying gzip integrity..."
        if ! gunzip -t "${backup_path}" 2>/dev/null; then
            log_error "Backup file failed gzip integrity check"
            exit 1
        fi
    fi

    # Terminate existing connections to target database
    log_info "Terminating existing connections to '${DB_NAME}'..."
    PGPASSWORD="${DB_PASSWORD}" psql \
        -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
        -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${DB_NAME}' AND pid <> pg_backend_pid();" \
        &>/dev/null || true

    # Drop and recreate database
    log_info "Dropping and recreating database '${DB_NAME}'..."
    PGPASSWORD="${DB_PASSWORD}" psql \
        -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
        -c "DROP DATABASE IF EXISTS ${DB_NAME};" &>/dev/null

    PGPASSWORD="${DB_PASSWORD}" psql \
        -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
        -c "CREATE DATABASE ${DB_NAME};" &>/dev/null

    # Restore
    log_info "Running pg_restore..."
    local restore_opts=(
        --host="${DB_HOST}"
        --port="${DB_PORT}"
        --username="${DB_USER}"
        --dbname="${DB_NAME}"
        --no-owner
        --no-privileges
        --verbose
    )

    if ! PGPASSWORD="${DB_PASSWORD}" pg_restore "${restore_opts[@]}" "${backup_path}" 2>>"${LOG_FILE}"; then
        log_warn "pg_restore completed with warnings (check log for details)"
    fi

    log_info "Restore completed"
}

# ─── Verify restore ──────────────────────────────────────────────────────────
verify_restore() {
    if [[ "${VERIFY_RESTORE}" != "true" ]]; then
        log_info "Verification skipped (--no-verify)"
        return 0
    fi

    log_info "Verifying restored database..."

    # Check database is accessible
    if ! PGPASSWORD="${DB_PASSWORD}" psql \
        -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
        -c "SELECT 1;" &>/dev/null; then
        log_error "Cannot connect to restored database"
        return 1
    fi

    # Get table count
    local table_count
    table_count=$(PGPASSWORD="${DB_PASSWORD}" psql \
        -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
        -tAc "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | tr -d '[:space:]')

    log_info "Restored database has ${table_count} table(s)"

    if [[ "${table_count}" -eq 0 ]]; then
        log_error "No tables found in restored database"
        return 1
    fi

    # Check critical tables exist
    local critical_tables=("users" "candidates" "jobs" "applications")
    local missing_tables=()
    for table in "${critical_tables[@]}"; do
        local exists
        exists=$(PGPASSWORD="${DB_PASSWORD}" psql \
            -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
            -tAc "SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='${table}';" 2>/dev/null | tr -d '[:space:]')
        if [[ "${exists}" != "1" ]]; then
            missing_tables+=("${table}")
        fi
    done

    if [[ ${#missing_tables[@]} -gt 0 ]]; then
        log_warn "Missing critical tables: ${missing_tables[*]}"
    else
        log_info "All critical tables present"
    fi

    # Get database size
    local db_size
    db_size=$(PGPASSWORD="${DB_PASSWORD}" psql \
        -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
        -tAc "SELECT pg_database_size('${DB_NAME}');" 2>/dev/null | tr -d '[:space:]')
    log_info "Restored database size: $(numfmt --to=iec "${db_size}" 2>/dev/null || echo "${db_size} bytes")"

    log_info "Verification completed successfully"
}

# ─── Confirmation prompt ─────────────────────────────────────────────────────
confirm_restore() {
    if [[ "${FORCE_RESTORE}" == "true" ]]; then
        return 0
    fi

    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    ⚠️  WARNING  ⚠️                           ║"
    echo "║                                                              ║"
    echo "║  You are about to RESTORE the database '${DB_NAME}'          ║"
    echo "║  This will DELETE all existing data!                         ║"
    echo "║                                                              ║"
    echo "║  Source: ${RESTORE_SOURCE}"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    read -rp "Type 'RESTORE' to confirm: " confirm

    if [[ "${confirm}" != "RESTORE" ]]; then
        log_info "Restore cancelled by user"
        exit 0
    fi
}

# ─── Main ────────────────────────────────────────────────────────────────────
main() {
    log_info "=========================================="
    log_info "Recruitment Platform DB Restore Starting"
    log_info "=========================================="
    log_info "Target database: ${DB_NAME}@${DB_HOST}:${DB_PORT}"
    log_info "Restore source: ${RESTORE_SOURCE}"

    preflight

    local backup_path=""

    case "${RESTORE_SOURCE}" in
        local)
            backup_path="${RESTORE_FILE}"
            ;;
        s3)
            backup_path=$(download_from_s3 "${RESTORE_FILE}")
            ;;
        latest-s3)
            local s3_url
            s3_url=$(find_latest_s3)
            backup_path=$(download_from_s3 "${s3_url}")
            ;;
    esac

    confirm_restore

    safety_backup

    do_restore "${backup_path}"

    verify_restore

    log_info "=========================================="
    log_info "Restore completed successfully"
    log_info "=========================================="
}

main "$@"
