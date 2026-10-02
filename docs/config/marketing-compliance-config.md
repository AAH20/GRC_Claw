# Marketing Compliance — Configuration Guide

> Marketing compliance platform for GDPR, CAN-SPAM, FTC endorsement, and ADA accessibility monitoring and enforcement.

---

## Table of Contents

1. [Overview](#overview)
2. [Configuration Options](#configuration-options)
3. [Environment Variables](#environment-variables)
4. [Full Configuration File](#full-configuration-file)
5. [Example .env File](#example-env-file)
6. [Agent Configuration](#agent-configuration)
7. [Integration Settings](#integration-settings)
8. [Security Configuration](#security-configuration)
9. [Monitoring & Observability](#monitoring--observability)
10. [Rate Limiting & Caching](#rate-limiting--caching)

---

## Overview

The **marketing-compliance** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/marketing-compliance/
├── config/
│   ├── config.yaml          # Main configuration
│   └── .env.example        # Environment variable template
├── .env                   # Local environment (git-ignored)
└── config.yaml            # Alternative config location
```

---

## Configuration Options

All available configuration options with their default values:

| Option | Default Value |
|--------|---------------|
| `environment` | `production` |
| `log_level` | `INFO` |
| `server.host` | `0.0.0.0` |
| `server.port` | `8000` |
| `server.workers` | `4` |
| `server.reload` | `False` |
| `agents.monitor.scan_interval_seconds` | `300` |
| `agents.monitor.batch_size` | `50` |
| `agents.monitor.max_retries` | `3` |
| `agents.monitor.timeout_seconds` | `60` |
| `agents.detect.confidence_threshold` | `0.75` |
| `agents.detect.model` | `gpt-4` |
| `agents.detect.max_tokens` | `2048` |
| `agents.detect.temperature` | `0.1` |
| `agents.respond.auto_respond` | `False` |
| `agents.respond.escalation_threshold` | `high` |
| `agents.respond.response_templates_dir` | `config/templates` |
| `agents.report.default_format` | `pdf` |
| `agents.report.retention_days` | `90` |
| `agents.report.schedule` | `0 9 * * 1` |
| `agents.analytics.metrics_retention_days` | `365` |
| `agents.analytics.dashboard_refresh_seconds` | `300` |
| `agents.orchestrator.max_concurrent_tasks` | `10` |
| `agents.orchestrator.task_timeout_seconds` | `300` |
| `agents.orchestrator.retry_policy.max_attempts` | `3` |
| `agents.orchestrator.retry_policy.backoff_factor` | `2` |
| `integrations.salesforce.enabled` | `False` |
| `integrations.salesforce.api_version` | `v58.0` |
| `integrations.salesforce.sandbox` | `False` |
| `integrations.salesforce.timeout_seconds` | `30` |
| `integrations.hubspot.enabled` | `False` |
| `integrations.hubspot.api_version` | `v3` |
| `integrations.hubspot.timeout_seconds` | `30` |
| `integrations.mailchimp.enabled` | `False` |
| `integrations.mailchimp.api_version` | `3.0` |
| `integrations.mailchimp.timeout_seconds` | `30` |
| `compliance.policies` | `{'name': 'gdpr_consent', 'description': 'Verify GDPR consent for EU customers', 'severity': 'critical', 'enabled': True}, {'name': 'CAN-SPAM', 'description': 'Ensure CAN-SPAM compliance for email campaigns', 'severity': 'high', 'enabled': True}, {'name': 'FTC_endorsement', 'description': 'Check FTC endorsement guidelines compliance', 'severity': 'medium', 'enabled': True}, {'name': 'ADA_accessibility', 'description': 'Verify ADA accessibility standards', 'severity': 'medium', 'enabled': True}` |
| `monitoring.prometheus_enabled` | `True` |
| `monitoring.metrics_port` | `9090` |
| `monitoring.alerting.enabled` | `True` |
| `monitoring.alerting.channels` | `{'type': 'slack', 'webhook_url': '${SLACK_WEBHOOK_URL}'}, {'type': 'email', 'recipients': ['compliance@example.com']}` |
| `storage.type` | `local` |
| `storage.data_dir` | `./data` |
| `storage.backup_enabled` | `True` |
| `storage.backup_schedule` | `0 2 * * *` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `COMPLIANCE_ENVIRONMENT` | `development` | Application |
| `COMPLIANCE_LOG_LEVEL` | `DEBUG` | Application |
| `COMPLIANCE_SECRET_KEY` | `change-me-in-production` | Application |
| `SERVER_HOST` | `0.0.0.0` | Server |
| `SERVER_PORT` | `8000` | Server |
| `OPENAI_API_KEY` | `sk-your-openai-api-key` | LangChain / LLM |
| `LANGCHAIN_API_KEY` | `lsv2-your-langchain-api-key` | LangChain / LLM |
| `LANGCHAIN_TRACING_V2` | `true` | LangChain / LLM |
| `LANGCHAIN_PROJECT` | `marketing-compliance` | LangChain / LLM |
| `SALESFORCE_CLIENT_ID` | `your-salesforce-client-id` | Salesforce |
| `SALESFORCE_CLIENT_SECRET` | `your-salesforce-client-secret` | Salesforce |
| `SALESFORCE_USERNAME` | `your-salesforce-username` | Salesforce |
| `SALESFORCE_PASSWORD` | `your-salesforce-password` | Salesforce |
| `SALESFORCE_SECURITY_TOKEN` | `your-salesforce-security-token` | Salesforce |
| `SALESFORCE_SANDBOX` | `false` | Salesforce |
| `HUBSPOT_API_KEY` | `your-hubspot-api-key` | Hubspot |
| `HUBSPOT_ACCESS_TOKEN` | `your-hubspot-access-token` | Hubspot |
| `MAILCHIMP_API_KEY` | `your-mailchimp-api-key` | Mailchimp |
| `MAILCHIMP_SERVER_PREFIX` | `us1` | Mailchimp |
| `PROMETHEUS_ENABLED` | `true` | Monitoring |
| `SLACK_WEBHOOK_URL` | `https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK` | Monitoring |
| `DATA_DIR` | `./data` | Storage |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
environment: production
log_level: INFO
server:
  host: 0.0.0.0
  port: 8000
  workers: 4
  reload: False
agents:
  monitor:
    scan_interval_seconds: 300
    batch_size: 50
    max_retries: 3
    timeout_seconds: 60
  detect:
    confidence_threshold: 0.75
    model: gpt-4
    max_tokens: 2048
    temperature: 0.1
  respond:
    auto_respond: False
    escalation_threshold: high
    response_templates_dir: config/templates
  report:
    default_format: pdf
    retention_days: 90
    schedule: 0 9 * * 1
  analytics:
    metrics_retention_days: 365
    dashboard_refresh_seconds: 300
  orchestrator:
    max_concurrent_tasks: 10
    task_timeout_seconds: 300
    retry_policy:
      max_attempts: 3
      backoff_factor: 2
integrations:
  salesforce:
    enabled: False
    api_version: v58.0
    sandbox: False
    timeout_seconds: 30
  hubspot:
    enabled: False
    api_version: v3
    timeout_seconds: 30
  mailchimp:
    enabled: False
    api_version: 3.0
    timeout_seconds: 30
compliance:
  policies:
    -
      name: gdpr_consent
      description: Verify GDPR consent for EU customers
      severity: critical
      enabled: True
    -
      name: CAN-SPAM
      description: Ensure CAN-SPAM compliance for email campaigns
      severity: high
      enabled: True
    -
      name: FTC_endorsement
      description: Check FTC endorsement guidelines compliance
      severity: medium
      enabled: True
    -
      name: ADA_accessibility
      description: Verify ADA accessibility standards
      severity: medium
      enabled: True
monitoring:
  prometheus_enabled: True
  metrics_port: 9090
  alerting:
    enabled: True
    channels:
      -
        type: slack
        webhook_url: ${SLACK_WEBHOOK_URL}
      -
        type: email
        recipients:
          - compliance@example.com
storage:
  type: local
  data_dir: ./data
  backup_enabled: True
  backup_schedule: 0 2 * * *
```

---

## Example .env File

```bash
# Marketing Compliance Platform - Environment Variables
# Copy this file to .env and fill in your values

# Application
COMPLIANCE_ENVIRONMENT=development
COMPLIANCE_LOG_LEVEL=DEBUG
COMPLIANCE_SECRET_KEY=change-me-in-production

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# LangChain / LLM
OPENAI_API_KEY=sk-your-openai-api-key
LANGCHAIN_API_KEY=lsv2-your-langchain-api-key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=marketing-compliance

# Salesforce
SALESFORCE_CLIENT_ID=your-salesforce-client-id
SALESFORCE_CLIENT_SECRET=your-salesforce-client-secret
SALESFORCE_USERNAME=your-salesforce-username
SALESFORCE_PASSWORD=your-salesforce-password
SALESFORCE_SECURITY_TOKEN=your-salesforce-security-token
SALESFORCE_SANDBOX=false

# Hubspot
HUBSPOT_API_KEY=your-hubspot-api-key
HUBSPOT_ACCESS_TOKEN=your-hubspot-access-token

# Mailchimp
MAILCHIMP_API_KEY=your-mailchimp-api-key
MAILCHIMP_SERVER_PREFIX=us1

# Monitoring
PROMETHEUS_ENABLED=true
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# Storage
DATA_DIR=./data

```

---

## Agent Configuration

```yaml
agents:
  analytics:
    dashboard_refresh_seconds: 300
    metrics_retention_days: 365
  detect:
    confidence_threshold: 0.75
    max_tokens: 2048
    model: gpt-4
    temperature: 0.1
  monitor:
    batch_size: 50
    max_retries: 3
    scan_interval_seconds: 300
    timeout_seconds: 60
  orchestrator:
    max_concurrent_tasks: 10
    retry_policy:
      backoff_factor: 2
      max_attempts: 3
    task_timeout_seconds: 300
  report:
    default_format: pdf
    retention_days: 90
    schedule: 0 9 * * 1
  respond:
    auto_respond: false
    escalation_threshold: high
    response_templates_dir: config/templates
```

---

## Integration Settings

```yaml
integrations:
  hubspot:
    api_version: v3
    enabled: false
    timeout_seconds: 30
  mailchimp:
    api_version: 3.0
    enabled: false
    timeout_seconds: 30
  salesforce:
    api_version: v58.0
    enabled: false
    sandbox: false
    timeout_seconds: 30
```

---

## Security Configuration

### compliance

```yaml
compliance:
  policies:
  - description: Verify GDPR consent for EU customers
    enabled: true
    name: gdpr_consent
    severity: critical
  - description: Ensure CAN-SPAM compliance for email campaigns
    enabled: true
    name: CAN-SPAM
    severity: high
  - description: Check FTC endorsement guidelines compliance
    enabled: true
    name: FTC_endorsement
    severity: medium
  - description: Verify ADA accessibility standards
    enabled: true
    name: ADA_accessibility
    severity: medium
```

---

## Monitoring & Observability

### monitoring

```yaml
monitoring:
  alerting:
    channels:
    - type: slack
      webhook_url: ${SLACK_WEBHOOK_URL}
    - recipients:
      - compliance@example.com
      type: email
    enabled: true
  metrics_port: 9090
  prometheus_enabled: true
```

---

## Rate Limiting & Caching

No explicit rate limiting or caching configuration found.

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/marketing-compliance
cp .env.example .env  # or: cp config/.env.example .env
```

### 2. Edit `.env` with your values:

```bash
nano .env  # or your preferred editor
```

### 3. Validate configuration:

```bash
python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"
```

### 4. Start the service:

```bash
python -m src.main  # or: uvicorn src.main:app --host 0.0.0.0 --port 8000
```

---

*Generated for `marketing-compliance` — GRC_Claw Configuration Guide*
