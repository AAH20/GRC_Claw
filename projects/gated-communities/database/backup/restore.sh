#!/usr/bin/env bash
# =============================================================================
# restore.sh — PostgreSQL Restore for Gated Communities
# =============================================================================
# Restores database from a local or S3 backup file.
#
# Usage:
#   ./restore.sh --file <backup_file> [--force] [--dry-run]
#   ./restore.sh --s3 <s3_key> [--force] [--dry-run]
#   ./restore.sh --latest [--force] [--dry-run]
#
# Options:
#   --file PATH       Restore from local file
#   --s3 KEY          Restore from S3 (downloads first)
#   --latest          Restore from most recent local backup
#   --force           Skip confirmation prompt
#   --dry-run         Show what would be done without executing
#   --target-db NAME  Restore to different database name
#   -h, --help        Show this help message
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
AWS_PROFILE="${AWS_PROFILE:-default}"
AWS_REGION="${AWS_REGION:-us-east-1}"
ENCRYPTION_KEY="${ENCRYPTION_KEY:-}"

LOG_DIR="${LOG_DIR:-${SCRIPT_DIR}/logs}"
LOG_FILE="${LOG_DIR}/restore-$(date +%Y%m%d-%H%M%S).log"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
    exit 1
}

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Options:
  --file PATH       Restore from local backup file
  --s3 KEY          Restore from S3 (downloads first)
  --latest          Restore from most recent local backup
  --force           Skip confirmation prompt
  --dry-run         Show what would be done without executing
  --target-db NAME  Restore to different database name
  -h, --help        Show this help message

Examples:
  ./restore.sh --file backups/gated_communities-full-20240101-120000.sql
  ./restore.sh --s3 gated-communities/backups/2024/01/01/backup.dump
  ./restore.sh --latest --force
  ./restore.sh --file backup.dump --target-db gated_communities_restored
EOF
}

check_dependencies() {
    local deps=("pg_restore" "psql" "gzip" "date")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &>/dev/null; then
            die "Required dependency not found: $dep"
        fi
    done
}

check_database_connection() {
    log_info "Checking database connection..."
    if ! PGPASSWORD="${DB_PASSWORD}" psql \
        -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" \
        -d "postgres" -c "SELECT 1;" &>/dev/null; then
        die "Cannot connect to PostgreSQL at ${DB_HOST}:${DB_PORT}"
    fi
    log_info "Database connection OK"
}

download_from_s3() {
    local s3_key="$1"
    local local_file="${BACKUP_DIR}/$(basename "${s3_key}")"
    
    mkdir -p "${BACKUP_DIR}"
    
    log_info "Downloading from S3: s3://${S3_BUCKET}/${s3_key}"
    aws s3 cp "s3://${S3_BUCKET}/${s3_key}" "${local_file}" \
        --profile "${AWS_PROFILE}" --region "${AWS_REGION}"
    
    if [[ $? -ne 0 ]]; then
        die "S3 download failed"
    fi
    
    echo "${local_file}"
}

find_latest_backup() {
    local latest
    latest=$(find "${BACKUP_DIR}" -type f -name "*.sql" -o -name "*.dump" -o -name "*.backup" | sort -r | head -1)
    
    if [[ -z "${latest}" ]]; then
        die "No backup files found in ${BACKUP_DIR}"
    fi
    
    echo "${latest}"
}

decrypt_if_needed() {
    local file="$1"
    
    if [[ "${file}" == *.gpg ]]; then
        if [[ -z "${ENCRYPTION_KEY}" ]]; then
            die "ENCRYPTION_KEY not set but backup is encrypted"
        fi
        
        log_info "Decrypting backup: ${file}"
        local decrypted="${file%.gpg}"
        
        gpg --batch --yes --passphrase "${ENCRYPTION_KEY}" \
            --decrypt --output "${decrypted}" "${file}"
        
        if [[ $? -ne 0 ]]; then
            die "Decryption failed"
        fi
        
        echo "${decrypted}"
    else
        echo "${file}"
    fi
}

decompress_if_needed() {
    local file="$1"
    
    if [[ "${file}" == *.gz ]]; then
        log_info "Decompressing backup: ${file}"
        gunzip -k "${file}"
        echo "${file%.gz}"
    else
        echo "${file}"
    fi
}

confirm_restore() {
    local target_db="$1"
    
    echo ""
    echo -e "${RED}WARNING: This will OVERWRITE database '${target_db}'${NC}"
    echo -e "${RED}All existing data will be LOST!${NC}"
    echo ""
    
    if [[ "${FORCE_RESTORE}" == "true" ]]; then
        log_warn "Force mode enabled, skipping confirmation"
        return 0
    fi
    
    read -p "Are you sure you want to continue? Type 'yes' to proceed: " confirm
    if [[ "${confirm}" != "yes" ]]; then
        log_info "Restore cancelled by user"
        exit 0
    fi
}

