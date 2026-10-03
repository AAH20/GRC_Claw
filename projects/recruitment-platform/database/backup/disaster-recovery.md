# Disaster Recovery Plan — Recruitment Platform Database

## Overview

This document describes the disaster recovery procedures for the Recruitment Platform PostgreSQL database. It covers recovery objectives, scenarios, step-by-step recovery procedures, and testing requirements.

## Recovery Objectives

| Metric | Target | Description |
|--------|--------|-------------|
| **RPO** (Recovery Point Objective) | ≤ 24 hours | Maximum acceptable data loss |
| **RTO** (Recovery Time Objective) | ≤ 4 hours | Maximum acceptable downtime |
| **Retention** | 30 days | Local backup retention |
| **S3 Retention** | 90 days | Off-site backup retention |

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   PostgreSQL    │────▶│  Local Backups   │────▶│   S3 Bucket     │
│   (Primary)     │     │  (30-day retain) │     │  (90-day retain) │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                        │                        │
        ▼                        ▼                        ▼
   pg_dump                 backup.sh               backup-cron.sh
   (custom format)        (compression +           (scheduled)
                           verification)
```

## Backup Schedule

| Type | Frequency | Retention | Storage |
|------|-----------|-----------|---------|
| Full backup | Daily at 2:00 AM | 30 days | Local + S3 |
| WAL archiving | Continuous | 7 days | Local |
| Safety backup | Before each restore | 7 days | Local |

## Disaster Scenarios

### Scenario 1: Database Corruption

**Symptoms:** Queries return errors, data inconsistency, application crashes.

**Recovery Steps:**

1. **Stop application writes**
   ```bash
   # Scale down application or enable maintenance mode
   docker compose stop api worker
   ```

2. **Create safety backup of corrupted state**
   ```bash
   ./backup.sh --no-s3
   ```

3. **Identify last known good backup**
   ```bash
   # List local backups
   ls -lt /var/backups/recruitment-platform/local/

   # Or find latest in S3
   aws s3 ls s3://${S3_BUCKET}/backups/database/ --recursive | sort | tail -5
   ```

4. **Restore from backup**
   ```bash
   ./restore.sh --file /var/backups/recruitment-platform/local/recruitment_YYYYMMDD_HHMMSS.dump.gz
   ```

5. **Verify and resume**
   ```bash
   # Check application health
   curl http://localhost:8000/api/v1/health

   # Resume services
   docker compose start api worker
   ```

### Scenario 2: Complete Server Failure

**Symptoms:** Server unreachable, hardware failure, cloud instance terminated.

**Recovery Steps:**

1. **Provision new server** (use Terraform/IaC)
   ```bash
   cd ~/GRC_Claw/projects/recruitment-platform/terraform
   terraform apply
   ```

2. **Install dependencies**
   ```bash
   # Install PostgreSQL 16
   # Install AWS CLI
   # Install required tools
   ```

3. **Restore from S3**
   ```bash
   export S3_BUCKET="your-backup-bucket"
   export DB_PASSWORD="new-db-password"

   ./restore.sh --latest-s3 --force
   ```

4. **Update connection strings**
   ```bash
   # Update .env or Kubernetes secrets
   export DATABASE_URL="postgresql://postgres:${DB_PASSWORD}@new-host:5432/recruitment"
   ```

5. **Verify and resume**
   ```bash
   docker compose up -d
   curl http://localhost:8000/api/v1/health
   ```

### Scenario 3: Accidental Data Deletion

**Symptoms:** Specific tables or records missing, accidental DROP TABLE.

**Recovery Steps:**

1. **Identify the time of deletion**

2. **Restore to a temporary database**
   ```bash
   ./restore.sh --file /path/to/backup.dump.gz --target-db recruitment_recovery
   ```

3. **Extract missing data**
   ```bash
   pg_dump -h localhost -U postgres -d recruitment_recovery \
     --table=deleted_table --data-only > missing_data.sql
   ```

4. **Apply to production**
   ```bash
   psql -h localhost -U postgres -d recruitment < missing_data.sql
   ```

5. **Clean up**
   ```bash
   psql -h localhost -U postgres -c "DROP DATABASE recruitment_recovery;"
   ```

### Scenario 4: Ransomware / Security Breach

**Symptoms:** Encrypted files, unauthorized access, data exfiltration.

**Recovery Steps:**

1. **Isolate affected systems**
   ```bash
   # Disconnect from network
   # Do NOT power off — preserve evidence
   ```

2. **Assess scope of compromise**

3. **Rebuild from known-good infrastructure**
   ```bash
   # Use Terraform to rebuild from scratch
   terraform destroy && terraform apply
   ```

4. **Restore from S3 (immutable backups)**
   ```bash
   # S3 versioning provides protection against ransomware
   ./restore.sh --latest-s3 --force
   ```

5. **Rotate all credentials**
   - Database passwords
   - API keys
   - AWS credentials
   - Application secrets

6. **Security audit and hardening**

## Recovery Procedures

### Full Restore from Local Backup

```bash
# 1. Identify backup
ls -lt /var/backups/recruitment-platform/local/ | head -5

