# Healthcare Marketing — Configuration Guide

> Healthcare marketing platform with HIPAA compliance, FDA guidelines, and healthcare-specific content generation.

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

The **healthcare-marketing** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/healthcare-marketing/
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
| `app.name` | `Healthcare Marketing Platform` |
| `app.version` | `0.1.0` |
| `app.environment` | `development` |
| `app.host` | `0.0.0.0` |
| `app.port` | `8000` |
| `app.debug` | `False` |
| `app.log_level` | `INFO` |
| `app.cors_origins` | `http://localhost:3000, https://healthcare-marketing.example.com` |
| `langchain.model_name` | `gpt-4` |
| `langchain.temperature` | `0.7` |
| `langchain.max_tokens` | `4096` |
| `langchain.timeout` | `60` |
| `langchain.max_retries` | `3` |
| `langchain.cache_enabled` | `True` |
| `agents.content.enabled` | `True` |
| `agents.content.max_content_length` | `10000` |
| `agents.content.supported_formats` | `blog_post, social_media, email, landing_page, video_script` |
| `agents.compliance.enabled` | `True` |
| `agents.compliance.strict_mode` | `True` |
| `agents.compliance.hipaa_validation` | `True` |
| `agents.compliance.fda_guidelines` | `True` |
| `agents.compliance.require_legal_review` | `True` |
| `agents.campaigns.enabled` | `True` |
| `agents.campaigns.max_concurrent_campaigns` | `10` |
| `agents.campaigns.default_duration_days` | `30` |
| `agents.campaigns.channels` | `email, social_media, paid_ads, content_marketing` |
| `agents.analytics.enabled` | `True` |
| `agents.analytics.metrics_retention_days` | `365` |
| `agents.analytics.real_time_tracking` | `True` |
| `agents.reporting.enabled` | `True` |
| `agents.reporting.default_format` | `pdf` |
| `agents.reporting.schedule` | `weekly` |
| `integrations.salesforce.enabled` | `False` |
| `integrations.salesforce.api_version` | `v58.0` |
| `integrations.salesforce.sandbox` | `False` |
| `integrations.salesforce.sync_interval_minutes` | `15` |
| `integrations.hubspot.enabled` | `False` |
| `integrations.hubspot.api_version` | `v3` |
| `integrations.hubspot.sync_interval_minutes` | `15` |
| `integrations.mailchimp.enabled` | `False` |
| `integrations.mailchimp.api_version` | `3.0` |
| `integrations.mailchimp.sync_interval_minutes` | `30` |
| `hipaa.encryption.algorithm` | `AES-256-GCM` |
| `hipaa.encryption.key_rotation_days` | `90` |
| `hipaa.audit_logging.enabled` | `True` |
| `hipaa.audit_logging.retention_days` | `2555` |
| `hipaa.audit_logging.log_level` | `detailed` |
| `hipaa.phi_detection.enabled` | `True` |
| `hipaa.phi_detection.auto_redact` | `True` |
| `hipaa.phi_detection.patterns` | `ssn, mrn, dob, phone, email, address` |
| `hipaa.access_control.session_timeout_minutes` | `30` |
| `hipaa.access_control.mfa_required` | `True` |
| `hipaa.access_control.max_failed_logins` | `5` |
| `database.pool_size` | `10` |
| `database.max_overflow` | `20` |
| `database.pool_timeout` | `30` |
| `database.echo` | `False` |
| `redis.db` | `0` |
| `redis.max_connections` | `50` |
| `redis.socket_timeout` | `5` |
| `monitoring.prometheus.enabled` | `True` |
| `monitoring.prometheus.port` | `9090` |
| `monitoring.health_check.interval_seconds` | `30` |
| `monitoring.health_check.timeout_seconds` | `10` |
| `monitoring.tracing.enabled` | `False` |
| `monitoring.tracing.jaeger_endpoint` | `http://jaeger:14268/api/traces` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `APP_NAME` | `Healthcare Marketing Platform` | Application |
| `APP_ENV` | `development` | Application |
| `APP_HOST` | `0.0.0.0` | Application |
| `APP_PORT` | `8000` | Application |
| `APP_DEBUG` | `false` | Application |
| `APP_SECRET_KEY` | `change-me-to-a-secure-random-string` | Application |
| `APP_LOG_LEVEL` | `INFO` | Application |
| `OPENAI_API_KEY` | `sk-your-openai-api-key` | LangChain / LLM |
| `LANGCHAIN_MODEL_NAME` | `gpt-4` | LangChain / LLM |
| `LANGCHAIN_TEMPERATURE` | `0.7` | LangChain / LLM |
| `LANGCHAIN_MAX_TOKENS` | `4096` | LangChain / LLM |
| `LANGCHAIN_TRACING_V2` | `false` | LangChain / LLM |
| `LANGCHAIN_PROJECT` | `healthcare-marketing` | LangChain / LLM |
| `DATABASE_URL` | `postgresql+asyncpg://user:password@localhost:5432/healthcare_marketing` | Database |
| `DATABASE_POOL_SIZE` | `10` | Database |
| `DATABASE_MAX_OVERFLOW` | `20` | Database |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis |
| `SALESFORCE_ENABLED` | `false` | Salesforce |
| `SALESFORCE_CLIENT_ID` | `your-salesforce-client-id` | Salesforce |
| `SALESFORCE_CLIENT_SECRET` | `your-salesforce-client-secret` | Salesforce |
| `SALESFORCE_USERNAME` | `your-salesforce-username` | Salesforce |
| `SALESFORCE_PASSWORD` | `your-salesforce-password` | Salesforce |
| `SALESFORCE_SECURITY_TOKEN` | `your-salesforce-security-token` | Salesforce |
| `SALESFORCE_SANDBOX` | `false` | Salesforce |
| `SALESFORCE_API_VERSION` | `v58.0` | Salesforce |
| `HUBSPOT_ENABLED` | `false` | HubSpot |
| `HUBSPOT_API_KEY` | `your-hubspot-api-key` | HubSpot |
| `HUBSPOT_PORTAL_ID` | `your-hubspot-portal-id` | HubSpot |
| `MAILCHIMP_ENABLED` | `false` | Mailchimp |
| `MAILCHIMP_API_KEY` | `your-mailchimp-api-key` | Mailchimp |
| `MAILCHIMP_SERVER_PREFIX` | `us1` | Mailchimp |
| `MAILCHIMP_LIST_ID` | `your-audience-list-id` | Mailchimp |
| `ENCRYPTION_KEY` | `your-32-byte-encryption-key-here` | HIPAA / Security |
| `ENCRYPTION_ALGORITHM` | `AES-256-GCM` | HIPAA / Security |
| `HIPAA_AUDIT_LOG_ENABLED` | `true` | HIPAA / Security |
| `HIPAA_PHI_DETECTION_ENABLED` | `true` | HIPAA / Security |
| `HIPAA_AUTO_REDACT` | `true` | HIPAA / Security |
| `HIPAA_SESSION_TIMEOUT_MINUTES` | `30` | HIPAA / Security |
| `HIPAA_MFA_REQUIRED` | `true` | HIPAA / Security |
| `JWT_SECRET_KEY` | `your-jwt-secret-key` | HIPAA / Security |
| `JWT_ALGORITHM` | `HS256` | HIPAA / Security |
| `JWT_EXPIRATION_HOURS` | `24` | HIPAA / Security |
| `PROMETHEUS_ENABLED` | `true` | Monitoring |
| `PROMETHEUS_PORT` | `9090` | Monitoring |
| `JAEGER_ENDPOINT` | `http://jaeger:14268/api/traces` | Monitoring |
| `SENTRY_DSN` | `` | Monitoring |
| `CORS_ORIGINS` | `http://localhost:3000,https://healthcare-marketing.example.com` | CORS |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: Healthcare Marketing Platform
  version: 0.1.0
  environment: development
  host: 0.0.0.0
  port: 8000
  debug: False
  log_level: INFO
  cors_origins:
    - http://localhost:3000
    - https://healthcare-marketing.example.com
