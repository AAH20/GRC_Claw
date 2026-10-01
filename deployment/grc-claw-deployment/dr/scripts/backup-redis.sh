#!/bin/bash
# Redis backup script
set -euo pipefail

BACKUP_DIR="/backup/redis"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

echo "Starting Redis backup at $(date)"

# Trigger BGSAVE
kubectl exec -it redis-0 -- redis-cli BGSAVE

# Wait for save to complete
sleep 5

# Copy RDB file
kubectl cp redis-0:/var/lib/redis/dump.rdb ${BACKUP_DIR}/dump_${TIMESTAMP}.rdb

# Upload to S3
aws s3 cp ${BACKUP_DIR}/dump_${TIMESTAMP}.rdb s3://grc-claw-backups/redis/

# Clean old backups
find ${BACKUP_DIR} -name "dump_*.rdb" -mtime +${RETENTION_DAYS} -delete

echo "Redis backup completed at $(date)"
