# Finance Marketing — Configuration Guide

> Finance marketing platform with FINRA/SEC compliance, financial content generation, and regulatory adherence.

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

The **finance-marketing** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/finance-marketing/
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
| `app.name` | `Finance Marketing` |
| `app.version` | `0.1.0` |
| `app.env` | `dev` |
| `app.log_level` | `INFO` |
| `app.debug` | `False` |
| `server.host` | `0.0.0.0` |
| `server.port` | `8000` |
| `server.workers` | `4` |
| `server.timeout` | `30` |
| `database.url` | `postgresql://localhost:5432/finance_marketing` |
| `database.pool_size` | `10` |
| `database.max_overflow` | `20` |
| `database.pool_timeout` | `30` |
| `database.echo` | `False` |
| `redis.url` | `redis://localhost:6379` |
| `redis.db` | `0` |
| `redis.max_connections` | `50` |
| `security.secret_key` | `change-me-in-production` |
| `security.algorithm` | `HS256` |
| `security.access_token_expire_minutes` | `30` |
| `security.allowed_hosts` | `localhost, 127.0.0.1` |
| `compliance.finra.enabled` | `True` |
| `compliance.finra.require_pre_approval` | `True` |
| `compliance.finra.prohibited_terms` | `guaranteed returns, risk-free, can't lose, no risk, sure thing` |
| `compliance.finra.required_disclosures` | `Investing involves risk including possible loss of principal.` |
| `compliance.sec.enabled` | `True` |
| `compliance.sec.require_substantiation` | `True` |
| `compliance.sec.prohibited_claims` | `past performance guarantees future results` |
| `compliance.audit.enabled` | `True` |
| `compliance.audit.retention_days` | `2555` |
| `compliance.audit.log_all_content` | `True` |
| `agents.content.model` | `gpt-4` |
| `agents.content.temperature` | `0.7` |
| `agents.content.max_tokens` | `2000` |
| `agents.content.timeout` | `60` |
| `agents.compliance.model` | `gpt-4` |
| `agents.compliance.temperature` | `0.1` |
| `agents.compliance.max_tokens` | `4000` |
| `agents.compliance.timeout` | `30` |
| `agents.campaigns.model` | `gpt-4` |
| `agents.campaigns.temperature` | `0.5` |
| `agents.campaigns.max_tokens` | `2000` |
| `agents.campaigns.timeout` | `60` |
| `agents.analytics.model` | `gpt-4` |
| `agents.analytics.temperature` | `0.3` |
| `agents.analytics.max_tokens` | `2000` |
| `agents.analytics.timeout` | `60` |
| `agents.reporting.model` | `gpt-4` |
| `agents.reporting.temperature` | `0.2` |
| `agents.reporting.max_tokens` | `4000` |
| `agents.reporting.timeout` | `60` |
| `integrations.salesforce.enabled` | `False` |
| `integrations.salesforce.api_version` | `v58.0` |
| `integrations.salesforce.timeout` | `30` |
| `integrations.salesforce.max_retries` | `3` |
| `integrations.hubspot.enabled` | `False` |
| `integrations.hubspot.api_version` | `v3` |
| `integrations.hubspot.timeout` | `30` |
| `integrations.hubspot.max_retries` | `3` |
| `integrations.mailchimp.enabled` | `False` |
| `integrations.mailchimp.api_version` | `3.0` |
| `integrations.mailchimp.timeout` | `30` |
| `integrations.mailchimp.max_retries` | `3` |
| `logging.format` | `json` |
| `logging.include_timestamp` | `True` |
| `logging.include_correlation_id` | `True` |
| `logging.redact_fields` | `password, token, api_key, secret, authorization` |
| `metrics.enabled` | `True` |
| `metrics.port` | `9090` |
| `metrics.path` | `/metrics` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `APP_ENV` | `dev` | Application |
| `LOG_LEVEL` | `DEBUG` | Application |
| `DEBUG` | `true` | Application |
| `SECRET_KEY` | `change-me-to-a-secure-random-string` | Application |
| `HOST` | `0.0.0.0` | Server |
| `PORT` | `8000` | Server |
| `WORKERS` | `4` | Server |
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/finance_marketing` | Database |
| `DATABASE_POOL_SIZE` | `10` | Database |
| `DATABASE_MAX_OVERFLOW` | `20` | Database |
| `REDIS_URL` | `redis://localhost:6379` | Redis |
| `REDIS_DB` | `0` | Redis |
| `OPENAI_API_KEY` | `sk-your-openai-api-key` | LangChain / LLM |
| `LANGCHAIN_API_KEY` | `lsv2-your-langchain-api-key` | LangChain / LLM |
| `LANGCHAIN_TRACING_V2` | `true` | LangChain / LLM |
| `LANGCHAIN_PROJECT` | `finance-marketing` | LangChain / LLM |
| `SALESFORCE_CLIENT_ID` | `your-salesforce-client-id` | Salesforce |
| `SALESFORCE_CLIENT_SECRET` | `your-salesforce-client-secret` | Salesforce |
| `SALESFORCE_USERNAME` | `your-salesforce-username` | Salesforce |
| `SALESFORCE_PASSWORD` | `your-salesforce-password` | Salesforce |
| `SALESFORCE_SECURITY_TOKEN` | `your-salesforce-security-token` | Salesforce |
| `SALESFORCE_DOMAIN` | `login` | Salesforce |
| `HUBSPOT_API_KEY` | `your-hubspot-api-key` | HubSpot |
| `HUBSPOT_PORTAL_ID` | `your-hubspot-portal-id` | HubSpot |
| `MAILCHIMP_API_KEY` | `your-mailchimp-api-key` | Mailchimp |
| `MAILCHIMP_SERVER_PREFIX` | `us1` | Mailchimp |
| `MAILCHIMP_LIST_ID` | `your-audience-list-id` | Mailchimp |
| `COMPLIANCE_PRE_APPROVAL_REQUIRED` | `true` | Compliance |
| `COMPLIANCE_AUDIT_RETENTION_DAYS` | `2555` | Compliance |
| `COMPLIANCE_LOG_ALL_CONTENT` | `true` | Compliance |
| `PROMETHEUS_ENABLED` | `true` | Monitoring |
| `PROMETHEUS_PORT` | `9090` | Monitoring |
| `SENTRY_DSN` | `your-sentry-dsn` | Monitoring |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: Finance Marketing
  version: 0.1.0
  env: dev
  log_level: INFO
  debug: False
