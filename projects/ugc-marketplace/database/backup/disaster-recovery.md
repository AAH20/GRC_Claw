# UGC Marketplace — Disaster Recovery Plan

## Overview

This document describes the disaster recovery procedures for the UGC Marketplace platform, covering PostgreSQL and Redis data recovery, RTO/RPO targets, and step-by-step recovery instructions.

## Recovery Objectives

| Metric | Target | Description |
|--------|--------|-------------|
| **RPO** (Recovery Point Objective) | ≤ 6 hours | Maximum acceptable data loss |
| **RTO** (Recovery Time Objective) | ≤ 2 hours | Maximum acceptable downtime |
| **Backup Retention** | 30 days local, 90 days S3 | Point-in-time recovery window |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Production                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ PostgreSQL│  │  Redis   │  │  Backend │              │
│  │  :5432    │  │  :6379   │  │  :8000   │              │
│  └────┬─────┘  └────┬─────┘  └──────────┘              │
│       │              │                                   │
│       ▼              ▼                                   │
│  ┌─────────────────────────────┐                        │
│  │     backup.sh (cron)        │                        │
│  │  Every 6 hours + daily S3   │                        │
│  └──────────┬──────────────────┘                        │
│             │                                            │
│     ┌───────┴───────┐                                   │
│     ▼               ▼                                   │
│  Local Disk      S3 Bucket                              │
│  (30 days)       (90 days)                              │
└─────────────────────────────────────────────────────────┘
```

## Backup Schedule

| Frequency | Type | Destination | Retention |
|-----------|------|-------------|-----------|
| Every 6 hours | PostgreSQL + Redis | Local disk | 30 days |
| Daily (2 AM) | PostgreSQL + Redis | S3 | 90 days |
| Weekly (Sunday 3 AM) | Full + S3 sync | S3 | 90 days |

## Disaster Scenarios

### Scenario 1: Database Corruption

**Detection**: Application errors, data inconsistency alerts, monitoring alerts.

**Recovery Steps**:

1. **Stop application writes**
   ```bash
   # Scale down backend to prevent further writes
   kubectl scale deployment backend --replicas=0 -n ugc-marketplace
   # Or with docker-compose
   docker compose -f docker/docker-compose.prod.yml stop backend
   ```

2. **Identify last known good backup**
   ```bash
   # List available backups
   ls -la /var/backups/ugc-marketplace/
   
   # Or list S3 backups
   aws s3 ls s3://your-bucket/ugc-marketplace/backups/ --recursive
   ```

3. **Restore from backup**
   ```bash
   # Restore PostgreSQL
   ./restore.sh --type postgres --date 2024-01-15
   
   # Restore Redis
   ./restore.sh --type redis --date 2024-01-15
   
   # Or restore both
   ./restore.sh --type all --date 2024-01-15
   ```

4. **Verify data integrity**
   ```bash
   # Check PostgreSQL
   psql -h localhost -U ugc_user -d ugc_marketplace -c "SELECT COUNT(*) FROM users;"
   psql -h localhost -U ugc_user -d ugc_marketplace -c "SELECT COUNT(*) FROM products;"
   
   # Check Redis
   redis-cli DBSIZE
   redis-cli PING
   ```

5. **Resume application**
   ```bash
   kubectl scale deployment backend --replicas=3 -n ugc-marketplace
   # Or
   docker compose -f docker/docker-compose.prod.yml start backend
   ```

### Scenario 2: Complete Server Failure

**Detection**: Server unreachable, infrastructure alerts.

**Recovery Steps**:

1. **Provision new server** (use Terraform/Ansible or manual)

2. **Install dependencies**
   ```bash
   # Install PostgreSQL, Redis, AWS CLI
   # Follow your infrastructure provisioning process
   ```

3. **Restore from S3**
   ```bash
   # Download and restore from S3
   ./restore.sh --s3 --date 2024-01-15 --type all
   ```

4. **Update DNS/load balancer** to point to new server

5. **Verify application health**
   ```bash
   curl -f http://localhost:8000/health
   curl -f http://localhost:3000
   ```

### Scenario 3: Accidental Data Deletion

**Detection**: User reports, audit logs, monitoring alerts.

**Recovery Steps**:

1. **Identify the time of deletion**

2. **Restore to a temporary database**
   ```bash
   # Restore to a temporary database for data extraction
   psql -h localhost -U ugc_user -d postgres -c "CREATE DATABASE ugc_marketplace_recovery;"
   pg_restore -h localhost -U ugc_user -d ugc_marketplace_recovery /path/to/backup.dump
   ```

3. **Extract affected data**
   ```bash
   psql -h localhost -U ugc_user -d ugc_marketplace_recovery -c "SELECT * FROM affected_table WHERE ..."
   ```

4. **Insert recovered data into production**
   ```bash
   psql -h localhost -U ugc_user -d ugc_marketplace -c "INSERT INTO affected_table SELECT * FROM ..."
   ```

### Scenario 4: Ransomware / Security Incident

**Detection**: Unusual file encryption, security alerts.

**Recovery Steps**:

1. **ISOLATE** affected systems immediately

2. **Do NOT pay ransom** — restore from clean backups

3. **Verify backup integrity** (check checksums)
   ```bash
   sha256sum -c /var/backups/ugc-marketplace/2024/01/15/postgresql_*.sha256
   ```

4. **Rebuild infrastructure from scratch** (clean OS install)

5. **Restore from verified clean backups**
   ```bash
   ./restore.sh --s3 --date 2024-01-15 --type all
   ```

6. **Rotate all credentials** (database passwords, API keys, secrets)

7. **Conduct post-incident review**

## Backup Verification

### Automated Verification

Run weekly to verify backup integrity:

```bash
#!/bin/bash
# verify-backups.sh — Run weekly via cron