# 2. Restore
./restore.sh --file /var/backups/recruitment-platform/local/recruitment_20240115_020000.dump.gz

# 3. Verify
psql -h localhost -U postgres -d recruitment -c "\dt"
```

### Full Restore from S3

```bash
# 1. Set environment
export S3_BUCKET="recruitment-platform-backups"
export DB_PASSWORD="your-password"

# 2. Restore latest
./restore.sh --latest-s3 --force

# 3. Or restore specific backup
./restore.sh --s3 s3://recruitment-platform-backups/backups/database/2024/01/15/recruitment_20240115_020000.dump.gz
```

### Point-in-Time Recovery (PITR)

Requires WAL archiving to be enabled in `postgresql.conf`:

```ini
wal_level = replica
archive_mode = on
archive_command = 'cp %p /var/backups/recruitment-platform/wal/%f'
```

```bash
# 1. Restore base backup
./restore.sh --file /path/to/base_backup.dump.gz

# 2. Configure recovery
cat >> /var/lib/postgresql/data/postgresql.auto.conf <<EOF
restore_command = 'cp /var/backups/recruitment-platform/wal/%f %p'
recovery_target_time = '2024-01-15 14:30:00'
recovery_target_action = 'promote'
EOF

# 3. Start PostgreSQL
pg_ctl start
```

## Testing Requirements

### Monthly DR Drill

- [ ] Perform full restore to staging environment
- [ ] Verify application functionality
- [ ] Document recovery time
- [ ] Update runbooks if needed

### Quarterly Tests

- [ ] Test S3 restore from different region
- [ ] Verify backup integrity (checksums)
- [ ] Test PITR procedure
- [ ] Review and update retention policies

### Annual Tests

- [ ] Full infrastructure rebuild from scratch
- [ ] Cross-region restore test
- [ ] Disaster recovery team training
- [ ] Update DR plan based on lessons learned

## Emergency Contacts

| Role | Name | Contact |
|------|------|---------|
| DBA On-Call | TBD | TBD |
| Infrastructure | TBD | TBD |
| Security | TBD | TBD |

## Quick Reference

```bash
# Backup now
./backup.sh

# Restore from local
./restore.sh --file /path/to/backup.dump.gz

# Restore from S3
./restore.sh --latest-s3

# Install cron job
./backup-cron.sh install '0 2 * * *'

# Check backup status
ls -lt /var/backups/recruitment-platform/local/
aws s3 ls s3://${S3_BUCKET}/backups/database/ --recursive | tail -5
```

## Document History

| Date | Author | Changes |
|------|--------|---------|
| 2024-01-01 | Ahmed Hassan | Initial DR plan |