server:
  host: 0.0.0.0
  port: 8000
  workers: 4
  timeout: 30
database:
  url: postgresql://localhost:5432/finance_marketing
  pool_size: 10
  max_overflow: 20
  pool_timeout: 30
  echo: False
redis:
  url: redis://localhost:6379
  db: 0
  max_connections: 50
security:
  secret_key: change-me-in-production
  algorithm: HS256
  access_token_expire_minutes: 30
  allowed_hosts:
    - localhost
    - 127.0.0.1
compliance:
  finra:
    enabled: True
    require_pre_approval: True
    prohibited_terms:
      - guaranteed returns
      - risk-free
      - can't lose
      - no risk
      - sure thing
    required_disclosures:
      - Investing involves risk including possible loss of principal.
  sec:
    enabled: True
    require_substantiation: True
    prohibited_claims:
      - past performance guarantees future results
  audit:
    enabled: True
    retention_days: 2555
    log_all_content: True
agents:
  content:
    model: gpt-4
    temperature: 0.7
    max_tokens: 2000
    timeout: 60
  compliance:
    model: gpt-4
    temperature: 0.1
    max_tokens: 4000
    timeout: 30
  campaigns:
    model: gpt-4
    temperature: 0.5
    max_tokens: 2000
    timeout: 60
  analytics:
    model: gpt-4
    temperature: 0.3
    max_tokens: 2000
    timeout: 60
  reporting:
    model: gpt-4
    temperature: 0.2
    max_tokens: 4000
    timeout: 60
