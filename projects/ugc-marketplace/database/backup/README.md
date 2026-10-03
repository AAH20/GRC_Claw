# UGC Marketplace — Database Backup & Recovery

Production-grade backup and disaster recovery solution for PostgreSQL and Redis.

## Quick Start

```bash
# 1. Make scripts executable
chmod +x backup.sh restore.sh backup-cron.sh

# 2. Configure environment (edit .env or export variables)
cp ../docker/.env.example ../docker/.env
# Edit .env with your database credentials

# 3. Run a manual backup
./backup.sh

# 4. Set up cron job
crontab -e
# Add: 0 */6 * * * /path/to/backup-cron.sh
```

## Files

| File | Purpose |
|------|---------|
| `backup.sh` | Main backup script — PostgreSQL + Redis with S3 upload |
| `restore.sh` | Restore script — from local or S3 backups |
| `backup-cron.sh` | Cron wrapper — environment setup and scheduled execution |
| `disaster-recovery.md` | Full DR documentation and runbooks |

## Configuration

All configuration is via environment variables. Copy `../docker/.env.example` and customize:

### PostgreSQL

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `localhost` | Database host |
| `POSTGRES_PORT` | `5432` | Database port |
| `POSTGRES_DB` | `ugc_marketplace` | Database name |
| `POSTGRES_USER` | `ugc_user` | Database user |
| `POSTGRES_PASSWORD` | — | Database password (required) |

### Redis

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | `localhost` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_PASSWORD` | — | Redis password |

### Backup

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKUP_BASE_DIR` | `/var/backups/ugc-marketplace` | Local backup directory |
| `BACKUP_RETENTION_DAYS` | `30` | Days to keep local backups |
| `BACKUP_FORMAT` | `custom` | pg_dump format: custom, plain, directory |
| `COMPRESSION_LEVEL` | `6` | Gzip compression level |

### S3

| Variable | Default | Description |
|----------|---------|-------------|
| `S3_ENABLED` | `false` | Enable S3 upload |
| `S3_BUCKET` | — | S3 bucket name (required if enabled) |
| `S3_PREFIX` | `ugc-marketplace/backups` | S3 key prefix |
| `S3_REGION` | `us-east-1` | AWS region |
| `S3_STORAGE_CLASS` | `STANDARD_IA` | S3 storage class |

### Notifications

| Variable | Default | Description |
|----------|---------|-------------|
| `SLACK_WEBHOOK_URL` | — | Slack webhook for notifications |
| `NOTIFY_ON_SUCCESS` | `false` | Notify on successful backup |

## Backup Script

### Usage

```bash
./backup.sh [OPTIONS]

# Environment variables control behavior:
S3_ENABLED=true S3_BUCKET=my-bucket ./backup.sh
```

### What It Does

1. Acquires lock to prevent concurrent runs
2. Verifies dependencies (pg_dump, psql, redis-cli, aws)
3. Checks connectivity to PostgreSQL and Redis
4. Backs up PostgreSQL using pg_dump (custom format)
5. Backs up Redis using BGSAVE + RDB copy
6. Generates SHA256 checksums
7. Uploads to S3 (if enabled)
8. Prunes old backups based on retention policy
9. Sends notifications (if configured)

### Output

```
/var/backups/ugc-marketplace/
├── 2024/
│   └── 01/
│       └── 15/
│           ├── postgresql_20240115_120000.dump
│           ├── postgresql_20240115_120000.dump.sha256
│           ├── redis_20240115_120000.rdb
│           └── redis_20240115_120000.rdb.sha256
└── logs/
    ├── backup_20240115_120000.log
    └── cron/
        └── cron_20240115.log
```

## Restore Script

### Usage

```bash
# Restore from specific date
./restore.sh --date 2024-01-15 --type all

# Restore from specific file
./restore.sh --file /path/to/postgresql_20240115_120000.dump --type postgres

# Restore from S3
./restore.sh --s3 --date 2024-01-15 --type all

# Dry run (show what would be done)
./restore.sh --date 2024-01-15 --dry-run

# Skip confirmation
./restore.sh --date 2024-01-15 --yes
```

### Options

| Option | Description |
|--------|-------------|
| `-f, --file PATH` | Specific backup file |
| `-d, --date DATE` | Restore from date (YYYY-MM-DD) |
| `-t, --type TYPE` | postgres, redis, or all |
| `-s, --s3` | Download from S3 first |
| `-n, --dry-run` | Show actions without executing |
| `-y, --yes` | Skip confirmation |

## Cron Setup

### Every 6 Hours (Recommended)

```bash
crontab -e
# Add:
0 */6 * * * /path/to/backup/backup-cron.sh
```

### Daily with S3 Upload

```bash
0 2 * * * /path/to/backup/backup-cron.sh --s3
```

### Weekly Full Backup

```bash
0 3 * * 0 /path/to/backup/backup-cron.sh --weekly
```

## Monitoring

### Check Backup Status

```bash
# Latest backup
ls -lt /var/backups/ugc-marketplace/2024/*/*/postgresql_*.dump | head -5

# Backup logs
tail -f /var/backups/ugc-marketplace/logs/backup_*.log

# Cron logs
tail -f /var/backups/ugc-marketplace/logs/cron/cron_*.log
```

### Verify Backup Integrity

```bash
# Check checksums
sha256sum -c /var/backups/ugc-marketplace/2024/01/15/*.sha256

# List backup contents
pg_restore --list /var/backups/ugc-marketplace/2024/01/15/postgresql_*.dump
```

## Troubleshooting

### Backup Fails

```bash
# Check logs
cat /var/backups/ugc-marketplace/logs/backup_*.log

# Test PostgreSQL connection
PGPASSWORD=yourpassword psql -h localhost -U ugc_user -d ugc_marketplace -c "SELECT 1;"

# Test Redis connection
redis-cli -a yourpassword PING

# Check disk space
df -h /var/backups/ugc-marketplace
```

### Restore Fails

```bash
# Check logs
cat /var/backups/ugc-marketplace/logs/restore_*.log

# Verify backup file
file /path/to/backup.dump
pg_restore --list /path/to/backup.dump

# Test with dry-run first
./restore.sh --date 2024-01-15 --dry-run
```

### S3 Upload Fails

```bash
# Test S3 access
aws s3 ls s3://your-bucket/ --region us-east-1

# Check AWS credentials
aws sts get-caller-identity

# Test with small file
echo "test" | aws s3 cp - s3://your-bucket/test.txt
```

## Security

- Backup files contain sensitive data — restrict access:
  ```bash
  chmod 700 /var/backups/ugc-marketplace
  chmod 600 /var/backups/ugc-marketplace/2024/*/*
  ```
- S3 bucket should have encryption enabled and versioning on
- Use IAM roles instead of access keys where possible
- Rotate database credentials regularly
- Never commit `.env` files to version control

## Disaster Recovery

See [disaster-recovery.md](./disaster-recovery.md) for full DR procedures including:
- Database corruption recovery
- Complete server failure recovery
- Accidental data deletion recovery
- Ransomware incident response
- Backup verification procedures
