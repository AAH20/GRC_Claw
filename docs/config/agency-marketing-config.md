# Agency Marketing — Configuration Guide

> Agency marketing platform for research, strategy, creative, launch, and optimization with CRM integrations.

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

The **agency-marketing** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/agency-marketing/
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
| `app.name` | `Agency Marketing` |
| `app.version` | `0.1.0` |
| `app.description` | `Standalone modularized agentic AI marketing platform` |
| `app.debug` | `False` |
| `app.log_level` | `INFO` |
| `server.host` | `0.0.0.0` |
| `server.port` | `8000` |
| `server.workers` | `4` |
| `server.reload` | `False` |
| `agents.research.enabled` | `True` |
| `agents.research.model` | `gpt-4` |
| `agents.research.max_tokens` | `4096` |
| `agents.research.temperature` | `0.7` |
| `agents.research.timeout_seconds` | `120` |
| `agents.research.retry_attempts` | `3` |
| `agents.strategy.enabled` | `True` |
| `agents.strategy.model` | `gpt-4` |
| `agents.strategy.max_tokens` | `4096` |
| `agents.strategy.temperature` | `0.5` |
| `agents.strategy.timeout_seconds` | `120` |
| `agents.strategy.retry_attempts` | `3` |
| `agents.creative.enabled` | `True` |
| `agents.creative.model` | `gpt-4` |
| `agents.creative.max_tokens` | `4096` |
| `agents.creative.temperature` | `0.8` |
| `agents.creative.timeout_seconds` | `120` |
| `agents.creative.retry_attempts` | `3` |
| `agents.launch.enabled` | `True` |
| `agents.launch.model` | `gpt-4` |
| `agents.launch.max_tokens` | `4096` |
| `agents.launch.temperature` | `0.3` |
| `agents.launch.timeout_seconds` | `120` |
| `agents.launch.retry_attempts` | `3` |
| `agents.optimization.enabled` | `True` |
| `agents.optimization.model` | `gpt-4` |
| `agents.optimization.max_tokens` | `4096` |
| `agents.optimization.temperature` | `0.4` |
| `agents.optimization.timeout_seconds` | `120` |
| `agents.optimization.retry_attempts` | `3` |
| `integrations.salesforce.enabled` | `False` |
| `integrations.salesforce.api_version` | `v58.0` |
| `integrations.salesforce.sandbox` | `False` |
| `integrations.salesforce.timeout_seconds` | `30` |
| `integrations.salesforce.rate_limit_per_second` | `25` |
| `integrations.hubspot.enabled` | `False` |
| `integrations.hubspot.api_version` | `v3` |
| `integrations.hubspot.timeout_seconds` | `30` |
| `integrations.hubspot.rate_limit_per_second` | `100` |
| `integrations.gohighlevel.enabled` | `False` |
| `integrations.gohighlevel.api_version` | `v1` |
| `integrations.gohighlevel.timeout_seconds` | `30` |
| `integrations.gohighlevel.rate_limit_per_second` | `50` |
| `database.url` | `postgresql://agency:agency_secret@localhost:5432/agency_marketing` |
| `database.pool_size` | `10` |
| `database.max_overflow` | `20` |
| `database.pool_timeout` | `30` |
| `redis.url` | `redis://localhost:6379/0` |
| `redis.ttl_seconds` | `3600` |
| `langchain.tracing_v2` | `False` |
| `langchain.project_name` | `agency-marketing` |
| `langchain.callbacks` | `` |
| `security.api_key_header` | `X-API-Key` |
| `security.rate_limit_requests` | `100` |
| `security.rate_limit_window_seconds` | `60` |
| `security.allowed_hosts` | `*` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `APP_NAME` | `Agency Marketing` | Application |
| `APP_VERSION` | `0.1.0` | Application |
| `DEBUG` | `false` | Application |
| `LOG_LEVEL` | `INFO` | Application |
| `HOST` | `0.0.0.0` | Server |
| `PORT` | `8000` | Server |
| `WORKERS` | `4` | Server |
| `OPENAI_API_KEY` | `sk-your-openai-api-key-here` | OpenAI (Required for LLM operations) |
| `LANGCHAIN_API_KEY` | `lsv2-your-langchain-api-key-here` | LangChain / LangSmith (Optional - for tracing) |
| `LANGCHAIN_TRACING_V2` | `false` | LangChain / LangSmith (Optional - for tracing) |
| `LANGCHAIN_PROJECT` | `agency-marketing` | LangChain / LangSmith (Optional - for tracing) |
| `SALESFORCE_ENABLED` | `false` | Salesforce Integration (Optional) |
| `SALESFORCE_CLIENT_ID` | `your-salesforce-client-id` | Salesforce Integration (Optional) |
| `SALESFORCE_CLIENT_SECRET` | `your-salesforce-client-secret` | Salesforce Integration (Optional) |
| `SALESFORCE_USERNAME` | `your-salesforce-username` | Salesforce Integration (Optional) |
| `SALESFORCE_PASSWORD` | `your-salesforce-password` | Salesforce Integration (Optional) |
| `SALESFORCE_SECURITY_TOKEN` | `your-salesforce-security-token` | Salesforce Integration (Optional) |
| `SALESFORCE_SANDBOX` | `false` | Salesforce Integration (Optional) |
| `HUBSPOT_ENABLED` | `false` | HubSpot Integration (Optional) |
| `HUBSPOT_API_KEY` | `your-hubspot-api-key` | HubSpot Integration (Optional) |
| `HUBSPOT_APP_ID` | `your-hubspot-app-id` | HubSpot Integration (Optional) |
| `GOHIGHLEVEL_ENABLED` | `false` | GoHighLevel Integration (Optional) |
| `GOHIGHLEVEL_API_KEY` | `your-gohighlevel-api-key` | GoHighLevel Integration (Optional) |
| `GOHIGHLEVEL_LOCATION_ID` | `your-gohighlevel-location-id` | GoHighLevel Integration (Optional) |
| `DATABASE_URL` | `postgresql://agency:agency_secret@localhost:5432/agency_marketing` | Database (Optional - uses in-memory if not set) |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis (Optional - for caching) |
| `API_KEY` | `your-api-key-for-production` | Security |
| `SECRET_KEY` | `your-secret-key-for-jwt-signing` | Security |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: Agency Marketing
  version: 0.1.0
  description: Standalone modularized agentic AI marketing platform
  debug: False
  log_level: INFO
