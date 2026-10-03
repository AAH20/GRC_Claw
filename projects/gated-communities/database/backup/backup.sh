#!/usr/bin/env bash
# =============================================================================
# backup.sh — Automated PostgreSQL Backup for Gated Communities
# =============================================================================
# Performs full database backup with pg_dump, compresses, encrypts (optional),
# uploads to S3, and manages retention.
#
# Usage:
#   ./backup.sh [--full] [--incremental] [--encrypt] [--upload] [--retention N]
#
# Environment variables (override in .env or export):
#   DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
#   BACKUP_DIR, S3_BUCKET, S3_PREFIX, RETENTION_DAYS
#   ENCRYPTION_KEY, AWS_PROFILE, AWS_REGION
# =============================================================================

set -euo pipefail
IFS=$'\n\t'

# ─── Configuration ──────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env"

# Load .env if present
if [[ -f "${ENV_FILE}" ]]; then
    # shellcheck disable=SC1090
    set -a
    source "${ENV_FILE}"
    set +a
fi

# Database defaults
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-gated_communities}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"

# Backup defaults
BACKUP_DIR="${BACKUP_DIR:-${SCRIPT_DIR}/backups}"
S3_BUCKET="${S3_BUCKET:-}"
S3_PREFIX="${S3_PREFIX:-gated-communities/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
ENCRYPTION_KEY="${ENCRYPTION_KEY:-}"
AWS_PROFILE="${AWS_PROFILE:-default}"
AWS_REGION="${AWS_REGION:-us-east-1}"

# Logging
LOG_DIR="${LOG_DIR:-${SCRIPT_DIR}/logs}"
LOG_FILE="${LOG_DIR}/backup-$(date +%Y%m%d-%H%M%S).log"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
DATE_PREFIX="$(date +%Y/%m/%d)"

# ─── Colors & Formatting ────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ─── Helper Functions ───────────────────────────────────────────────────────

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
log_debug() { log "DEBUG" "$@"; }

die() {
    log_error "$@"
    exit 1
}

cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "Backup failed with exit code ${exit_code}"
        # Clean up partial files
        if [[ -n "${BACKUP_FILE:-}" && -f "${BACKUP_FILE}" ]]; then
            rm -f "${BACKUP_FILE}"
            log_info "Removed partial backup file: ${BACKUP_FILE}"
        fi
    fi
    exit $exit_code
}

trap cleanup EXIT ERR

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Options:
  --full          Full database backup (default)
  --incremental   Incremental backup (requires WAL archiving)
  --encrypt       Encrypt backup with GPG
  --upload        Upload to S3 after backup
  --retention N   Override retention period (days)
  --dry-run       Show what would be done without executing
  -h, --help      Show this help message

Environment:
  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
  BACKUP_DIR, S3_BUCKET, S3_PREFIX, RETENTION_DAYS
  ENCRYPTION_KEY, AWS_PROFILE, AWS_REGION
EOF
}

# ─── Validation ─────────────────────────────────────────────────────────────

check_dependencies() {
    local deps=("pg_dump" "psql" "gzip" "date" "mkdir" "rm")
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &>/dev/null; then
            die "Required dependency not found: $dep"
        fi
    done

    if [[ "${ENCRYPT_BACKUP}" == "true" ]] && ! command -v "gpg" &>/dev/null; then
        die "GPG not found but encryption requested"
    fi

    if [[ "${UPLOAD_S3}" == "true" ]] && ! command -v "aws" &>/dev/null; then
        die "AWS CLI not found but S3 upload requested"
    fi
}

check_database_connection() {
    log_info "Checking database connection..."
    
    if ! PGPASSWORD="${DB_PASSWORD}" psql \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        -c "SELECT 1;" &>/dev/null; then
        die "Cannot connect to database ${DB_NAME} at ${DB_HOST}:${DB_PORT}"
    fi
    
    local db_size
    db_size=$(PGPASSWORD="${DB_PASSWORD}" psql \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        -t -c "SELECT pg_size_pretty(pg_database_size('${DB_NAME}'));" 2>/dev/null | xargs)
    
    log_info "Database connection OK. Size: ${db_size}"
}

