# Crm Enhancer — Configuration Guide

> CRM enhancement platform that enriches contacts, scores deals, automates tasks, and provides sales performance analytics.

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

The **crm-enhancer** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/crm-enhancer/
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
| `app.name` | `CRM Enhancer` |
| `app.version` | `0.1.0` |
| `app.environment` | `development` |
| `app.log_level` | `INFO` |
| `app.host` | `0.0.0.0` |
| `app.port` | `8000` |
| `agents.contact_enrichment.enabled` | `True` |
| `agents.contact_enrichment.max_retries` | `3` |
| `agents.contact_enrichment.timeout_seconds` | `30` |
| `agents.contact_enrichment.enrichment_sources` | `clearbit, zoominfo, hunter` |
| `agents.deal_scoring.enabled` | `True` |
| `agents.deal_scoring.model_path` | `models/deal_scorer.pkl` |
| `agents.deal_scoring.scoring_factors` | `deal_size, stage_progression, engagement_level, company_fit, timeline` |
| `agents.deal_scoring.weights.deal_size` | `0.25` |
| `agents.deal_scoring.weights.stage_progression` | `0.2` |
| `agents.deal_scoring.weights.engagement_level` | `0.25` |
| `agents.deal_scoring.weights.company_fit` | `0.15` |
| `agents.deal_scoring.weights.timeline` | `0.15` |
| `agents.task_automation.enabled` | `True` |
| `agents.task_automation.max_concurrent_tasks` | `10` |
| `agents.task_automation.default_priority` | `medium` |
| `agents.task_automation.auto_assign` | `True` |
| `agents.meeting_scheduling.enabled` | `True` |
| `agents.meeting_scheduling.default_duration_minutes` | `30` |
| `agents.meeting_scheduling.buffer_minutes` | `15` |
| `agents.meeting_scheduling.timezone` | `UTC` |
| `agents.meeting_scheduling.working_hours.start` | `09:00` |
| `agents.meeting_scheduling.working_hours.end` | `17:00` |
| `agents.followup_automation.enabled` | `True` |
| `agents.followup_automation.max_followups` | `5` |
| `agents.followup_automation.followup_intervals_days` | `1, 3, 7, 14, 30` |
| `agents.followup_automation.templates.initial` | `templates/followup_initial.md` |
| `agents.followup_automation.templates.reminder` | `templates/followup_reminder.md` |
| `agents.followup_automation.templates.final` | `templates/followup_final.md` |
| `agents.performance_analytics.enabled` | `True` |
| `agents.performance_analytics.metrics_refresh_interval_minutes` | `15` |
| `agents.performance_analytics.retention_days` | `365` |
| `agents.performance_analytics.dashboards` | `sales_performance, pipeline_health, agent_effectiveness` |
| `integrations.salesforce.enabled` | `False` |
| `integrations.salesforce.api_version` | `v58.0` |
| `integrations.salesforce.sandbox` | `False` |
| `integrations.salesforce.batch_size` | `200` |
| `integrations.hubspot.enabled` | `False` |
| `integrations.hubspot.api_version` | `v3` |
| `integrations.hubspot.rate_limit_per_second` | `10` |
| `integrations.pipedrive.enabled` | `False` |
| `integrations.pipedrive.api_version` | `v1` |
| `integrations.pipedrive.rate_limit_per_second` | `5` |
| `monitoring.prometheus.enabled` | `True` |
| `monitoring.prometheus.port` | `9090` |
| `monitoring.health_check.interval_seconds` | `30` |
| `monitoring.health_check.timeout_seconds` | `10` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `ENVIRONMENT` | `development` | Application |
| `LOG_LEVEL` | `DEBUG` | Application |
| `SECRET_KEY` | `change-me-in-production` | Application |
| `HOST` | `0.0.0.0` | Server |
| `PORT` | `8000` | Server |
| `SALESFORCE_CLIENT_ID` | `` | Salesforce |
| `SALESFORCE_CLIENT_SECRET` | `` | Salesforce |
| `SALESFORCE_USERNAME` | `` | Salesforce |
| `SALESFORCE_PASSWORD` | `` | Salesforce |
| `SALESFORCE_SECURITY_TOKEN` | `` | Salesforce |
| `SALESFORCE_SANDBOX` | `false` | Salesforce |
| `HUBSPOT_API_KEY` | `` | HubSpot |
| `HUBSPOT_APP_ID` | `` | HubSpot |
| `PIPEDRIVE_API_TOKEN` | `` | Pipedrive |
| `PIPEDRIVE_COMPANY_DOMAIN` | `` | Pipedrive |
| `OPENAI_API_KEY` | `` | LangChain / LLM |
| `LANGCHAIN_API_KEY` | `` | LangChain / LLM |
| `LANGCHAIN_TRACING_V2` | `false` | LangChain / LLM |
| `LANGCHAIN_PROJECT` | `crm-enhancer` | LangChain / LLM |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis (for caching and task queue) |
| `PROMETHEUS_PORT` | `9090` | Monitoring |
| `SENTRY_DSN` | `` | Monitoring |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: CRM Enhancer
  version: 0.1.0
  environment: development
  log_level: INFO
  host: 0.0.0.0
  port: 8000
