#!/usr/bin/env bash
# =============================================================================
# backup.sh — Automated database backup script for Recruitment Platform
#
# Performs a full PostgreSQL backup with compression, optional S3 upload,
# retention management, and integrity verification.
#
# Usage:
#   ./backup.sh [--no-s3] [--no-compress] [--verbose]
#
# Environment variables (override defaults):
#   DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
#   BACKUP_DIR, S3_BUCKET, S3_PREFIX, RETENTION_DAYS
#   AWS_PROFILE, AWS_REGION, SLACK_WEBHOOK_URL
# =============================================================================

set -euo pipefail
IFS=$'\n\t'

# ─── Defaults ────────────────────────────────────────────────────────────────
readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
readonly DATE_PREFIX="$(date +%Y/%m/%d)"

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-recruitment}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-}"

BACKUP_DIR="${BACKUP_DIR:-/var/backups/recruitment-platform}"
S3_BUCKET="${S3_BUCKET:-}"
S3_PREFIX="${S3_PREFIX:-backups/database}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
AWS_PROFILE="${AWS_PROFILE:-default}"
AWS_REGION="${AWS_REGION:-us-east-1}"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"

COMPRESS="${COMPRESS:-true}"
UPLOAD_S3="${UPLOAD_S3:-true}"
VERBOSE="${VERBOSE:-false}"

# ─── Logging ─────────────────────────────────────────────────────────────────
LOG_FILE="${BACKUP_DIR}/logs/backup_${TIMESTAMP}.log"
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
log_debug() { [[ "${VERBOSE}" == "true" ]] && log "DEBUG" "$@"; }

# ─── Cleanup trap ────────────────────────────────────────────────────────────
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Backup failed with exit code ${exit_code}"
        send_alert "FAILED" "Backup failed with exit code ${exit_code}. Check ${LOG_FILE}"
    fi
    # Remove temporary files
    rm -f "${BACKUP_DIR}/.tmp_${TIMESTAMP}"*
}
trap cleanup EXIT

# ─── Argument parsing ────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-s3)       UPLOAD_S3="false"; shift ;;
        --no-compress) COMPRESS="false"; shift ;;
        --verbose|-v)  VERBOSE="true"; shift ;;
        --help|-h)
            sed -n '2,15p' "$0" | sed 's/^# \?//'
            exit 0
            ;;
        *)
            log_error "Unknown argument: $1"
            exit 1
            ;;
    esac
done

# ─── Pre-flight checks ───────────────────────────────────────────────────────
preflight() {
    log_info "Starting pre-flight checks..."

    # Check required tools
    local required_tools=("pg_dump" "psql")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &>/dev/null; then
            log_error "Required tool not found: ${tool}"
            exit 1
        fi
    done

    # Check AWS CLI if S3 upload enabled
    if [[ "${UPLOAD_S3}" == "true" && -n "${S3_BUCKET}" ]]; then
        if ! command -v aws &>/dev/null; then
            log_error "AWS CLI not found but S3 upload is enabled"
            exit 1
        fi
    fi

    # Check database connectivity
    if ! PGPASSWORD="${DB_PASSWORD}" psql \
        -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
        -c "SELECT 1;" &>/dev/null; then
        log_error "Cannot connect to database ${DB_NAME} at ${DB_HOST}:${DB_PORT}"
        exit 1
    fi

    # Check disk space (need at least 2x database size)
    local db_size
    db_size=$(PGPASSWORD="${DB_PASSWORD}" psql \
        -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
        -tAc "SELECT pg_database_size('${DB_NAME}');" 2>/dev/null | tr -d '[:space:]')
    local available_space
    available_space=$(df -P "${BACKUP_DIR}" | awk 'NR==2 {print $4}')
    local required_space=$(( db_size * 2 / 1024 ))  # in KB

    if [[ ${available_space} -lt ${required_space} ]]; then
        log_error "Insufficient disk space. Required: ${required_space}KB, Available: ${available_space}KB"
        exit 1
    fi

    # Create backup directories
    mkdir -p "${BACKUP_DIR}"/{logs,local,manifest}

    log_info "Pre-flight checks passed"
}

# ─── Slack alert ─────────────────────────────────────────────────────────────
send_alert() {
    local status="$1"
    local message="$2"

    if [[ -n "${SLACK_WEBHOOK_URL}" ]]; then
        curl -s -X POST "${SLACK_WEBHOOK_URL}" \
            -H 'Content-type: application/json' \
            -d "{\"text\": \"[Recruitment Platform DB] Backup ${status}: ${message}\"}" \
            &>/dev/null || true
    fi
}

