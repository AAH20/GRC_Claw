# Sales Automator — Configuration Guide

> Sales automation platform for prospecting, outreach, qualification, demo scheduling, and follow-up automation.

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

The **sales-automator** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/sales-automator/
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
| `app.name` | `sales-automator` |
| `app.version` | `0.1.0` |
| `app.environment` | `development` |
| `app.log_level` | `INFO` |
| `server.host` | `0.0.0.0` |
| `server.port` | `8000` |
| `server.workers` | `1` |
| `agents.prospecting.enabled` | `True` |
| `agents.prospecting.max_concurrent` | `5` |
| `agents.prospecting.scoring_threshold` | `0.6` |
| `agents.prospecting.sources` | `linkedin, web` |
| `agents.outreach.enabled` | `True` |
| `agents.outreach.max_concurrent` | `3` |
| `agents.outreach.channels` | `email, linkedin, call` |
| `agents.outreach.templates.initial_contact` | `initial_contact` |
| `agents.outreach.templates.follow_up` | `follow_up` |
| `agents.outreach.templates.break_up` | `break_up` |
| `agents.qualification.enabled` | `True` |
| `agents.qualification.max_concurrent` | `3` |
| `agents.qualification.framework` | `bant` |
| `agents.qualification.min_score` | `0.5` |
| `agents.demo_scheduling.enabled` | `True` |
| `agents.demo_scheduling.max_concurrent` | `2` |
| `agents.demo_scheduling.calendar_provider` | `google_calendar` |
| `agents.demo_scheduling.default_duration_minutes` | `30` |
| `agents.demo_scheduling.buffer_minutes` | `15` |
| `agents.followup.enabled` | `True` |
| `agents.followup.max_concurrent` | `3` |
| `agents.followup.cadence_days` | `3` |
| `agents.followup.max_touches` | `5` |
| `agents.sales_forecasting.enabled` | `True` |
| `agents.sales_forecasting.max_concurrent` | `1` |
| `agents.sales_forecasting.forecast_horizon_days` | `90` |
| `agents.sales_forecasting.confidence_interval` | `0.95` |
| `integrations.salesforce.enabled` | `True` |
| `integrations.salesforce.api_version` | `v59.0` |
| `integrations.salesforce.sandbox` | `False` |
| `integrations.hubspot.enabled` | `True` |
| `integrations.hubspot.api_version` | `v3` |
| `integrations.linkedin.enabled` | `True` |
| `integrations.linkedin.api_version` | `v2` |
| `integrations.google_calendar.enabled` | `True` |
| `integrations.google_calendar.timezone` | `UTC` |
| `llm.provider` | `openai` |
| `llm.model` | `gpt-4o` |
| `llm.temperature` | `0.7` |
| `llm.max_tokens` | `2048` |
| `llm.timeout_seconds` | `60` |
| `monitoring.metrics_enabled` | `True` |
| `monitoring.metrics_port` | `9090` |
| `monitoring.tracing_enabled` | `False` |

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
| `OPENAI_API_KEY` | `sk-your-openai-api-key` | LLM |
| `LLM_MODEL` | `gpt-4o` | LLM |
| `LLM_TEMPERATURE` | `0.7` | LLM |
| `LLM_MAX_TOKENS` | `2048` | LLM |
| `SALESFORCE_CLIENT_ID` | `your-salesforce-client-id` | Salesforce |
| `SALESFORCE_CLIENT_SECRET` | `your-salesforce-client-secret` | Salesforce |
| `SALESFORCE_USERNAME` | `your-salesforce-username` | Salesforce |
| `SALESFORCE_PASSWORD` | `your-salesforce-password` | Salesforce |
| `SALESFORCE_SECURITY_TOKEN` | `your-salesforce-security-token` | Salesforce |
| `SALESFORCE_SANDBOX` | `false` | Salesforce |
| `HUBSPOT_API_KEY` | `your-hubspot-api-key` | HubSpot |
| `HUBSPOT_PORTAL_ID` | `your-hubspot-portal-id` | HubSpot |
| `LINKEDIN_CLIENT_ID` | `your-linkedin-client-id` | LinkedIn |
| `LINKEDIN_CLIENT_SECRET` | `your-linkedin-client-secret` | LinkedIn |
| `LINKEDIN_ACCESS_TOKEN` | `your-linkedin-access-token` | LinkedIn |
| `GOOGLE_CALENDAR_CREDENTIALS_PATH` | `/path/to/credentials.json` | Google Calendar |
| `GOOGLE_CALENDAR_TOKEN_PATH` | `/path/to/token.json` | Google Calendar |
| `GOOGLE_CALENDAR_PRIMARY_CALENDAR_ID` | `primary` | Google Calendar |
| `METRICS_ENABLED` | `true` | Monitoring |
| `METRICS_PORT` | `9090` | Monitoring |
| `TRACING_ENABLED` | `false` | Monitoring |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: sales-automator
  version: 0.1.0
  environment: development
  log_level: INFO