server:
  host: 0.0.0.0
  port: 8000
  workers: 4
  reload: False
agents:
  research:
    enabled: True
    model: gpt-4
    max_tokens: 4096
    temperature: 0.7
    timeout_seconds: 120
    retry_attempts: 3
  strategy:
    enabled: True
    model: gpt-4
    max_tokens: 4096
    temperature: 0.5
    timeout_seconds: 120
    retry_attempts: 3
  creative:
    enabled: True
    model: gpt-4
    max_tokens: 4096
    temperature: 0.8
    timeout_seconds: 120
    retry_attempts: 3
  launch:
    enabled: True
    model: gpt-4
    max_tokens: 4096
    temperature: 0.3
    timeout_seconds: 120
    retry_attempts: 3
  optimization:
    enabled: True
    model: gpt-4
    max_tokens: 4096
    temperature: 0.4
    timeout_seconds: 120
    retry_attempts: 3
integrations:
  salesforce:
    enabled: False
    api_version: v58.0
    sandbox: False
    timeout_seconds: 30
    rate_limit_per_second: 25
  hubspot:
    enabled: False
    api_version: v3
    timeout_seconds: 30
    rate_limit_per_second: 100
  gohighlevel:
    enabled: False
    api_version: v1
    timeout_seconds: 30
    rate_limit_per_second: 50
database:
  url: postgresql://agency:agency_secret@localhost:5432/agency_marketing
  pool_size: 10
  max_overflow: 20
  pool_timeout: 30
redis:
  url: redis://localhost:6379/0
  ttl_seconds: 3600
