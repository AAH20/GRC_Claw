# Disaster Recovery Plan — Gated Communities

## Overview

This document describes the disaster recovery procedures for the Gated Communities platform. It covers recovery objectives, scenarios, step-by-step recovery procedures, and testing protocols.

## Recovery Objectives

| Metric | Target | Description |
|--------|--------|-------------|
| **RPO** (Recovery Point Objective) | ≤ 1 hour | Maximum acceptable data loss |
| **RTO** (Recovery Time Objective) | ≤ 4 hours | Maximum acceptable downtime |
| **Backup Retention** | 30 days local, 1 year S3 | Point-in-time recovery capability |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Production Environment                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  App     │  │  Redis   │  │ Postgres │  │  Worker  │   │
│  │ Servers  │  │  Cache   │  │ Primary  │  │  Nodes   │   │
│  └──────────┘  └──────────┘  └────┬─────┘  └──────────┘   │
│                                    │                        │
│                              pg_dump /                      │
│                              pg_basebackup                  │
└────────────────────────────────────┼────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
              ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
              │  Local    │   │  S3       │   │  S3       │
              │  Disk     │   │  Standard │   │  Glacier  │
              │  (7 days) │   │  (30 days)│   │  (1 year) │
              └───────────┘   └───────────┘   └───────────┘
```

## Backup Schedule

| Frequency | Type | Location | Retention |
|-----------|------|----------|-----------|
| Hourly | Incremental (WAL) | S3 Standard | 7 days |
| Daily | Full (pg_dump) | S3 Standard | 30 days |
| Weekly | Full + Verify | S3 Standard | 90 days |
| Monthly | Full + Archive | S3 Glacier | 1 year |

## Disaster Scenarios

### Scenario 1: Database Corruption

**Detection:** Application errors, data inconsistency alerts, failed health checks.

**Recovery Steps:**

1. **Stop application writes**
   ```bash
   docker compose stop app worker
   ```

2. **Identify last known good backup**
   ```bash
   # List available backups
   aws s3 ls s3://${S3_BUCKET}/${S3_PREFIX}/ --recursive
   
   # Or check local backups
   ls -lt ${BACKUP_DIR}/
   ```

3. **Restore from backup**
   ```bash
   cd ~/GRC_Claw/projects/gated-communities/database/backup
   ./restore.sh --latest --force
   ```

4. **Verify data integrity**
   ```bash
   psql -h ${DB_HOST} -U ${DB_USER} -d ${DB_NAME} -c "
     SELECT count(*) FROM communities;
     SELECT count(*) FROM users;
     SELECT count(*) FROM content;
   "
   ```

5. **Replay WAL logs** (if available)
   ```bash
   # Use pg_waldump to replay transactions up to corruption point
   pg_waldump /var/lib/postgresql/data/pg_wal/ | ...
   ```

6. **Restart application**
   ```bash
   docker compose start app worker
   ```

### Scenario 2: Complete Server Failure

**Detection:** Server unreachable, infrastructure alerts.

**Recovery Steps:**

1. **Provision new server**
   ```bash
   # Use infrastructure-as-code (Terraform/Ansible)
   terraform apply -var="environment=production"
   ```

2. **Install dependencies**
   ```bash
   # Docker, AWS CLI, PostgreSQL client
   ./scripts/setup-server.sh
   ```

3. **Restore from S3**
   ```bash
   cd ~/GRC_Claw/projects/gated-communities/database/backup
   ./restore.sh --s3 ${S3_PREFIX}/latest/backup.dump --force
   ```

4. **Update DNS/load balancer**
   ```bash
   # Update Route53 or load balancer to point to new server
   aws route53 change-resource-record-sets ...
   ```

5. **Verify application health**
   ```bash
   curl -f http://localhost:8000/health
   ```

### Scenario 3: Accidental Data Deletion

**Detection:** User reports, audit log analysis.

**Recovery Steps:**

1. **Identify deletion timeframe**
   ```sql
   SELECT * FROM audit_log 
   WHERE action = 'DELETE' 
   AND timestamp > NOW() - INTERVAL '24 hours'
   ORDER BY timestamp DESC;
   ```

2. **Restore to temporary database**
   ```bash
   ./restore.sh --latest --target-db gated_communities_recovery
   ```

3. **Extract affected data**
   ```sql
   -- Export deleted records
   COPY (SELECT * FROM deleted_table WHERE id IN (...)) 
   TO '/tmp/recovered_data.csv' CSV HEADER;
   ```

4. **Merge back to production**
   ```sql
   INSERT INTO production_table 
   SELECT * FROM gated_communities_recovery.deleted_table
   WHERE id IN (...);
   ```

5. **Drop temporary database**
   ```sql
   DROP DATABASE gated_communities_recovery;
   ```

### Scenario 4: Ransomware / Security Breach

**Detection:** Unusual file access patterns, encryption alerts.

**Recovery Steps:**

1. **Isolate affected systems**
   ```bash
   # Disconnect from network
   ifconfig eth0 down
   
   # Or use security groups
   aws ec2 modify-instance-attribute --instance-id ${INSTANCE_ID} --no-source-dest-check
   ```

2. **Preserve evidence**
   ```bash
   # Create forensic snapshot
   aws ec2 create-snapshot --volume-id ${VOLUME_ID} --description "Forensic snapshot"
   ```

3. **Restore from clean backup**
   ```bash
   # Use backup from before breach
   ./restore.sh --file /path/to/clean/backup.dump --force
   ```

4. **Rotate all credentials**
   ```bash
   # Database passwords
   # API keys
   # Encryption keys
   # SSL certificates
   ```

5. **Security audit and patch**
   ```bash
   # Review access logs
   # Apply security patches
   # Update firewall rules
   ```

## Recovery Procedures

### Full Database Restore

```bash
#!/bin/bash
# Full restore procedure

