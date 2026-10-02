# Broker Enablement — Configuration Guide

> Broker enablement platform for partner onboarding, commission tracking, performance analytics, and multi-tenant orchestration.

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

The **broker-enablement** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/broker-enablement/
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
| `app.name` | `broker-enablement` |
| `app.version` | `0.1.0` |
| `app.environment` | `development` |
| `app.log_level` | `INFO` |
| `app.debug` | `False` |
| `server.host` | `0.0.0.0` |
| `server.port` | `8000` |
| `server.workers` | `4` |
| `server.reload` | `False` |
| `database.url` | `postgresql://user:password@localhost:5432/broker_enablement` |
| `database.pool_size` | `10` |
| `database.max_overflow` | `20` |
| `database.pool_timeout` | `30` |
| `redis.url` | `redis://localhost:6379/0` |
| `redis.max_connections` | `50` |
| `agents.partner_onboarding.max_retries` | `3` |
| `agents.partner_onboarding.timeout_seconds` | `300` |
| `agents.partner_onboarding.model` | `gpt-4` |
| `agents.partner_enablement.max_retries` | `3` |
| `agents.partner_enablement.timeout_seconds` | `300` |
| `agents.partner_enablement.model` | `gpt-4` |
| `agents.commission_tracking.max_retries` | `3` |
| `agents.commission_tracking.timeout_seconds` | `120` |
| `agents.commission_tracking.model` | `gpt-4` |
| `agents.performance_analytics.max_retries` | `3` |
| `agents.performance_analytics.timeout_seconds` | `180` |
| `agents.performance_analytics.model` | `gpt-4` |
| `agents.multi_tenant_orchestration.max_retries` | `3` |
| `agents.multi_tenant_orchestration.timeout_seconds` | `60` |
| `agents.multi_tenant_orchestration.model` | `gpt-4` |
| `integrations.salesforce.api_version` | `v58.0` |
| `integrations.salesforce.timeout_seconds` | `30` |
| `integrations.salesforce.sandbox` | `False` |
| `integrations.hubspot.api_version` | `v3` |
| `integrations.hubspot.timeout_seconds` | `30` |
| `integrations.stripe.api_version` | `2024-06-20` |
| `integrations.stripe.timeout_seconds` | `30` |
| `security.secret_key` | `change-me-in-production` |
| `security.algorithm` | `HS256` |
| `security.access_token_expire_minutes` | `30` |
| `security.allowed_hosts` | `*` |
| `security.cors_origins` | `http://localhost:3000, https://app.broker-enablement.example.com` |
| `rate_limiting.enabled` | `True` |
| `rate_limiting.requests_per_minute` | `100` |
| `rate_limiting.burst_size` | `20` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `ENVIRONMENT` | `development` | Application |
| `DEBUG` | `true` | Application |
| `LOG_LEVEL` | `INFO` | Application |
| `SECRET_KEY` | `your-secret-key-here` | Application |
| `HOST` | `0.0.0.0` | Server |
| `PORT` | `8000` | Server |
| `WORKERS` | `4` | Server |
| `DATABASE_URL` | `postgresql://user:password@localhost:5432/broker_enablement` | Database |
| `DATABASE_POOL_SIZE` | `10` | Database |
| `DATABASE_MAX_OVERFLOW` | `20` | Database |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis |
| `OPENAI_API_KEY` | `sk-your-openai-api-key` | LangChain / AI |
| `LANGCHAIN_API_KEY` | `lsv2-your-langchain-api-key` | LangChain / AI |
| `LANGCHAIN_TRACING_V2` | `true` | LangChain / AI |
| `LANGCHAIN_PROJECT` | `broker-enablement` | LangChain / AI |
| `SALESFORCE_CLIENT_ID` | `your-salesforce-client-id` | Salesforce |
| `SALESFORCE_CLIENT_SECRET` | `your-salesforce-client-secret` | Salesforce |
| `SALESFORCE_USERNAME` | `your-salesforce-username` | Salesforce |
| `SALESFORCE_PASSWORD` | `your-salesforce-password` | Salesforce |
| `SALESFORCE_SECURITY_TOKEN` | `your-salesforce-security-token` | Salesforce |
| `SALESFORCE_SANDBOX` | `false` | Salesforce |
| `HUBSPOT_API_KEY` | `your-hubspot-api-key` | HubSpot |
| `HUBSPOT_PORTAL_ID` | `your-hubspot-portal-id` | HubSpot |
| `STRIPE_SECRET_KEY` | `sk_test_your-stripe-secret-key` | Stripe |
| `STRIPE_WEBHOOK_SECRET` | `whsec_your-webhook-secret` | Stripe |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Security |
| `ALLOWED_HOSTS` | `*` | Security |
| `CORS_ORIGINS` | `http://localhost:3000,https://app.broker-enablement.example.com` | Security |
| `RATE_LIMIT_ENABLED` | `true` | Rate Limiting |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | `100` | Rate Limiting |
| `RATE_LIMIT_BURST_SIZE` | `20` | Rate Limiting |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: broker-enablement
  version: 0.1.0
  environment: development
  log_level: INFO
  debug: False