agents:
  contact_enrichment:
    enabled: True
    max_retries: 3
    timeout_seconds: 30
    enrichment_sources:
      - clearbit
      - zoominfo
      - hunter
  deal_scoring:
    enabled: True
    model_path: models/deal_scorer.pkl
    scoring_factors:
      - deal_size
      - stage_progression
      - engagement_level
      - company_fit
      - timeline
    weights:
      deal_size: 0.25
      stage_progression: 0.2
      engagement_level: 0.25
      company_fit: 0.15
      timeline: 0.15
  task_automation:
    enabled: True
    max_concurrent_tasks: 10
    default_priority: medium
    auto_assign: True
  meeting_scheduling:
    enabled: True
    default_duration_minutes: 30
    buffer_minutes: 15
    timezone: UTC
    working_hours:
      start: 09:00
      end: 17:00
  followup_automation:
    enabled: True
    max_followups: 5
    followup_intervals_days:
      - 1
      - 3
      - 7
      - 14
      - 30
    templates:
      initial: templates/followup_initial.md
      reminder: templates/followup_reminder.md
      final: templates/followup_final.md
  performance_analytics:
    enabled: True
    metrics_refresh_interval_minutes: 15
    retention_days: 365
    dashboards:
      - sales_performance
      - pipeline_health
      - agent_effectiveness
integrations:
  salesforce:
    enabled: False
    api_version: v58.0
    sandbox: False
    batch_size: 200
  hubspot:
    enabled: False
    api_version: v3
    rate_limit_per_second: 10
  pipedrive:
    enabled: False
    api_version: v1
    rate_limit_per_second: 5
monitoring:
  prometheus:
    enabled: True
    port: 9090
  health_check:
    interval_seconds: 30
    timeout_seconds: 10
```

---

## Example .env File

```bash
# Application
ENVIRONMENT=development
LOG_LEVEL=DEBUG
SECRET_KEY=change-me-in-production

# Server
HOST=0.0.0.0
PORT=8000

# Salesforce
SALESFORCE_CLIENT_ID=
SALESFORCE_CLIENT_SECRET=
SALESFORCE_USERNAME=
SALESFORCE_PASSWORD=
SALESFORCE_SECURITY_TOKEN=
SALESFORCE_SANDBOX=false

# HubSpot
HUBSPOT_API_KEY=
HUBSPOT_APP_ID=

# Pipedrive
PIPEDRIVE_API_TOKEN=
PIPEDRIVE_COMPANY_DOMAIN=

# LangChain / LLM
OPENAI_API_KEY=
LANGCHAIN_API_KEY=
LANGCHAIN_TRACING_V2=false
LANGCHAIN_PROJECT=crm-enhancer

# Redis (for caching and task queue)
REDIS_URL=redis://localhost:6379/0

# Monitoring
PROMETHEUS_PORT=9090
SENTRY_DSN=

```

---

## Agent Configuration

```yaml
agents:
  contact_enrichment:
    enabled: true
    enrichment_sources:
    - clearbit
    - zoominfo
    - hunter
    max_retries: 3
    timeout_seconds: 30
  deal_scoring:
    enabled: true
    model_path: models/deal_scorer.pkl
    scoring_factors:
    - deal_size
    - stage_progression
    - engagement_level
    - company_fit
    - timeline
    weights:
      company_fit: 0.15
      deal_size: 0.25
      engagement_level: 0.25
      stage_progression: 0.2
      timeline: 0.15
  followup_automation:
    enabled: true
    followup_intervals_days:
    - 1
    - 3
    - 7
    - 14
    - 30
    max_followups: 5
    templates:
      final: templates/followup_final.md
      initial: templates/followup_initial.md
      reminder: templates/followup_reminder.md
  meeting_scheduling:
    buffer_minutes: 15
    default_duration_minutes: 30
    enabled: true
    timezone: UTC
    working_hours:
      end: '17:00'
      start: 09:00
  performance_analytics:
    dashboards:
    - sales_performance
    - pipeline_health
    - agent_effectiveness
    enabled: true
    metrics_refresh_interval_minutes: 15
    retention_days: 365
  task_automation:
    auto_assign: true
    default_priority: medium
    enabled: true
    max_concurrent_tasks: 10
```

---

## Integration Settings

```yaml
integrations:
  hubspot:
    api_version: v3
    enabled: false
    rate_limit_per_second: 10
  pipedrive:
    api_version: v1
    enabled: false
    rate_limit_per_second: 5
  salesforce:
    api_version: v58.0
    batch_size: 200
    enabled: false
    sandbox: false
```

---

## Security Configuration

No explicit security configuration found. See environment variables for API keys and secrets.

---

## Monitoring & Observability

### monitoring

```yaml
monitoring:
  health_check:
    interval_seconds: 30
    timeout_seconds: 10
  prometheus:
    enabled: true
    port: 9090
```

---

## Rate Limiting & Caching

No explicit rate limiting or caching configuration found.

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/crm-enhancer
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

*Generated for `crm-enhancer` — GRC_Claw Configuration Guide*
