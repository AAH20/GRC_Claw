# Database Backup & Recovery

Automated backup and disaster recovery for Gated Communities PostgreSQL database.

## Quick Start

```bash
# Make scripts executable
chmod +x *.sh

# Run full backup
./backup.sh --full --encrypt --upload

# Restore from latest backup
./restore.sh --latest --force

# Setup cron job
crontab -e
# Add: 0 2 * * * /path/to/backup-cron.sh --daily
```

## Scripts

| Script | Purpose |
|--------|---------|
| `backup.sh` | Full/incremental backup with S3 upload |
| `restore.sh` | Restore from local or S3 backup |
| `backup-cron.sh` | Scheduled backup cron wrapper |

## Configuration

Create `.env` in project root:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gated_communities
DB_USER=postgres
DB_PASSWORD=your-password

BACKUP_DIR=./backups
S3_BUCKET=your-backup-bucket
S3_PREFIX=gated-communities/backups
RETENTION_DAYS=30

ENCRYPTION_KEY=your-gpg-passphrase
AWS_PROFILE=default
AWS_REGION=us-east-1

ALERT_EMAIL=ops@example.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

## Backup Types

- **Full** — Complete database dump (pg_dump -Fc)
- **Incremental** — WAL-based incremental (pg_basebackup)
- **Encrypted** — GPG AES-256 encryption
- **Compressed** — gzip level 9

## Restore Options

```bash
# From local file
./restore.sh --file backups/backup-20240101.dump

# From S3
./restore.sh --s3 gated-communities/backups/2024/01/01/backup.dump

# Latest local backup
./restore.sh --latest

# To different database
./restore.sh --file backup.dump --target-db test_restore
```

## Monitoring

Logs: `./logs/backup-*.log`, `./logs/restore-*.log`

Alerts: Email, Slack, PagerDuty (configure in `.env`)

## DR Procedures

See [disaster-recovery.md](./disaster-recovery.md) for full DR plan.