integrations:
  salesforce:
    enabled: False
    api_version: v58.0
    timeout: 30
    max_retries: 3
  hubspot:
    enabled: False
    api_version: v3
    timeout: 30
    max_retries: 3
  mailchimp:
    enabled: False
    api_version: 3.0
    timeout: 30
    max_retries: 3
logging:
  format: json
  include_timestamp: True
  include_correlation_id: True
  redact_fields:
    - password
    - token
    - api_key
    - secret
    - authorization
metrics:
  enabled: True
  port: 9090
  path: /metrics
```

---

## Example .env File

```bash
# Finance Marketing Platform - Environment Variables
# Copy this file to .env and fill in your values

# Application
APP_ENV=dev
LOG_LEVEL=DEBUG
DEBUG=true
SECRET_KEY=change-me-to-a-secure-random-string

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/finance_marketing
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://localhost:6379
REDIS_DB=0

# LangChain / LLM
OPENAI_API_KEY=sk-your-openai-api-key
LANGCHAIN_API_KEY=lsv2-your-langchain-api-key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=finance-marketing

# Salesforce
SALESFORCE_CLIENT_ID=your-salesforce-client-id
SALESFORCE_CLIENT_SECRET=your-salesforce-client-secret
SALESFORCE_USERNAME=your-salesforce-username
SALESFORCE_PASSWORD=your-salesforce-password
SALESFORCE_SECURITY_TOKEN=your-salesforce-security-token
SALESFORCE_DOMAIN=login

# HubSpot
HUBSPOT_API_KEY=your-hubspot-api-key
HUBSPOT_PORTAL_ID=your-hubspot-portal-id

# Mailchimp
MAILCHIMP_API_KEY=your-mailchimp-api-key
MAILCHIMP_SERVER_PREFIX=us1
MAILCHIMP_LIST_ID=your-audience-list-id

# Compliance
COMPLIANCE_PRE_APPROVAL_REQUIRED=true
COMPLIANCE_AUDIT_RETENTION_DAYS=2555
COMPLIANCE_LOG_ALL_CONTENT=true

# Monitoring
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
SENTRY_DSN=your-sentry-dsn

```

---

## Agent Configuration

```yaml
agents:
  analytics:
    max_tokens: 2000
    model: gpt-4
    temperature: 0.3
    timeout: 60
  campaigns:
    max_tokens: 2000
    model: gpt-4
    temperature: 0.5
    timeout: 60
  compliance:
    max_tokens: 4000
    model: gpt-4
    temperature: 0.1
    timeout: 30
  content:
    max_tokens: 2000
    model: gpt-4
    temperature: 0.7
    timeout: 60
  reporting:
    max_tokens: 4000
    model: gpt-4
    temperature: 0.2
    timeout: 60
```

---

## Integration Settings

```yaml
integrations:
  hubspot:
    api_version: v3
    enabled: false
    max_retries: 3
    timeout: 30
  mailchimp:
    api_version: '3.0'
    enabled: false
    max_retries: 3
    timeout: 30
  salesforce:
    api_version: v58.0
    enabled: false
    max_retries: 3
    timeout: 30
```

---

## Security Configuration

### security

```yaml
security:
  access_token_expire_minutes: 30
  algorithm: HS256
  allowed_hosts:
  - localhost
  - 127.0.0.1
  secret_key: change-me-in-production
```

### compliance

```yaml
compliance:
  audit:
    enabled: true
    log_all_content: true
    retention_days: 2555
  finra:
    enabled: true
    prohibited_terms:
    - guaranteed returns
    - risk-free
    - can't lose
    - no risk
    - sure thing
    require_pre_approval: true
    required_disclosures:
    - Investing involves risk including possible loss of principal.
  sec:
    enabled: true
    prohibited_claims:
    - past performance guarantees future results
    require_substantiation: true
```

---

## Monitoring & Observability

### metrics

```yaml
metrics:
  enabled: true
  path: /metrics
  port: 9090
```

---

## Rate Limiting & Caching

### redis

```yaml
redis:
  db: 0
  max_connections: 50
  url: redis://localhost:6379
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/finance-marketing
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

*Generated for `finance-marketing` — GRC_Claw Configuration Guide*