# ─── Backup Functions ───────────────────────────────────────────────────────

perform_full_backup() {
    local backup_file="${BACKUP_DIR}/${DB_NAME}-full-${TIMESTAMP}.sql"
    local compressed_file="${backup_file}.gz"
    
    log_info "Starting full backup of ${DB_NAME}..."
    log_info "Backup file: ${compressed_file}"
    
    # Create backup directory
    mkdir -p "${BACKUP_DIR}"
    
    # Perform pg_dump with custom format (compressed, parallel)
    PGPASSWORD="${DB_PASSWORD}" pg_dump \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        --format=custom \
        --compress=9 \
        --verbose \
        --file="${backup_file}" \
        2>>"${LOG_FILE}"
    
    if [[ $? -ne 0 ]]; then
        die "pg_dump failed"
    fi
    
    # Get backup size
    local backup_size
    backup_size=$(du -h "${backup_file}" | cut -f1)
    log_info "Backup completed. Size: ${backup_size}"
    
    # Encrypt if requested
    if [[ "${ENCRYPT_BACKUP}" == "true" ]]; then
        encrypt_backup "${backup_file}"
        backup_file="${backup_file}.gpg"
        compressed_file="${backup_file}"
    fi
    
    # Upload to S3 if requested
    if [[ "${UPLOAD_S3}" == "true" ]]; then
        upload_to_s3 "${backup_file}" "full"
    fi
    
    # Clean up local file if uploaded
    if [[ "${UPLOAD_S3}" == "true" && "${KEEP_LOCAL}" != "true" ]]; then
        rm -f "${backup_file}"
        log_info "Removed local backup file (uploaded to S3)"
    fi
    
    echo "${compressed_file}"
}

perform_incremental_backup() {
    log_info "Starting incremental backup..."
    
    # Check if WAL archiving is enabled
    local wal_archive_enabled
    wal_archive_enabled=$(PGPASSWORD="${DB_PASSWORD}" psql \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -d "${DB_NAME}" \
        -t -c "SHOW archive_mode;" 2>/dev/null | xargs)
    
    if [[ "${wal_archive_enabled}" != "on" ]]; then
        log_warn "WAL archiving is not enabled. Falling back to full backup."
        perform_full_backup
        return
    fi
    
    # Use pg_basebackup for incremental
    local backup_file="${BACKUP_DIR}/${DB_NAME}-incr-${TIMESTAMP}"
    
    PGPASSWORD="${DB_PASSWORD}" pg_basebackup \
        -h "${DB_HOST}" \
        -p "${DB_PORT}" \
        -U "${DB_USER}" \
        -D "${backup_file}" \
        -Ft -z -P \
        2>>"${LOG_FILE}"
    
    if [[ $? -ne 0 ]]; then
        die "pg_basebackup failed"
    fi
    
    log_info "Incremental backup completed: ${backup_file}.tar.gz"
    
    if [[ "${UPLOAD_S3}" == "true" ]]; then
        upload_to_s3 "${backup_file}.tar.gz" "incremental"
    fi
    
    echo "${backup_file}.tar.gz"
}

encrypt_backup() {
    local file="$1"
    
    if [[ -z "${ENCRYPTION_KEY}" ]]; then
        die "ENCRYPTION_KEY not set but encryption requested"
    fi
    
    log_info "Encrypting backup: ${file}"
    
    gpg --batch --yes --passphrase "${ENCRYPTION_KEY}" \
        --symmetric --cipher-algo AES256 \
        --output "${file}.gpg" \
        "${file}"
    
    if [[ $? -ne 0 ]]; then
        die "Encryption failed"
    fi
    
    rm -f "${file}"
    log_info "Encryption completed: ${file}.gpg"
}

