# Database Backup & Recovery

Production-grade backup and disaster recovery solution for the Recruitment Platform PostgreSQL database.

## Features

- **Automated daily backups** with compression and integrity verification
- **S3 integration** for off-site backup storage
- **Retention management** with automatic cleanup
- **One-command restore** with safety checks and verification
- **Cron scheduling** with lock management
- **Slack notifications** for backup status
- **Manifest generation** for backup tracking

## Quick Start

### 1. Configure Environment

Create a `.env` file in this directory:

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=recruitment
DB_USER=postgres
DB_PASSWORD=your-secure-password

# Backup
BACKUP_DIR=/var/backups/recruitment-platform
RETENTION_DAYS=30

# S3 (optional)
S3_BUCKET=your-backup-bucket
S3_PREFIX=backups/database
AWS_PROFILE=default
AWS_REGION=us-east-1

# Notifications (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### 2. Run Backup

```bash
# Make executable
chmod +x backup.sh restore.sh backup-cron.sh

# Run backup
./backup.sh

# Run with options
./backup.sh --verbose
./backup.sh --no-s3        # Local only
./backup.sh --no-compress  # No compression
```

### 3. Schedule with Cron

```bash
# Install daily backup at 2 AM
./backup-cron.sh install '0 2 * * *'

# Install every 6 hours
./backup-cron.sh install '0 */6 * * *'

# Remove cron job
./backup-cron.sh uninstall
```

### 4. Restore

```bash
# Restore from local file
./restore.sh --file /var/backups/recruitment-platform/local/recruitment_20240115_020000.dump.gz

# Restore from S3
./restore.sh --s3 s3://your-bucket/backups/database/2024/01/15/recruitment_20240115_020000.dump.gz

# Restore latest from S3
./restore.sh --latest-s3

# Restore without confirmation (automation)
./restore.sh --latest-s3 --force
```

## File Structure

```
database/backup/
├── backup.sh              # Main backup script
├── restore.sh             # Restore script
├── backup-cron.sh         # Cron wrapper with locking
├── disaster-recovery.md   # DR procedures
├── README.md              # This file
├── .env                   # Environment config (create this)
├── local/                 # Local backup storage
│   ├── recruitment_YYYYMMDD_HHMMSS.dump.gz
│   └── pre_restore_YYYYMMDD_HHMMSS.dump.gz
├── logs/                  # Backup/restore logs
│   ├── backup_YYYYMMDD_HHMMSS.log
│   └── restore_YYYYMMDD_HHMMSS.log
└── manifest/              # Backup manifests
    └── YYYYMMDD_HHMMSS.manifest
```

## Backup Process

1. **Pre-flight checks** — Verify tools, connectivity, disk space
2. **pg_dump** — Custom format backup with compression
3. **Integrity verification** — Gzip test + trial restore
4. **Manifest generation** — SHA-256 checksum + metadata
5. **S3 upload** — Off-site copy with metadata
6. **Retention cleanup** — Remove old backups

## Restore Process

1. **Pre-flight checks** — Verify tools, connectivity, active connections
2. **Safety backup** — Backup current state before restore
3. **Download** (if S3) — Fetch backup file
4. **Integrity check** — Verify file integrity
5. **pg_restore** — Restore with `--no-owner --no-privileges`
6. **Verification** — Check tables, critical data, size

## Monitoring

### Check Backup Status

```bash
# List recent backups
ls -lt /var/backups/recruitment-platform/local/ | head -10

# Check logs
tail -f /var/backups/recruitment-platform/logs/backup_*.log

# Check S3
aws s3 ls s3://${S3_BUCKET}/backups/database/ --recursive | tail -10
```

### Slack Notifications

Set `SLACK_WEBHOOK_URL` in `.env` to receive notifications on:
- Backup success/failure
- Restore operations

## Troubleshooting

### Backup fails with "disk space"

```bash
# Check disk usage
df -h /var/backups/recruitment-platform

# Clean old backups manually
find /var/backups/recruitment-platform/local -name "*.dump.gz" -mtime +30 -delete

# Or reduce retention
RETENTION_DAYS=14 ./backup.sh
```

### Restore fails with "database in use"

```bash
# Terminate connections
psql -h localhost -U postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='recruitment';"

# Or use --force
./restore.sh --file backup.dump.gz --force
```

### S3 upload fails

```bash
# Check AWS credentials
aws sts get-caller-identity

# Check bucket permissions
aws s3 ls s3://${S3_BUCKET}/

# Test upload
echo "test" | aws s3 cp - s3://${S3_BUCKET}/test.txt
```

## Security Considerations

- **File permissions:** Scripts should be readable only by backup user
- **Credentials:** Never commit `.env` to version control
- **S3 bucket:** Enable versioning and encryption
- **Network:** Use VPC endpoints for S3 access
- **Encryption:** Backups are encrypted at rest by S3

## Disaster Recovery

See [disaster-recovery.md](./disaster-recovery.md) for full DR procedures including:
- Database corruption recovery
- Complete server failure recovery
- Accidental data deletion recovery
- Ransomware recovery
- Point-in-time recovery (PITR)

## License

MIT
