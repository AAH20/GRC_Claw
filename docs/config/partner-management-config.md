# Partner Management — Configuration Guide

> Partner management platform for onboarding, deal management, communication, analytics, and compliance.

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

The **partner-management** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/partner-management/
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
| `app.name` | `partner-management` |
| `app.version` | `0.1.0` |
| `app.environment` | `development` |
| `app.log_level` | `INFO` |
| `app.host` | `0.0.0.0` |
| `app.port` | `8000` |
| `agents.onboarding.enabled` | `True` |
| `agents.onboarding.max_retries` | `3` |
| `agents.onboarding.timeout_seconds` | `300` |
| `agents.deal_management.enabled` | `True` |
| `agents.deal_management.max_retries` | `3` |
| `agents.deal_management.timeout_seconds` | `300` |
| `agents.communication.enabled` | `True` |
| `agents.communication.max_retries` | `3` |
| `agents.communication.timeout_seconds` | `120` |
| `agents.analytics.enabled` | `True` |
| `agents.analytics.max_retries` | `3` |
| `agents.analytics.timeout_seconds` | `180` |
| `agents.enablement.enabled` | `True` |
| `agents.enablement.max_retries` | `3` |
| `agents.enablement.timeout_seconds` | `300` |
| `agents.compliance.enabled` | `True` |
| `agents.compliance.max_retries` | `3` |
| `agents.compliance.timeout_seconds` | `120` |
| `integrations.salesforce.enabled` | `False` |
| `integrations.salesforce.api_version` | `v58.0` |
| `integrations.salesforce.timeout_seconds` | `30` |
| `integrations.salesforce.sandbox` | `False` |
| `integrations.hubspot.enabled` | `False` |
| `integrations.hubspot.timeout_seconds` | `30` |
| `integrations.impartner.enabled` | `False` |
| `integrations.impartner.timeout_seconds` | `30` |
| `database.url` | `sqlite:///./partner_management.db` |
| `database.echo` | `False` |
| `database.pool_size` | `5` |
| `database.max_overflow` | `10` |
| `cache.backend` | `memory` |
| `cache.ttl_seconds` | `300` |
| `security.secret_key` | `change-me-in-production` |
| `security.algorithm` | `HS256` |
| `security.access_token_expire_minutes` | `30` |
| `observability.metrics_enabled` | `True` |
| `observability.tracing_enabled` | `False` |
| `observability.health_check_interval_seconds` | `30` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `ENVIRONMENT` | `development` | Application |
| `LOG_LEVEL` | `DEBUG` | Application |
| `SECRET_KEY` | `your-secret-key-here` | Application |
| `HOST` | `0.0.0.0` | Server |
| `PORT` | `8000` | Server |
| `DATABASE_URL` | `sqlite:///./partner_management.db` | Database |
| `SALESFORCE_ENABLED` | `false` | Salesforce |
| `SALESFORCE_CLIENT_ID` | `` | Salesforce |
| `SALESFORCE_CLIENT_SECRET` | `` | Salesforce |
| `SALESFORCE_USERNAME` | `` | Salesforce |
| `SALESFORCE_PASSWORD` | `` | Salesforce |
| `SALESFORCE_SECURITY_TOKEN` | `` | Salesforce |
| `SALESFORCE_SANDBOX` | `false` | Salesforce |
| `HUBSPOT_ENABLED` | `false` | HubSpot |
| `HUBSPOT_API_KEY` | `` | HubSpot |
| `HUBSPOT_PORTAL_ID` | `` | HubSpot |
| `IMPARTNER_ENABLED` | `false` | Impartner |
| `IMPARTNER_API_KEY` | `` | Impartner |
| `IMPARTNER_BASE_URL` | `` | Impartner |
| `LANGCHAIN_API_KEY` | `` | LangChain / DeepAgents |
| `LANGCHAIN_TRACING_V2` | `false` | LangChain / DeepAgents |
| `LANGCHAIN_PROJECT` | `partner-management` | LangChain / DeepAgents |
| `METRICS_ENABLED` | `true` | Observability |
| `TRACING_ENABLED` | `false` | Observability |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: partner-management
  version: 0.1.0
  environment: development
  log_level: INFO
  host: 0.0.0.0
  port: 8000
agents:
  onboarding:
    enabled: True
    max_retries: 3
    timeout_seconds: 300
  deal_management:
    enabled: True
    max_retries: 3
    timeout_seconds: 300
  communication:
    enabled: True
    max_retries: 3
    timeout_seconds: 120
  analytics:
    enabled: True
    max_retries: 3
    timeout_seconds: 180
  enablement:
    enabled: True
    max_retries: 3
    timeout_seconds: 300
  compliance:
    enabled: True
    max_retries: 3
    timeout_seconds: 120
integrations:
  salesforce:
    enabled: False
    api_version: v58.0
    timeout_seconds: 30
    sandbox: False
  hubspot:
    enabled: False
    timeout_seconds: 30
  impartner:
    enabled: False
    timeout_seconds: 30
database:
  url: sqlite:///./partner_management.db
  echo: False
  pool_size: 5
  max_overflow: 10
cache:
  backend: memory
  ttl_seconds: 300
security:
  secret_key: change-me-in-production
  algorithm: HS256
  access_token_expire_minutes: 30
observability:
  metrics_enabled: True
  tracing_enabled: False
  health_check_interval_seconds: 30
```

---

## Example .env File

```bash
# Application
ENVIRONMENT=development
LOG_LEVEL=DEBUG
SECRET_KEY=your-secret-key-here

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite:///./partner_management.db

# Salesforce
SALESFORCE_ENABLED=false
SALESFORCE_CLIENT_ID=
SALESFORCE_CLIENT_SECRET=
SALESFORCE_USERNAME=
SALESFORCE_PASSWORD=
SALESFORCE_SECURITY_TOKEN=
SALESFORCE_SANDBOX=false

# HubSpot
HUBSPOT_ENABLED=false
HUBSPOT_API_KEY=
HUBSPOT_PORTAL_ID=

# Impartner
IMPARTNER_ENABLED=false
IMPARTNER_API_KEY=
IMPARTNER_BASE_URL=

# LangChain / DeepAgents
LANGCHAIN_API_KEY=
LANGCHAIN_TRACING_V2=false
LANGCHAIN_PROJECT=partner-management

# Observability
METRICS_ENABLED=true
TRACING_ENABLED=false

```

---

## Agent Configuration

```yaml
agents:
  analytics:
    enabled: true
    max_retries: 3
    timeout_seconds: 180
  communication:
    enabled: true
    max_retries: 3
    timeout_seconds: 120
  compliance:
    enabled: true
    max_retries: 3
    timeout_seconds: 120
  deal_management:
    enabled: true
    max_retries: 3
    timeout_seconds: 300
  enablement:
    enabled: true
    max_retries: 3
    timeout_seconds: 300
  onboarding:
    enabled: true
    max_retries: 3
    timeout_seconds: 300
```

---

## Integration Settings

```yaml
integrations:
  hubspot:
    enabled: false
    timeout_seconds: 30
  impartner:
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

### security

```yaml
security:
  access_token_expire_minutes: 30
  algorithm: HS256
  secret_key: change-me-in-production
```

---

## Monitoring & Observability

### observability

```yaml
observability:
  health_check_interval_seconds: 30
  metrics_enabled: true
  tracing_enabled: false
```

---

## Rate Limiting & Caching

### cache

```yaml
cache:
  backend: memory
  ttl_seconds: 300
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/partner-management
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

*Generated for `partner-management` — GRC_Claw Configuration Guide*