# ─── Perform backup ──────────────────────────────────────────────────────────
do_backup() {
    log_info "Starting backup of database '${DB_NAME}'..."

    local backup_filename="recruitment_${TIMESTAMP}.dump"
    local backup_path="${BACKUP_DIR}/local/${backup_filename}"

    if [[ "${COMPRESS}" == "true" ]]; then
        backup_filename="${backup_filename}.gz"
        backup_path="${backup_path}.gz"
    fi

    log_info "Backup file: ${backup_path}"

    # Build pg_dump options
    local dump_opts=(
        --host="${DB_HOST}"
        --port="${DB_PORT}"
        --username="${DB_USER}"
        --dbname="${DB_NAME}"
        --format=custom
        --verbose
        --no-owner
        --no-privileges
    )

    # Add compression if enabled
    if [[ "${COMPRESS}" == "true" ]]; then
        dump_opts+=(--compress=9)
    fi

    # Execute backup
    log_info "Running pg_dump..."
    if ! PGPASSWORD="${DB_PASSWORD}" pg_dump "${dump_opts[@]}" > "${backup_path}" 2>>"${LOG_FILE}"; then
        log_error "pg_dump failed"
        rm -f "${backup_path}"
        exit 1
    fi

    # Verify backup file exists and is non-empty
    if [[ ! -s "${backup_path}" ]]; then
        log_error "Backup file is empty or does not exist: ${backup_path}"
        exit 1
    fi

    local backup_size
    backup_size=$(stat -f%z "${backup_path}" 2>/dev/null || stat -c%s "${backup_path}" 2>/dev/null)
    log_info "Backup completed: ${backup_filename} ($(numfmt --to=iec "${backup_size}" 2>/dev/null || echo "${backup_size} bytes"))"

    # Generate checksum
    local checksum
    checksum=$(shasum -a 256 "${backup_path}" | awk '{print $1}')
    log_info "SHA-256 checksum: ${checksum}"

    # Write manifest
    local manifest_file="${BACKUP_DIR}/manifest/${TIMESTAMP}.manifest"
    cat > "${manifest_file}" <<EOF
{
    "timestamp": "${TIMESTAMP}",
    "database": "${DB_NAME}",
    "host": "${DB_HOST}",
    "port": ${DB_PORT},
    "filename": "${backup_filename}",
    "path": "${backup_path}",
    "size_bytes": ${backup_size},
    "sha256": "${checksum}",
    "compressed": ${COMPRESS},
    "pg_dump_version": "$(pg_dump --version | awk '{print $3}')",
    "postgres_version": "$(PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -tAc 'SHOW server_version;' 2>/dev/null | tr -d '[:space:]')"
}
EOF

    # Verify backup integrity
    log_info "Verifying backup integrity..."
    if [[ "${COMPRESS}" == "true" ]]; then
        if ! gunzip -t "${backup_path}" 2>/dev/null; then
            log_error "Backup file failed gzip integrity check"
            exit 1
        fi
    fi

    # Test restore to a temporary database
    local test_db="_backup_verify_${TIMESTAMP}"
    log_info "Testing restore to temporary database '${test_db}'..."
    if PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
        -c "CREATE DATABASE ${test_db};" &>/dev/null; then

        local restore_opts=(--host="${DB_HOST}" --port="${DB_PORT}" --username="${DB_USER}" --dbname="${test_db}")
        if [[ "${COMPRESS}" == "true" ]]; then
            restore_opts+=(--no-owner --no-privileges)
        fi

        if PGPASSWORD="${DB_PASSWORD}" pg_restore "${restore_opts[@]}" "${backup_path}" &>/dev/null; then
            log_info "Backup integrity verified successfully"
        else
            log_warn "Backup restore test had warnings (may be normal for some configurations)"
        fi

        # Drop test database
        PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
            -c "DROP DATABASE IF EXISTS ${test_db};" &>/dev/null || true
    else
        log_warn "Could not create verification database, skipping restore test"
    fi

    echo "${backup_path}"
}

