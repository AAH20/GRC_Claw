#!/bin/bash
# PostgreSQL backup script using pgBackRest
set -euo pipefail

BACKUP_DIR="/backup/postgresql"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

echo "Starting PostgreSQL backup at $(date)"

# Create backup
pgbackrest --stanza=grc-claw backup --type=full

# Verify backup
pgbackrest --stanza=grc-claw verify

# Upload to S3 (cross-region)
aws s3 sync /backup/postgresql/ s3://grc-claw-backups/postgresql/ --storage-class STANDARD_IA

# Clean old backups
pgbackrest --stanza=grc-claw expire --retention-full=${RETENTION_DAYS}

echo "PostgreSQL backup completed at $(date)"