langchain:
  model_name: gpt-4
  temperature: 0.7
  max_tokens: 4096
  timeout: 60
  max_retries: 3
  cache_enabled: True
agents:
  content:
    enabled: True
    max_content_length: 10000
    supported_formats:
      - blog_post
      - social_media
      - email
      - landing_page
      - video_script
  compliance:
    enabled: True
    strict_mode: True
    hipaa_validation: True
    fda_guidelines: True
    require_legal_review: True
  campaigns:
    enabled: True
    max_concurrent_campaigns: 10
    default_duration_days: 30
    channels:
      - email
      - social_media
      - paid_ads
      - content_marketing
  analytics:
    enabled: True
    metrics_retention_days: 365
    real_time_tracking: True
  reporting:
    enabled: True
    default_format: pdf
    schedule: weekly
integrations:
  salesforce:
    enabled: False
    api_version: v58.0
    sandbox: False
    sync_interval_minutes: 15
  hubspot:
    enabled: False
    api_version: v3
    sync_interval_minutes: 15
  mailchimp:
    enabled: False
    api_version: 3.0
    sync_interval_minutes: 30
hipaa:
  encryption:
    algorithm: AES-256-GCM
    key_rotation_days: 90
  audit_logging:
    enabled: True
    retention_days: 2555
    log_level: detailed
  phi_detection:
    enabled: True
    auto_redact: True
    patterns:
      - ssn
      - mrn
      - dob
      - phone
      - email
      - address
  access_control:
    session_timeout_minutes: 30
    mfa_required: True
    max_failed_logins: 5
