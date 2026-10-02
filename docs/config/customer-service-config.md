# Customer Service — Configuration Guide

> AI-powered customer service platform with triage, resolution, escalation, sentiment analysis, and customer success agents.

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

The **customer-service** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/customer-service/
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
| `app.name` | `customer-service` |
| `app.version` | `0.1.0` |
| `app.environment` | `development` |
| `app.log_level` | `DEBUG` |
| `app.host` | `0.0.0.0` |
| `app.port` | `8000` |
| `agents.triage.model` | `gpt-4o` |
| `agents.triage.temperature` | `0.1` |
| `agents.triage.max_tokens` | `1024` |
| `agents.triage.timeout_seconds` | `30` |
| `agents.triage.categories` | `billing, technical, account, general, complaint` |
| `agents.triage.priority_levels` | `low, medium, high, critical` |
| `agents.resolution.model` | `gpt-4o` |
| `agents.resolution.temperature` | `0.3` |
| `agents.resolution.max_tokens` | `2048` |
| `agents.resolution.timeout_seconds` | `60` |
| `agents.resolution.auto_reply_enabled` | `False` |
| `agents.resolution.confidence_threshold` | `0.85` |
| `agents.escalation.model` | `gpt-4o` |
| `agents.escalation.temperature` | `0.1` |
| `agents.escalation.max_tokens` | `1024` |
| `agents.escalation.timeout_seconds` | `30` |
| `agents.escalation.escalation_threshold` | `0.7` |
| `agents.escalation.human_handoff_enabled` | `True` |
| `agents.sentiment_analysis.model` | `gpt-4o` |
| `agents.sentiment_analysis.temperature` | `0.1` |
| `agents.sentiment_analysis.max_tokens` | `512` |
| `agents.sentiment_analysis.timeout_seconds` | `15` |
| `agents.sentiment_analysis.sentiment_scale` | `5` |
| `agents.customer_success.model` | `gpt-4o` |
| `agents.customer_success.temperature` | `0.3` |
| `agents.customer_success.max_tokens` | `1024` |
| `agents.customer_success.timeout_seconds` | `30` |
| `agents.customer_success.churn_risk_threshold` | `0.6` |
| `agents.customer_success.proactive_outreach_enabled` | `True` |
| `integrations.zendesk.base_url` | `https://your-subdomain.zendesk.com` |
| `integrations.zendesk.api_version` | `v2` |
| `integrations.zendesk.timeout_seconds` | `30` |
| `integrations.zendesk.retry_attempts` | `3` |
| `integrations.zendesk.rate_limit_per_minute` | `100` |
| `integrations.intercom.base_url` | `https://api.intercom.io` |
| `integrations.intercom.api_version` | `2.0` |
| `integrations.intercom.timeout_seconds` | `30` |
| `integrations.intercom.retry_attempts` | `3` |
| `integrations.intercom.rate_limit_per_minute` | `100` |
| `integrations.salesforce.base_url` | `https://your-instance.salesforce.com` |
| `integrations.salesforce.api_version` | `v58.0` |
| `integrations.salesforce.timeout_seconds` | `30` |
| `integrations.salesforce.retry_attempts` | `3` |
| `integrations.salesforce.rate_limit_per_minute` | `100` |
| `monitoring.prometheus_enabled` | `True` |
| `monitoring.metrics_port` | `9090` |
| `monitoring.health_check_interval_seconds` | `30` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `ENVIRONMENT` | `development` | Application |
| `LOG_LEVEL` | `DEBUG` | Application |
| `SECRET_KEY` | `change-me-in-production` | Application |
| `OPENAI_API_KEY` | `sk-your-openai-api-key` | OpenAI (required for LangChain DeepAgents) |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI (required for LangChain DeepAgents) |
| `LANGCHAIN_TRACING_V2` | `false` | LangChain |
| `LANGCHAIN_API_KEY` | `your-langsmith-api-key` | LangChain |
| `LANGCHAIN_PROJECT` | `customer-service` | LangChain |
| `ZENDESK_SUBDOMAIN` | `your-subdomain` | Zendesk |
| `ZENDESK_EMAIL` | `your-email@example.com` | Zendesk |
| `ZENDESK_API_TOKEN` | `your-zendesk-api-token` | Zendesk |
| `INTERCOM_ACCESS_TOKEN` | `your-intercom-access-token` | Intercom |
| `INTERCOM_WORKSPACE_ID` | `your-workspace-id` | Intercom |
| `SALESFORCE_USERNAME` | `your-username@example.com` | Salesforce |
| `SALESFORCE_PASSWORD` | `your-password` | Salesforce |
| `SALESFORCE_SECURITY_TOKEN` | `your-security-token` | Salesforce |
| `SALESFORCE_CLIENT_ID` | `your-oauth-client-id` | Salesforce |
| `SALESFORCE_CLIENT_SECRET` | `your-oauth-client-secret` | Salesforce |
| `SALESFORCE_DOMAIN` | `login` | Salesforce |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis (for caching/sessions) |
| `PROMETHEUS_ENABLED` | `true` | Monitoring |
| `SENTRY_DSN` | `your-sentry-dsn` | Monitoring |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: customer-service
  version: 0.1.0
  environment: development
  log_level: DEBUG
  host: 0.0.0.0
  port: 8000