perform_restore() {
    local backup_file="$1"
    local target_db="${2:-${DB_NAME}}"
    
    log_info "Starting restore to database: ${target_db}"
    log_info "Backup file: ${backup_file}"
    
    # Check if target database exists
    local db_exists
    db_exists=$(PGPASSWORD="${DB_PASSWORD}" psql \
        -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" \
        -d "postgres" -t -c \
        "SELECT 1 FROM pg_database WHERE datname='${target_db}';" 2>/dev/null | xargs)
    
    if [[ "${db_exists}" == "1" ]]; then
        log_warn "Database '${target_db}' already exists"
        
        if [[ "${FORCE_RESTORE}" == "true" ]]; then
            log_info "Dropping existing database..."
            PGPASSWORD="${DB_PASSWORD}" psql \
                -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" \
                -d "postgres" -c "DROP DATABASE IF EXISTS ${target_db};"
        else
            read -p "Database exists. Drop and recreate? (yes/no): " drop_confirm
            if [[ "${drop_confirm}" != "yes" ]]; then
                die "Restore cancelled"
            fi
            PGPASSWORD="${DB_PASSWORD}" psql \
                -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" \
                -d "postgres" -c "DROP DATABASE IF EXISTS ${target_db};"
        fi
    fi
    
    # Create new database
    log_info "Creating database: ${target_db}"
    PGPASSWORD="${DB_PASSWORD}" psql \
        -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" \
        -d "postgres" -c "CREATE DATABASE ${target_db};"
    
    # Determine file type and restore accordingly
    local file_type
    file_type=$(file -b "${backup_file}")
    
    if [[ "${backup_file}" == *.sql ]] || [[ "${file_type}" == *"ASCII text"* ]]; then
        # Plain SQL dump
        log_info "Restoring from SQL dump..."
        PGPASSWORD="${DB_PASSWORD}" psql \
            -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" \
            -d "${target_db}" \
            -f "${backup_file}" \
            2>>"${LOG_FILE}"
    else
        # Custom format (pg_dump -Fc)
        log_info "Restoring from custom format dump..."
        PGPASSWORD="${DB_PASSWORD}" pg_restore \
            -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" \
            -d "${target_db}" \
            --verbose \
            --no-owner \
            --no-privileges \
            "${backup_file}" \
            2>>"${LOG_FILE}"
    fi
    
    if [[ $? -ne 0 ]]; then
        die "Restore failed"
    fi
    
    # Verify restore
    log_info "Verifying restore..."
    local table_count
    table_count=$(PGPASSWORD="${DB_PASSWORD}" psql \
        -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" \
        -d "${target_db}" -t -c \
        "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | xargs)
    
    log_info "Restore completed. Tables in database: ${table_count}"
}

main() {
    local backup_file=""
    local s3_key=""
    local use_latest=false
    FORCE_RESTORE="false"
    DRY_RUN="false"
    local target_db="${DB_NAME}"
    
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --file)
                backup_file="$2"
                shift 2
                ;;
            --s3)
                s3_key="$2"
                shift 2
                ;;
            --latest)
                use_latest=true
                shift
                ;;
            --force)
                FORCE_RESTORE="true"
                shift
                ;;
            --dry-run)
                DRY_RUN="true"
                shift
                ;;
            --target-db)
                target_db="$2"
                shift 2
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
    
    mkdir -p "${LOG_DIR}"
    touch "${LOG_FILE}"
    
    log_info "=========================================="
    log_info "Gated Communities Database Restore"
    log_info "=========================================="
    
    if [[ "${DRY_RUN}" == "true" ]]; then
        log_info "DRY RUN - No changes will be made"
        exit 0
    fi
    
    check_dependencies
    check_database_connection
    
    # Determine backup source
    if [[ -n "${s3_key}" ]]; then
        backup_file=$(download_from_s3 "${s3_key}")
    elif [[ "${use_latest}" == "true" ]]; then
        backup_file=$(find_latest_backup)
    elif [[ -z "${backup_file}" ]]; then
        die "No backup source specified. Use --file, --s3, or --latest"
    fi
    
    if [[ ! -f "${backup_file}" ]]; then
        die "Backup file not found: ${backup_file}"
    fi
    
    log_info "Using backup file: ${backup_file}"
    
    # Pre-process backup file
    backup_file=$(decrypt_if_needed "${backup_file}")
    backup_file=$(decompress_if_needed "${backup_file}")
    
    # Confirm and restore
    confirm_restore "${target_db}"
    perform_restore "${backup_file}" "${target_db}"
    
    log_info "=========================================="
    log_info "Restore completed successfully"
    log_info "=========================================="
}

main "$@"