# 1. Stop services
docker compose down

# 2. Clean data volume
docker volume rm gated-communities_postgres_data

# 3. Start database only
docker compose up -d db

# 4. Wait for database
sleep 10

# 5. Restore from backup
cd ~/GRC_Claw/projects/gated-communities/database/backup
./restore.sh --latest --force

# 6. Start all services
docker compose up -d

# 7. Verify
curl -f http://localhost:8000/health
```

### Point-in-Time Recovery

```bash
#!/bin/bash
# PITR using WAL archives

# 1. Restore base backup
./restore.sh --file /path/to/base/backup.dump --target-db ${DB_NAME}_pitr

# 2. Configure recovery
cat >> /var/lib/postgresql/data/postgresql.conf <<EOF
restore_command = 'aws s3 cp s3://${S3_BUCKET}/wal/%f %p'
recovery_target_time = '2024-01-15 14:30:00'
recovery_target_action = 'promote'
EOF

# 3. Start recovery
pg_ctl start

# 4. Monitor progress
tail -f /var/lib/postgresql/data/log/postgresql-*.log
```

## Testing Protocol

### Monthly DR Drill

1. **Schedule:** First Saturday of each month
2. **Duration:** 2 hours
3. **Participants:** DevOps, DBA, Engineering Lead

**Checklist:**
- [ ] Restore from S3 to clean environment
- [ ] Verify data integrity (row counts, checksums)
- [ ] Run application smoke tests
- [ ] Measure actual RTO
- [ ] Document issues and improvements
- [ ] Update runbooks

### Quarterly Full DR Test

1. **Schedule:** First week of each quarter
2. **Duration:** 1 day
3. **Scope:** Complete environment rebuild

**Checklist:**
- [ ] Provision new infrastructure
- [ ] Restore from Glacier (test retrieval time)
- [ ] Full application deployment
- [ ] Load testing
- [ ] Failover testing
- [ ] Documentation review

## Contact Information

| Role | Name | Contact |
|------|------|---------|
| DBA On-Call | [Name] | [Phone/Email] |
| DevOps Lead | [Name] | [Phone/Email] |
| Engineering Manager | [Name] | [Phone/Email] |
| Security Team | [Name] | [Phone/Email] |

## Document History

| Date | Author | Changes |
|------|--------|---------|
| 2024-01-01 | System | Initial version |