langchain:
  tracing_v2: False
  project_name: agency-marketing
  callbacks:
security:
  api_key_header: X-API-Key
  rate_limit_requests: 100
  rate_limit_window_seconds: 60
  allowed_hosts:
    - *
```

---

## Example .env File

```bash
# Agency Marketing Environment Configuration
# Copy this file to .env and fill in your values

# Application
APP_NAME=Agency Marketing
APP_VERSION=0.1.0
DEBUG=false
LOG_LEVEL=INFO

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=4

# OpenAI (Required for LLM operations)
OPENAI_API_KEY=sk-your-openai-api-key-here

# LangChain / LangSmith (Optional - for tracing)
LANGCHAIN_API_KEY=lsv2-your-langchain-api-key-here
LANGCHAIN_TRACING_V2=false
LANGCHAIN_PROJECT=agency-marketing

# Salesforce Integration (Optional)
SALESFORCE_ENABLED=false
SALESFORCE_CLIENT_ID=your-salesforce-client-id
SALESFORCE_CLIENT_SECRET=your-salesforce-client-secret
SALESFORCE_USERNAME=your-salesforce-username
SALESFORCE_PASSWORD=your-salesforce-password
SALESFORCE_SECURITY_TOKEN=your-salesforce-security-token
SALESFORCE_SANDBOX=false

# HubSpot Integration (Optional)
HUBSPOT_ENABLED=false
HUBSPOT_API_KEY=your-hubspot-api-key
HUBSPOT_APP_ID=your-hubspot-app-id

# GoHighLevel Integration (Optional)
GOHIGHLEVEL_ENABLED=false
GOHIGHLEVEL_API_KEY=your-gohighlevel-api-key
GOHIGHLEVEL_LOCATION_ID=your-gohighlevel-location-id

# Database (Optional - uses in-memory if not set)
DATABASE_URL=postgresql://agency:agency_secret@localhost:5432/agency_marketing

# Redis (Optional - for caching)
REDIS_URL=redis://localhost:6379/0

# Security
API_KEY=your-api-key-for-production
SECRET_KEY=your-secret-key-for-jwt-signing

```

---

## Agent Configuration

```yaml
agents:
  creative:
    enabled: true
    max_tokens: 4096
    model: gpt-4
    retry_attempts: 3
    temperature: 0.8
    timeout_seconds: 120
  launch:
    enabled: true
    max_tokens: 4096
    model: gpt-4
    retry_attempts: 3
    temperature: 0.3
    timeout_seconds: 120
  optimization:
    enabled: true
    max_tokens: 4096
    model: gpt-4
    retry_attempts: 3
    temperature: 0.4
    timeout_seconds: 120
  research:
    enabled: true
    max_tokens: 4096
    model: gpt-4
    retry_attempts: 3
    temperature: 0.7
    timeout_seconds: 120
  strategy:
    enabled: true
    max_tokens: 4096
    model: gpt-4
    retry_attempts: 3
    temperature: 0.5
    timeout_seconds: 120
```

---

## Integration Settings

```yaml
integrations:
  gohighlevel:
    api_version: v1
    enabled: false
    rate_limit_per_second: 50
    timeout_seconds: 30
  hubspot:
    api_version: v3
    enabled: false
    rate_limit_per_second: 100
    timeout_seconds: 30
  salesforce:
    api_version: v58.0
    enabled: false
    rate_limit_per_second: 25
    sandbox: false
    timeout_seconds: 30
```

---

## Security Configuration

### security

```yaml
security:
  allowed_hosts:
  - '*'
  api_key_header: X-API-Key
  rate_limit_requests: 100
  rate_limit_window_seconds: 60
```

---

## Monitoring & Observability

No explicit monitoring configuration found.

---

## Rate Limiting & Caching

### redis

```yaml
redis:
  ttl_seconds: 3600
  url: redis://localhost:6379/0
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/agency-marketing
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

*Generated for `agency-marketing` — GRC_Claw Configuration Guide*
