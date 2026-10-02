# Journey Orchestrator — Configuration Guide

> Multi-agent customer journey orchestration platform that designs, personalizes, and optimizes cross-channel customer journeys.

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

The **journey-orchestrator** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/journey-orchestrator/
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
| `app.name` | `journey-orchestrator` |
| `app.version` | `0.1.0` |
| `app.environment` | `development` |
| `app.log_level` | `INFO` |
| `app.host` | `0.0.0.0` |
| `app.port` | `8000` |
| `agents.journey_designer.model` | `gpt-4` |
| `agents.journey_designer.temperature` | `0.7` |
| `agents.journey_designer.max_tokens` | `4096` |
| `agents.personalization.model` | `gpt-4` |
| `agents.personalization.temperature` | `0.5` |
| `agents.personalization.max_tokens` | `2048` |
| `agents.timing_optimizer.model` | `gpt-4` |
| `agents.timing_optimizer.temperature` | `0.3` |
| `agents.timing_optimizer.max_tokens` | `1024` |
| `agents.experimentation.model` | `gpt-4` |
| `agents.experimentation.temperature` | `0.5` |
| `agents.experimentation.max_tokens` | `2048` |
| `agents.critic.model` | `gpt-4` |
| `agents.critic.temperature` | `0.2` |
| `agents.critic.max_tokens` | `2048` |
| `agents.cross_channel.model` | `gpt-4` |
| `agents.cross_channel.temperature` | `0.5` |
| `agents.cross_channel.max_tokens` | `2048` |
| `integrations.salesforce.api_version` | `v58.0` |
| `integrations.salesforce.timeout` | `30` |
| `integrations.salesforce.max_retries` | `3` |
| `integrations.segment.api_version` | `v1` |
| `integrations.segment.timeout` | `10` |
| `integrations.segment.max_retries` | `3` |
| `integrations.amplitude.api_version` | `v2` |
| `integrations.amplitude.timeout` | `10` |
| `integrations.amplitude.max_retries` | `3` |
| `orchestration.max_concurrent_journeys` | `100` |
| `orchestration.event_batch_size` | `50` |
| `orchestration.event_flush_interval_seconds` | `30` |
| `orchestration.journey_timeout_seconds` | `3600` |
| `features.enable_experimentation` | `True` |
| `features.enable_critic_review` | `True` |
| `features.enable_cross_channel` | `True` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `JOURNEY_ENVIRONMENT` | `development` | Application |
| `JOURNEY_DEBUG` | `false` | Application |
| `JOURNEY_LOG_LEVEL` | `INFO` | Application |
| `JOURNEY_SECRET_KEY` | `change-me-in-production` | Application |
| `JOURNEY_API_HOST` | `0.0.0.0` | API |
| `JOURNEY_API_PORT` | `8000` | API |
| `JOURNEY_API_WORKERS` | `4` | API |
| `JOURNEY_DATABASE_URL` | `postgresql+asyncpg://journey:journey@localhost:5432/journey_orchestrator` | Database |
| `JOURNEY_DATABASE_POOL_SIZE` | `20` | Database |
| `JOURNEY_DATABASE_MAX_OVERFLOW` | `10` | Database |
| `JOURNEY_REDIS_URL` | `redis://localhost:6379/0` | Redis |
| `JOURNEY_REDIS_MAX_CONNECTIONS` | `50` | Redis |
| `OPENAI_API_KEY` | `sk-your-openai-api-key` | LLM Providers |
| `ANTHROPIC_API_KEY` | `sk-ant-your-anthropic-api-key` | LLM Providers |
| `SENDGRID_API_KEY` | `SG.your-sendgrid-key` | Channel Providers |
| `TWILIO_ACCOUNT_SID` | `your-twilio-account-sid` | Channel Providers |
| `TWILIO_AUTH_TOKEN` | `your-twilio-auth-token` | Channel Providers |
| `TWILIO_PHONE_NUMBER` | `+1234567890` | Channel Providers |
| `FIREBASE_CREDENTIALS_PATH` | `/path/to/firebase-credentials.json` | Channel Providers |
| `META_ACCESS_TOKEN` | `your-meta-access-token` | Channel Providers |
| `JOURNEY_METRICS_ENABLED` | `true` | Observability |
| `JOURNEY_METRICS_PORT` | `9090` | Observability |
| `JOURNEY_TRACING_ENABLED` | `false` | Observability |
| `JOURNEY_TRACING_ENDPOINT` | `http://localhost:4318` | Observability |
| `JOURNEY_JWT_ALGORITHM` | `HS256` | Security |
| `JOURNEY_JWT_EXPIRATION` | `3600` | Security |
| `JOURNEY_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Security |
| `GRC_CLAW_ENABLED` | `true` | GRC Claw Governance |
| `GRC_CLAW_POLICY_PATH` | `/etc/grc-claw/policies` | GRC Claw Governance |
| `GRC_CLAW_AUDIT_LOG_PATH` | `/var/log/grc-claw/audit.log` | GRC Claw Governance |
| `GRC_MARKETING_CORE_PATH` | `/path/to/grc-marketing-core` | grc-marketing-core |
| `GRC_MARKETING_CORE_ENABLED` | `true` | grc-marketing-core |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: journey-orchestrator
  version: 0.1.0
  environment: development
  log_level: INFO
  host: 0.0.0.0
  port: 8000
agents:
  journey_designer:
    model: gpt-4
    temperature: 0.7
    max_tokens: 4096
  personalization:
    model: gpt-4
    temperature: 0.5
    max_tokens: 2048
  timing_optimizer:
    model: gpt-4
    temperature: 0.3
    max_tokens: 1024
  experimentation:
    model: gpt-4
    temperature: 0.5
    max_tokens: 2048
  critic:
    model: gpt-4
    temperature: 0.2
    max_tokens: 2048
  cross_channel:
    model: gpt-4
    temperature: 0.5
    max_tokens: 2048
integrations:
  salesforce:
    api_version: v58.0
    timeout: 30
    max_retries: 3
  segment:
    api_version: v1
    timeout: 10
    max_retries: 3
  amplitude:
    api_version: v2
    timeout: 10
    max_retries: 3
orchestration:
  max_concurrent_journeys: 100
  event_batch_size: 50
  event_flush_interval_seconds: 30
  journey_timeout_seconds: 3600
features:
  enable_experimentation: True
  enable_critic_review: True
  enable_cross_channel: True
```