server:
  host: 0.0.0.0
  port: 8000
  workers: 4
  reload: False
database:
  url: postgresql://user:password@localhost:5432/broker_enablement
  pool_size: 10
  max_overflow: 20
  pool_timeout: 30
redis:
  url: redis://localhost:6379/0
  max_connections: 50
agents:
  partner_onboarding:
    max_retries: 3
    timeout_seconds: 300
    model: gpt-4
  partner_enablement:
    max_retries: 3
    timeout_seconds: 300
    model: gpt-4
  commission_tracking:
    max_retries: 3
    timeout_seconds: 120
    model: gpt-4
  performance_analytics:
    max_retries: 3
    timeout_seconds: 180
    model: gpt-4
  multi_tenant_orchestration:
    max_retries: 3
    timeout_seconds: 60
    model: gpt-4
integrations:
  salesforce:
    api_version: v58.0
    timeout_seconds: 30
    sandbox: False
  hubspot:
    api_version: v3
    timeout_seconds: 30
  stripe:
    api_version: 2024-06-20
    timeout_seconds: 30
security:
  secret_key: change-me-in-production
  algorithm: HS256
  access_token_expire_minutes: 30
  allowed_hosts:
    - *
  cors_origins:
    - http://localhost:3000
    - https://app.broker-enablement.example.com
rate_limiting:
  enabled: True
  requests_per_minute: 100
  burst_size: 20
```

---

## Example .env File

```bash
# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key-here

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/broker_enablement
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://localhost:6379/0

# LangChain / AI
OPENAI_API_KEY=sk-your-openai-api-key
LANGCHAIN_API_KEY=lsv2-your-langchain-api-key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=broker-enablement

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

# Stripe
STRIPE_SECRET_KEY=sk_test_your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret

# Security
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALLOWED_HOSTS=*
CORS_ORIGINS=http://localhost:3000,https://app.broker-enablement.example.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_BURST_SIZE=20

```

---

## Agent Configuration

```yaml
agents:
  commission_tracking:
    max_retries: 3
    model: gpt-4
    timeout_seconds: 120
  multi_tenant_orchestration:
    max_retries: 3
    model: gpt-4
    timeout_seconds: 60
  partner_enablement:
    max_retries: 3
    model: gpt-4
    timeout_seconds: 300
  partner_onboarding:
    max_retries: 3
    model: gpt-4
    timeout_seconds: 300
  performance_analytics:
    max_retries: 3
    model: gpt-4
    timeout_seconds: 180
```

---

## Integration Settings

```yaml
integrations:
  hubspot:
    api_version: v3
    timeout_seconds: 30
  salesforce:
    api_version: v58.0
    sandbox: false
    timeout_seconds: 30
  stripe:
    api_version: '2024-06-20'
    timeout_seconds: 30
```

---

## Security Configuration

### security

```yaml
security:
  access_token_expire_minutes: 30
  algorithm: HS256
  allowed_hosts:
  - '*'
  cors_origins:
  - http://localhost:3000
  - https://app.broker-enablement.example.com
  secret_key: change-me-in-production
```

---

## Monitoring & Observability

No explicit monitoring configuration found.

---

## Rate Limiting & Caching

### redis

```yaml
redis:
  max_connections: 50
  url: redis://localhost:6379/0
```

### rate_limiting

```yaml
rate_limiting:
  burst_size: 20
  enabled: true
  requests_per_minute: 100
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/broker-enablement
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

*Generated for `broker-enablement` — GRC_Claw Configuration Guide*