server:
  host: 0.0.0.0
  port: 8000
  workers: 1
agents:
  prospecting:
    enabled: True
    max_concurrent: 5
    scoring_threshold: 0.6
    sources:
      - linkedin
      - web
  outreach:
    enabled: True
    max_concurrent: 3
    channels:
      - email
      - linkedin
      - call
    templates:
      initial_contact: initial_contact
      follow_up: follow_up
      break_up: break_up
  qualification:
    enabled: True
    max_concurrent: 3
    framework: bant
    min_score: 0.5
  demo_scheduling:
    enabled: True
    max_concurrent: 2
    calendar_provider: google_calendar
    default_duration_minutes: 30
    buffer_minutes: 15
  followup:
    enabled: True
    max_concurrent: 3
    cadence_days: 3
    max_touches: 5
  sales_forecasting:
    enabled: True
    max_concurrent: 1
    forecast_horizon_days: 90
    confidence_interval: 0.95
integrations:
  salesforce:
    enabled: True
    api_version: v59.0
    sandbox: False
  hubspot:
    enabled: True
    api_version: v3
  linkedin:
    enabled: True
    api_version: v2
  google_calendar:
    enabled: True
    timezone: UTC
llm:
  provider: openai
  model: gpt-4o
  temperature: 0.7
  max_tokens: 2048
  timeout_seconds: 60
monitoring:
  metrics_enabled: True
  metrics_port: 9090
  tracing_enabled: False
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

# LLM
OPENAI_API_KEY=sk-your-openai-api-key
LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048

# Salesforce
SALESFORCE_CLIENT_ID=your-salesforce-client-id
SALESFORCE_CLIENT_SECRET=your-salesforce-client-secret
SALESFORCE_USERNAME=your-salesforce-username
SALESFORCE_PASSWORD=your-salesforce-password
SALESFORCE_SECURITY_TOKEN=your-salesforce-security-token
SALESFORCE_SANDBOX=false

# HubSpot
HUBSPOT_API_KEY=your-hubspot-api-key
HUBSPOT_PORTAL_ID=your-hubspot-portal-id

# LinkedIn
LINKEDIN_CLIENT_ID=your-linkedin-client-id
LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret
LINKEDIN_ACCESS_TOKEN=your-linkedin-access-token

# Google Calendar
GOOGLE_CALENDAR_CREDENTIALS_PATH=/path/to/credentials.json
GOOGLE_CALENDAR_TOKEN_PATH=/path/to/token.json
GOOGLE_CALENDAR_PRIMARY_CALENDAR_ID=primary

# Monitoring
METRICS_ENABLED=true
METRICS_PORT=9090
TRACING_ENABLED=false

```

---

## Agent Configuration

```yaml
agents:
  demo_scheduling:
    buffer_minutes: 15
    calendar_provider: google_calendar
    default_duration_minutes: 30
    enabled: true
    max_concurrent: 2
  followup:
    cadence_days: 3
    enabled: true
    max_concurrent: 3
    max_touches: 5
  outreach:
    channels:
    - email
    - linkedin
    - call
    enabled: true
    max_concurrent: 3
    templates:
      break_up: break_up
      follow_up: follow_up
      initial_contact: initial_contact
  prospecting:
    enabled: true
    max_concurrent: 5
    scoring_threshold: 0.6
    sources:
    - linkedin
    - web
  qualification:
    enabled: true
    framework: bant
    max_concurrent: 3
    min_score: 0.5
  sales_forecasting:
    confidence_interval: 0.95
    enabled: true
    forecast_horizon_days: 90
    max_concurrent: 1
```

---

## Integration Settings

```yaml
integrations:
  google_calendar:
    enabled: true
    timezone: UTC
  hubspot:
    api_version: v3
    enabled: true
  linkedin:
    api_version: v2
    enabled: true
  salesforce:
    api_version: v59.0
    enabled: true
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
  metrics_enabled: true
  metrics_port: 9090
  tracing_enabled: false
```

---

## Rate Limiting & Caching

No explicit rate limiting or caching configuration found.

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/sales-automator
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

*Generated for `sales-automator` — GRC_Claw Configuration Guide*