agents:
  triage:
    model: gpt-4o
    temperature: 0.1
    max_tokens: 1024
    timeout_seconds: 30
    categories:
      - billing
      - technical
      - account
      - general
      - complaint
    priority_levels:
      - low
      - medium
      - high
      - critical
  resolution:
    model: gpt-4o
    temperature: 0.3
    max_tokens: 2048
    timeout_seconds: 60
    auto_reply_enabled: False
    confidence_threshold: 0.85
  escalation:
    model: gpt-4o
    temperature: 0.1
    max_tokens: 1024
    timeout_seconds: 30
    escalation_threshold: 0.7
    human_handoff_enabled: True
  sentiment_analysis:
    model: gpt-4o
    temperature: 0.1
    max_tokens: 512
    timeout_seconds: 15
    sentiment_scale: 5
  customer_success:
    model: gpt-4o
    temperature: 0.3
    max_tokens: 1024
    timeout_seconds: 30
    churn_risk_threshold: 0.6
    proactive_outreach_enabled: True
integrations:
  zendesk:
    base_url: https://your-subdomain.zendesk.com
    api_version: v2
    timeout_seconds: 30
    retry_attempts: 3
    rate_limit_per_minute: 100
  intercom:
    base_url: https://api.intercom.io
    api_version: 2.0
    timeout_seconds: 30
    retry_attempts: 3
    rate_limit_per_minute: 100
  salesforce:
    base_url: https://your-instance.salesforce.com
    api_version: v58.0
    timeout_seconds: 30
    retry_attempts: 3
    rate_limit_per_minute: 100
monitoring:
  prometheus_enabled: True
  metrics_port: 9090
  health_check_interval_seconds: 30
```

---

## Example .env File

```bash
# Application
ENVIRONMENT=development
LOG_LEVEL=DEBUG
SECRET_KEY=change-me-in-production

# OpenAI (required for LangChain DeepAgents)
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o

# LangChain
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=your-langsmith-api-key
LANGCHAIN_PROJECT=customer-service

# Zendesk
ZENDESK_SUBDOMAIN=your-subdomain
ZENDESK_EMAIL=your-email@example.com
ZENDESK_API_TOKEN=your-zendesk-api-token

# Intercom
INTERCOM_ACCESS_TOKEN=your-intercom-access-token
INTERCOM_WORKSPACE_ID=your-workspace-id

# Salesforce
SALESFORCE_USERNAME=your-username@example.com
SALESFORCE_PASSWORD=your-password
SALESFORCE_SECURITY_TOKEN=your-security-token
SALESFORCE_CLIENT_ID=your-oauth-client-id
SALESFORCE_CLIENT_SECRET=your-oauth-client-secret
SALESFORCE_DOMAIN=login

# Redis (for caching/sessions)
REDIS_URL=redis://localhost:6379/0

# Monitoring
PROMETHEUS_ENABLED=true
SENTRY_DSN=your-sentry-dsn

```

---

## Agent Configuration

```yaml
agents:
  customer_success:
    churn_risk_threshold: 0.6
    max_tokens: 1024
    model: gpt-4o
    proactive_outreach_enabled: true
    temperature: 0.3
    timeout_seconds: 30
  escalation:
    escalation_threshold: 0.7
    human_handoff_enabled: true
    max_tokens: 1024
    model: gpt-4o
    temperature: 0.1
    timeout_seconds: 30
  resolution:
    auto_reply_enabled: false
    confidence_threshold: 0.85
    max_tokens: 2048
    model: gpt-4o
    temperature: 0.3
    timeout_seconds: 60
  sentiment_analysis:
    max_tokens: 512
    model: gpt-4o
    sentiment_scale: 5
    temperature: 0.1
    timeout_seconds: 15
  triage:
    categories:
    - billing
    - technical
    - account
    - general
    - complaint
    max_tokens: 1024
    model: gpt-4o
    priority_levels:
    - low
    - medium
    - high
    - critical
    temperature: 0.1
    timeout_seconds: 30
```

---

## Integration Settings

```yaml
integrations:
  intercom:
    api_version: '2.0'
    base_url: https://api.intercom.io
    rate_limit_per_minute: 100
    retry_attempts: 3
    timeout_seconds: 30
  salesforce:
    api_version: v58.0
    base_url: https://your-instance.salesforce.com
    rate_limit_per_minute: 100
    retry_attempts: 3
    timeout_seconds: 30
  zendesk:
    api_version: v2
    base_url: https://your-subdomain.zendesk.com
    rate_limit_per_minute: 100
    retry_attempts: 3
    timeout_seconds: 30
```

---

## Security Configuration

No explicit security configuration found. See environment variables for API keys and secrets.

---

## Monitoring & Observability

### monitoring

```yaml
monitoring:
  health_check_interval_seconds: 30
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
cd ~/GRC_Claw/projects/customer-service
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

*Generated for `customer-service` — GRC_Claw Configuration Guide*