BACKUP_DIR="/var/backups/ugc-marketplace"
LATEST_BACKUP=$(find "$BACKUP_DIR" -name "postgresql_*.dump" -type f | sort -r | head -1)

if [[ -z "$LATEST_BACKUP" ]]; then
    echo "ERROR: No backup found!"
    exit 1
fi

# Verify checksum
if ! sha256sum -c "${LATEST_BACKUP}.sha256"; then
    echo "ERROR: Checksum verification failed for $LATEST_BACKUP"
    exit 1
fi

# Test restore to temporary database
TEMP_DB="verify_$(date +%s)"
psql -h localhost -U ugc_user -d postgres -c "CREATE DATABASE $TEMP_DB;"
if pg_restore -h localhost -U ugc_user -d $TEMP_DB "$LATEST_BACKUP" 2>/dev/null; then
    echo "SUCCESS: Backup verified: $LATEST_BACKUP"
    psql -h localhost -U ugc_user -d postgres -c "DROP DATABASE $TEMP_DB;"
else
    echo "ERROR: Backup restore test failed: $LATEST_BACKUP"
    psql -h localhost -U ugc_user -d postgres -c "DROP DATABASE IF EXISTS $TEMP_DB;"
    exit 1
fi
```

### Manual Verification

```bash
# List recent backups
ls -lh /var/backups/ugc-marketplace/2024/01/

# Check backup file sizes (should be > 0)
du -sh /var/backups/ugc-marketplace/2024/01/15/

# Verify checksums
sha256sum -c /var/backups/ugc-marketplace/2024/01/15/*.sha256

# Test PostgreSQL restore
pg_restore --list /var/backups/ugc-marketplace/2024/01/15/postgresql_*.dump | head -20
```

## S3 Backup Configuration

### Bucket Policy

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DenyUnencryptedUploads",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:PutObject",
            "Resource": "arn:aws:s3:::your-backup-bucket/*",
            "Condition": {
                "StringNotEquals": {
                    "s3:x-amz-server-side-encryption": "AES256"
                }
            }
        },
        {
            "Sid": "DenyDelete",
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:DeleteObject",
            "Resource": "arn:aws:s3:::your-backup-bucket/*"
        }
    ]
}
```

### S3 Lifecycle Policy

```json
{
    "Rules": [
        {
            "ID": "TransitionToGlacier",
            "Status": "Enabled",
            "Filter": {
                "Prefix": "ugc-marketplace/backups/"
            },
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "STANDARD_IA"
                },
                {
                    "Days": 60,
                    "StorageClass": "GLACIER"
                }
            ],
            "Expiration": {
                "Days": 365
            }
        }
    ]
}
```

## Monitoring & Alerts

### Backup Failure Alerts

Configure monitoring to alert on:
- Backup script exit code ≠ 0
- Backup file size < expected threshold
- Backup age > 12 hours (for 6-hour schedule)
- S3 upload failures
- Disk space < 10% on backup volume

### Health Check Script

```bash
#!/bin/bash
# health-check.sh — Run every 15 minutes

BACKUP_DIR="/var/backups/ugc-marketplace"
MAX_AGE_HOURS=7  # Slightly more than 6-hour schedule

# Check latest backup age
LATEST=$(find "$BACKUP_DIR" -name "postgresql_*.dump" -type f -printf '%T@ %p\n' | sort -rn | head -1 | cut -d' ' -f2-)
if [[ -z "$LATEST" ]]; then
    echo "CRITICAL: No backup found!"
    exit 2
fi

AGE_HOURS=$(( ($(date +%s) - $(stat -c %Y "$LATEST")) / 3600 ))
if [[ $AGE_HOURS -gt $MAX_AGE_HOURS ]]; then
    echo "CRITICAL: Last backup is ${AGE_HOURS} hours old!"
    exit 2
fi

echo "OK: Last backup is ${AGE_HOURS} hours old"
exit 0
```

## Contact & Escalation

| Role | Contact | Responsibility |
|------|---------|----------------|
| On-call Engineer | [PagerDuty rotation] | First responder |
| DBA | [Team lead] | Database recovery |
| Infrastructure | [Infra team] | Server provisioning |
| Security | [Security team] | Incident response |

## Testing Schedule

| Test | Frequency | Owner |
|------|-----------|-------|
| Backup verification (automated) | Weekly | Automated |
| Restore drill (to staging) | Monthly | DBA |
| Full DR simulation | Quarterly | Infrastructure |
| Ransomware recovery test | Bi-annually | Security |

## Document History

| Date | Author | Change |
|------|--------|--------|
| 2024-01-01 | Infrastructure | Initial DR plan |
