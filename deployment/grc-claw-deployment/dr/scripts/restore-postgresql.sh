#!/bin/bash
# PostgreSQL restore script
set -euo pipefail

TARGET_TIME=$1  # ISO 8601 timestamp for PITR

echo "Starting PostgreSQL restore to ${TARGET_TIME}"

# 1. Stop writes
kubectl exec -it postgresql-0 -- pg_ctl stop -m fast

# 2. Restore from backup
pgbackrest --stanza=grc-claw restore \
  --target-time="${TARGET_TIME}" \
  --target-action=promote

# 3. Verify data integrity
psql -c "SELECT count(*) FROM policies;"

# 4. Resume writes
kubectl exec -it postgresql-0 -- pg_ctl start

echo "PostgreSQL restore completed"