---

## Example .env File

```bash
# Journey Orchestrator Environment Configuration
# Copy this file to .env and fill in your values

# Application
JOURNEY_ENVIRONMENT=development
JOURNEY_DEBUG=false
JOURNEY_LOG_LEVEL=INFO
JOURNEY_SECRET_KEY=change-me-in-production

# API
JOURNEY_API_HOST=0.0.0.0
JOURNEY_API_PORT=8000
JOURNEY_API_WORKERS=4

# Database
JOURNEY_DATABASE_URL=postgresql+asyncpg://journey:journey@localhost:5432/journey_orchestrator
JOURNEY_DATABASE_POOL_SIZE=20
JOURNEY_DATABASE_MAX_OVERFLOW=10

# Redis
JOURNEY_REDIS_URL=redis://localhost:6379/0
JOURNEY_REDIS_MAX_CONNECTIONS=50

# LLM Providers
OPENAI_API_KEY=sk-your-openai-api-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key

# Channel Providers
SENDGRID_API_KEY=SG.your-sendgrid-key
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=+1234567890
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
META_ACCESS_TOKEN=your-meta-access-token

# Observability
JOURNEY_METRICS_ENABLED=true
JOURNEY_METRICS_PORT=9090
JOURNEY_TRACING_ENABLED=false
JOURNEY_TRACING_ENDPOINT=http://localhost:4318

# Security
JOURNEY_JWT_ALGORITHM=HS256
JOURNEY_JWT_EXPIRATION=3600
JOURNEY_ALLOWED_HOSTS=localhost,127.0.0.1

# GRC Claw Governance
GRC_CLAW_ENABLED=true
GRC_CLAW_POLICY_PATH=/etc/grc-claw/policies
GRC_CLAW_AUDIT_LOG_PATH=/var/log/grc-claw/audit.log

# grc-marketing-core
GRC_MARKETING_CORE_PATH=/path/to/grc-marketing-core
GRC_MARKETING_CORE_ENABLED=true

```

---

## Agent Configuration

```yaml
agents:
  critic:
    max_tokens: 2048
    model: gpt-4
    temperature: 0.2
  cross_channel:
    max_tokens: 2048
    model: gpt-4
    temperature: 0.5
  experimentation:
    max_tokens: 2048
    model: gpt-4
    temperature: 0.5
  journey_designer:
    max_tokens: 4096
    model: gpt-4
    temperature: 0.7
  personalization:
    max_tokens: 2048
    model: gpt-4
    temperature: 0.5
  timing_optimizer:
    max_tokens: 1024
    model: gpt-4
    temperature: 0.3
```

---

## Integration Settings

```yaml
integrations:
  amplitude:
    api_version: v2
    max_retries: 3
    timeout: 10
  salesforce:
    api_version: v58.0
    max_retries: 3
    timeout: 30
  segment:
    api_version: v1
    max_retries: 3
    timeout: 10
```

---

## Security Configuration

No explicit security configuration found. See environment variables for API keys and secrets.

---

## Monitoring & Observability

No explicit monitoring configuration found.

---

## Rate Limiting & Caching

No explicit rate limiting or caching configuration found.

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/journey-orchestrator
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

*Generated for `journey-orchestrator` — GRC_Claw Configuration Guide*