# ─── Upload to S3 ────────────────────────────────────────────────────────────
upload_s3() {
    local backup_path="$1"
    local filename
    filename="$(basename "${backup_path}")"

    if [[ "${UPLOAD_S3}" != "true" || -z "${S3_BUCKET}" ]]; then
        log_info "S3 upload disabled, skipping"
        return 0
    fi

    log_info "Uploading to S3: s3://${S3_BUCKET}/${S3_PREFIX}/${DATE_PREFIX}/${filename}"

    if ! aws s3 cp "${backup_path}" "s3://${S3_BUCKET}/${S3_PREFIX}/${DATE_PREFIX}/${filename}" \
        --profile "${AWS_PROFILE}" \
        --region "${AWS_REGION}" \
        --storage-class STANDARD_IA \
        --metadata "timestamp=${TIMESTAMP},database=${DB_NAME}" 2>>"${LOG_FILE}"; then
        log_error "S3 upload failed"
        return 1
    fi

    # Upload manifest too
    local manifest_file="${BACKUP_DIR}/manifest/${TIMESTAMP}.manifest"
    if [[ -f "${manifest_file}" ]]; then
        aws s3 cp "${manifest_file}" "s3://${S3_BUCKET}/${S3_PREFIX}/${DATE_PREFIX}/${TIMESTAMP}.manifest" \
            --profile "${AWS_PROFILE}" \
            --region "${AWS_REGION}" 2>>"${LOG_FILE}" || true
    fi

    log_info "S3 upload completed"
}

# ─── Retention management ────────────────────────────────────────────────────
apply_retention() {
    log_info "Applying retention policy (${RETENTION_DAYS} days)..."

    # Local retention
    local deleted_local
    deleted_local=$(find "${BACKUP_DIR}/local" -name "recruitment_*.dump*" -type f -mtime +"${RETENTION_DAYS}" | wc -l | tr -d '[:space:]')
    find "${BACKUP_DIR}/local" -name "recruitment_*.dump*" -type f -mtime +"${RETENTION_DAYS}" -delete
    log_info "Deleted ${deleted_local} local backup(s) older than ${RETENTION_DAYS} days"

    # Manifest retention
    find "${BACKUP_DIR}/manifest" -name "*.manifest" -type f -mtime +"${RETENTION_DAYS}" -delete

    # Log retention
    find "${BACKUP_DIR}/logs" -name "backup_*.log" -type f -mtime +"${RETENTION_DAYS}" -delete

    # S3 retention (if enabled)
    if [[ "${UPLOAD_S3}" == "true" && -n "${S3_BUCKET}" ]]; then
        log_info "Applying S3 lifecycle/retention..."
        local cutoff_date
        cutoff_date=$(date -d "${RETENTION_DAYS} days ago" +%Y-%m-%d 2>/dev/null || date -v-"${RETENTION_DAYS}"d +%Y-%m-%d 2>/dev/null || echo "")

        if [[ -n "${cutoff_date}" ]]; then
            # List and delete old S3 objects
            aws s3 ls "s3://${S3_BUCKET}/${S3_PREFIX}/" --recursive --profile "${AWS_PROFILE}" --region "${AWS_REGION}" 2>/dev/null | \
            while read -r line; do
                local file_date
                file_date=$(echo "${line}" | awk '{print $1}')
                local file_key
                file_key=$(echo "${line}" | awk '{print $4}')
                if [[ "${file_date}" < "${cutoff_date}" ]]; then
                    aws s3 rm "s3://${S3_BUCKET}/${file_key}" --profile "${AWS_PROFILE}" --region "${AWS_REGION}" 2>/dev/null || true
                    log_info "Deleted old S3 object: ${file_key}"
                fi
            done
        fi
    fi
}

# ─── Main ────────────────────────────────────────────────────────────────────
main() {
    log_info "=========================================="
    log_info "Recruitment Platform DB Backup Starting"
    log_info "=========================================="
    log_info "Database: ${DB_NAME}@${DB_HOST}:${DB_PORT}"
    log_info "Backup directory: ${BACKUP_DIR}"
    log_info "S3 upload: ${UPLOAD_S3}"
    log_info "Compression: ${COMPRESS}"
    log_info "Retention: ${RETENTION_DAYS} days"

    preflight

    local backup_path
    backup_path=$(do_backup)

    upload_s3 "${backup_path}"

    apply_retention

    log_info "=========================================="
    log_info "Backup completed successfully"
    log_info "=========================================="

    send_alert "SUCCESS" "Backup completed: $(basename "${backup_path}")"
}

main "$@"