upload_to_s3() {
    local file="$1"
    local backup_type="$2"
    local s3_key="${S3_PREFIX}/${DATE_PREFIX}/$(basename "${file}")"
    
    log_info "Uploading to S3: s3://${S3_BUCKET}/${s3_key}"
    
    aws s3 cp "${file}" "s3://${S3_BUCKET}/${s3_key}" \
        --profile "${AWS_PROFILE}" \
        --region "${AWS_REGION}" \
        --storage-class STANDARD_IA
    
    if [[ $? -ne 0 ]]; then
        die "S3 upload failed"
    fi
    
    log_info "S3 upload completed"
}

# ─── Retention Management ───────────────────────────────────────────────────

apply_retention() {
    log_info "Applying retention policy (${RETENTION_DAYS} days)..."
    
    # Local retention
    if [[ -d "${BACKUP_DIR}" ]]; then
        local deleted_count
        deleted_count=$(find "${BACKUP_DIR}" -type f -mtime +"${RETENTION_DAYS}" | wc -l | xargs)
        find "${BACKUP_DIR}" -type f -mtime +"${RETENTION_DAYS}" -delete
        log_info "Deleted ${deleted_count} old local backup files"
    fi
    
    # S3 retention
    if [[ "${UPLOAD_S3}" == "true" && -n "${S3_BUCKET}" ]]; then
        local cutoff_date
        cutoff_date=$(date -d "${RETENTION_DAYS} days ago" +%Y-%m-%d 2>/dev/null || \
                      date -v-"${RETENTION_DAYS}"d +%Y-%m-%d)
        
        log_info "Deleting S3 objects older than ${cutoff_date}"
        
        aws s3 ls "s3://${S3_BUCKET}/${S3_PREFIX}/" \
            --profile "${AWS_PROFILE}" \
            --region "${AWS_REGION}" \
            --recursive | \
        while read -r line; do
            local file_date
            file_date=$(echo "$line" | awk '{print $1}')
            if [[ "${file_date}" < "${cutoff_date}" ]]; then
                local file_key
                file_key=$(echo "$line" | awk '{print $4}')
                log_info "Deleting old S3 object: ${file_key}"
                aws s3 rm "s3://${S3_BUCKET}/${file_key}" \
                    --profile "${AWS_PROFILE}" \
                    --region "${AWS_REGION}"
            fi
        done
    fi
}

# ─── Main ───────────────────────────────────────────────────────────────────

main() {
    local backup_type="full"
    ENCRYPT_BACKUP="false"
    UPLOAD_S3="false"
    KEEP_LOCAL="true"
    DRY_RUN="false"
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --full)
                backup_type="full"
                shift
                ;;
            --incremental)
                backup_type="incremental"
                shift
                ;;
            --encrypt)
                ENCRYPT_BACKUP="true"
                shift
                ;;
            --upload)
                UPLOAD_S3="true"
                shift
                ;;
            --retention)
                RETENTION_DAYS="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN="true"
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
    
    # Initialize logging
    mkdir -p "${LOG_DIR}"
    touch "${LOG_FILE}"
    
    log_info "=========================================="
    log_info "Gated Communities Database Backup"
    log_info "=========================================="
    log_info "Backup type: ${backup_type}"
    log_info "Database: ${DB_NAME}@${DB_HOST}:${DB_PORT}"
    log_info "Encryption: ${ENCRYPT_BACKUP}"
    log_info "S3 Upload: ${UPLOAD_S3}"
    log_info "Retention: ${RETENTION_DAYS} days"
    log_info "Log file: ${LOG_FILE}"
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log_info "DRY RUN - No changes will be made"
        exit 0
    fi
    
    # Pre-flight checks
    check_dependencies
    check_database_connection
    
    # Perform backup
    case "${backup_type}" in
        full)
            perform_full_backup
            ;;
        incremental)
            perform_incremental_backup
            ;;
    esac
    
    # Apply retention
    apply_retention
    
    log_info "=========================================="
    log_info "Backup completed successfully"
    log_info "=========================================="
}

main "$@"