database:
  pool_size: 10
  max_overflow: 20
  pool_timeout: 30
  echo: False
redis:
  db: 0
  max_connections: 50
  socket_timeout: 5
monitoring:
  prometheus:
    enabled: True
    port: 9090
  health_check:
    interval_seconds: 30
    timeout_seconds: 10
  tracing:
    enabled: False
    jaeger_endpoint: http://jaeger:14268/api/traces
```

---

## Example .env File

```bash
# Healthcare Marketing Platform - Environment Variables
# Copy this file to .env and fill in your actual values.
# NEVER commit .env to version control.

# ──────────────────────────────────────────────
# Application
# ──────────────────────────────────────────────
APP_NAME=Healthcare Marketing Platform
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=false
APP_SECRET_KEY=change-me-to-a-secure-random-string
APP_LOG_LEVEL=INFO

# ──────────────────────────────────────────────
# LangChain / LLM
# ──────────────────────────────────────────────
OPENAI_API_KEY=sk-your-openai-api-key
LANGCHAIN_MODEL_NAME=gpt-4
LANGCHAIN_TEMPERATURE=0.7
LANGCHAIN_MAX_TOKENS=4096
LANGCHAIN_TRACING_V2=false
LANGCHAIN_PROJECT=healthcare-marketing

# ──────────────────────────────────────────────
# Database
# ──────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/healthcare_marketing
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# ──────────────────────────────────────────────
# Redis
# ──────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0

# ──────────────────────────────────────────────
# Salesforce
# ──────────────────────────────────────────────
SALESFORCE_ENABLED=false
SALESFORCE_CLIENT_ID=your-salesforce-client-id
SALESFORCE_CLIENT_SECRET=your-salesforce-client-secret
SALESFORCE_USERNAME=your-salesforce-username
SALESFORCE_PASSWORD=your-salesforce-password
SALESFORCE_SECURITY_TOKEN=your-salesforce-security-token
SALESFORCE_SANDBOX=false
SALESFORCE_API_VERSION=v58.0

# ──────────────────────────────────────────────
# HubSpot
# ──────────────────────────────────────────────
HUBSPOT_ENABLED=false
HUBSPOT_API_KEY=your-hubspot-api-key
HUBSPOT_PORTAL_ID=your-hubspot-portal-id

# ──────────────────────────────────────────────
# Mailchimp
# ──────────────────────────────────────────────
MAILCHIMP_ENABLED=false
MAILCHIMP_API_KEY=your-mailchimp-api-key
MAILCHIMP_SERVER_PREFIX=us1
MAILCHIMP_LIST_ID=your-audience-list-id

# ──────────────────────────────────────────────
# HIPAA / Security
# ──────────────────────────────────────────────
ENCRYPTION_KEY=your-32-byte-encryption-key-here
ENCRYPTION_ALGORITHM=AES-256-GCM
HIPAA_AUDIT_LOG_ENABLED=true
HIPAA_PHI_DETECTION_ENABLED=true
HIPAA_AUTO_REDACT=true
HIPAA_SESSION_TIMEOUT_MINUTES=30
HIPAA_MFA_REQUIRED=true
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# ──────────────────────────────────────────────
# Monitoring
# ──────────────────────────────────────────────
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
JAEGER_ENDPOINT=http://jaeger:14268/api/traces
SENTRY_DSN=

# ──────────────────────────────────────────────
# CORS
# ──────────────────────────────────────────────
CORS_ORIGINS=http://localhost:3000,https://healthcare-marketing.example.com

```

---

## Agent Configuration

```yaml
agents:
  analytics:
    enabled: true
    metrics_retention_days: 365
    real_time_tracking: true
  campaigns:
    channels:
    - email
    - social_media
    - paid_ads
    - content_marketing
    default_duration_days: 30
    enabled: true
    max_concurrent_campaigns: 10
  compliance:
    enabled: true
    fda_guidelines: true
    hipaa_validation: true
    require_legal_review: true
    strict_mode: true
  content:
    enabled: true
    max_content_length: 10000
    supported_formats:
    - blog_post
    - social_media
    - email
    - landing_page
    - video_script
  reporting:
    default_format: pdf
    enabled: true
    schedule: weekly
```

---

## Integration Settings

```yaml
integrations:
  hubspot:
    api_version: v3
    enabled: false
    sync_interval_minutes: 15
  mailchimp:
    api_version: '3.0'
    enabled: false
    sync_interval_minutes: 30
  salesforce:
    api_version: v58.0
    enabled: false
    sandbox: false
    sync_interval_minutes: 15
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
  tracing:
    enabled: false
    jaeger_endpoint: http://jaeger:14268/api/traces
```

---

## Rate Limiting & Caching

### redis

```yaml
redis:
  db: 0
  max_connections: 50
  socket_timeout: 5
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/healthcare-marketing
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

*Generated for `healthcare-marketing` — GRC_Claw Configuration Guide*
