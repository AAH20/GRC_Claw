# Influencer Marketing — Configuration Guide

> Influencer marketing platform for discovery, vetting, outreach, negotiation, content review, and performance tracking.

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

The **influencer-marketing** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/influencer-marketing/
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
| `app.name` | `Influencer Marketing Platform` |
| `app.version` | `0.1.0` |
| `app.environment` | `development` |
| `app.log_level` | `debug` |
| `app.api_prefix` | `/api/v1` |
| `llm.provider` | `openai` |
| `llm.model` | `gpt-4o` |
| `llm.temperature` | `0.7` |
| `llm.max_tokens` | `4096` |
| `llm.timeout_seconds` | `60` |
| `agents.discovery.max_results` | `50` |
| `agents.discovery.platforms` | `instagram, tiktok, youtube` |
| `agents.discovery.filters.min_followers` | `1000` |
| `agents.discovery.filters.max_followers` | `10000000` |
| `agents.discovery.filters.min_engagement_rate` | `0.01` |
| `agents.discovery.filters.languages` | `en` |
| `agents.discovery.filters.categories` | `fashion, beauty, fitness, food, travel, tech, lifestyle` |
| `agents.vetting.authenticity_threshold` | `0.7` |
| `agents.vetting.brand_safety_check` | `True` |
| `agents.vetting.content_quality_weight` | `0.3` |
| `agents.vetting.audience_quality_weight` | `0.3` |
| `agents.vetting.engagement_quality_weight` | `0.2` |
| `agents.vetting.brand_safety_weight` | `0.2` |
| `agents.outreach.max_concurrent_outreach` | `10` |
| `agents.outreach.follow_up_interval_days` | `7` |
| `agents.outreach.max_follow_ups` | `3` |
| `agents.outreach.templates.initial_contact` | `Hi {name}, we love your content...` |
| `agents.outreach.templates.follow_up` | `Hi {name}, just following up on our previous message...` |
| `agents.negotiation.max_negotiation_rounds` | `5` |
| `agents.negotiation.auto_approve_below` | `500` |
| `agents.negotiation.currency` | `USD` |
| `agents.content.review_workflow_enabled` | `True` |
| `agents.content.auto_approve_trusted` | `False` |
| `agents.content.max_revision_rounds` | `3` |
| `agents.performance.metrics` | `impressions, reach, engagement, clicks, conversions, roi` |
| `agents.performance.reporting_interval_hours` | `24` |
| `agents.optimization.auto_optimize` | `True` |
| `agents.optimization.optimization_interval_hours` | `12` |
| `agents.optimization.min_data_points` | `100` |
| `agents.relationship_management.check_in_interval_days` | `30` |
| `agents.relationship_management.loyalty_program_enabled` | `True` |
| `agents.relationship_management.crm_sync_interval_hours` | `24` |
| `integrations.instagram.api_version` | `v18.0` |
| `integrations.instagram.rate_limit_per_hour` | `200` |
| `integrations.instagram.webhook_verify_token` | `` |
| `integrations.tiktok.api_version` | `v2` |
| `integrations.tiktok.rate_limit_per_hour` | `1000` |
| `integrations.youtube.api_version` | `v3` |
| `integrations.youtube.rate_limit_per_quota` | `10000` |
| `api.rate_limit_per_minute` | `60` |
| `api.cors_origins` | `http://localhost:3000, http://localhost:8080` |
| `api.pagination_default_limit` | `20` |
| `api.pagination_max_limit` | `100` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `ENVIRONMENT` | `development` | Application |
| `LOG_LEVEL` | `debug` | Application |
| `SECRET_KEY` | `change-me-in-production` | Application |
| `OPENAI_API_KEY` | `sk-your-openai-api-key` | LLM Configuration |
| `LLM_MODEL` | `gpt-4o` | LLM Configuration |
| `LLM_TEMPERATURE` | `0.7` | LLM Configuration |
| `LLM_MAX_TOKENS` | `4096` | LLM Configuration |
| `INSTAGRAM_APP_ID` | `your-instagram-app-id` | Instagram Integration |
| `INSTAGRAM_APP_SECRET` | `your-instagram-app-secret` | Instagram Integration |
| `INSTAGRAM_ACCESS_TOKEN` | `your-instagram-access-token` | Instagram Integration |
| `INSTAGRAM_API_VERSION` | `v18.0` | Instagram Integration |
| `TIKTOK_CLIENT_KEY` | `your-tiktok-client-key` | TikTok Integration |
| `TIKTOK_CLIENT_SECRET` | `your-tiktok-client-secret` | TikTok Integration |
| `TIKTOK_ACCESS_TOKEN` | `your-tiktok-access-token` | TikTok Integration |
| `YOUTUBE_API_KEY` | `your-youtube-api-key` | YouTube Integration |
| `YOUTUBE_CLIENT_ID` | `your-youtube-client-id` | YouTube Integration |
| `YOUTUBE_CLIENT_SECRET` | `your-youtube-client-secret` | YouTube Integration |
| `AGENT_MAX_RETRIES` | `3` | Agent Configuration |
| `AGENT_TIMEOUT_SECONDS` | `60` | Agent Configuration |
| `AGENT_CONCURRENCY_LIMIT` | `5` | Agent Configuration |
| `API_RATE_LIMIT_PER_MINUTE` | `60` | API Configuration |
| `API_CORS_ORIGINS` | `http://localhost:3000,http://localhost:8080` | API Configuration |
| `DATABASE_URL` | `postgresql://user:password@localhost:5432/influencer_marketing` | Database (if needed) |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: Influencer Marketing Platform
  version: 0.1.0
  environment: development
  log_level: debug
  api_prefix: /api/v1
llm:
  provider: openai
  model: gpt-4o
  temperature: 0.7
  max_tokens: 4096
  timeout_seconds: 60
agents:
  discovery:
    max_results: 50
    platforms:
      - instagram
      - tiktok
      - youtube
    filters:
      min_followers: 1000
      max_followers: 10000000
      min_engagement_rate: 0.01
      languages:
        - en
      categories:
        - fashion
        - beauty
        - fitness
        - food
        - travel
        - tech
        - lifestyle
  vetting:
    authenticity_threshold: 0.7
    brand_safety_check: True
    content_quality_weight: 0.3
    audience_quality_weight: 0.3
    engagement_quality_weight: 0.2
    brand_safety_weight: 0.2
  outreach:
    max_concurrent_outreach: 10
    follow_up_interval_days: 7
    max_follow_ups: 3
    templates:
      initial_contact: Hi {name}, we love your content...
      follow_up: Hi {name}, just following up on our previous message...
  negotiation:
    max_negotiation_rounds: 5
    auto_approve_below: 500
    currency: USD
  content:
    review_workflow_enabled: True
    auto_approve_trusted: False
    max_revision_rounds: 3
  performance:
    metrics:
      - impressions
      - reach
      - engagement
      - clicks
      - conversions
      - roi
    reporting_interval_hours: 24
  optimization:
    auto_optimize: True
    optimization_interval_hours: 12
    min_data_points: 100
  relationship_management:
    check_in_interval_days: 30
    loyalty_program_enabled: True
    crm_sync_interval_hours: 24
integrations:
  instagram:
    api_version: v18.0
    rate_limit_per_hour: 200
    webhook_verify_token: 
  tiktok:
    api_version: v2
    rate_limit_per_hour: 1000
  youtube:
    api_version: v3
    rate_limit_per_quota: 10000
api:
  rate_limit_per_minute: 60
  cors_origins:
    - http://localhost:3000
    - http://localhost:8080
  pagination_default_limit: 20
  pagination_max_limit: 100
```

---

## Example .env File

```bash
# Application
ENVIRONMENT=development
LOG_LEVEL=debug
SECRET_KEY=change-me-in-production

# LLM Configuration
OPENAI_API_KEY=sk-your-openai-api-key
LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096

# Instagram Integration
INSTAGRAM_APP_ID=your-instagram-app-id
INSTAGRAM_APP_SECRET=your-instagram-app-secret
INSTAGRAM_ACCESS_TOKEN=your-instagram-access-token
INSTAGRAM_API_VERSION=v18.0

# TikTok Integration
TIKTOK_CLIENT_KEY=your-tiktok-client-key
TIKTOK_CLIENT_SECRET=your-tiktok-client-secret
TIKTOK_ACCESS_TOKEN=your-tiktok-access-token

# YouTube Integration
YOUTUBE_API_KEY=your-youtube-api-key
YOUTUBE_CLIENT_ID=your-youtube-client-id
YOUTUBE_CLIENT_SECRET=your-youtube-client-secret

# Agent Configuration
AGENT_MAX_RETRIES=3
AGENT_TIMEOUT_SECONDS=60
AGENT_CONCURRENCY_LIMIT=5

# API Configuration
API_RATE_LIMIT_PER_MINUTE=60
API_CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Database (if needed)
DATABASE_URL=postgresql://user:password@localhost:5432/influencer_marketing

# Redis
REDIS_URL=redis://localhost:6379/0

```

---

## Agent Configuration

```yaml
agents:
  content:
    auto_approve_trusted: false
    max_revision_rounds: 3
    review_workflow_enabled: true
  discovery:
    filters:
      categories:
      - fashion
      - beauty
      - fitness
      - food
      - travel
      - tech
      - lifestyle
      languages:
      - en
      max_followers: 10000000
      min_engagement_rate: 0.01
      min_followers: 1000
    max_results: 50
    platforms:
    - instagram
    - tiktok
    - youtube
  negotiation:
    auto_approve_below: 500
    currency: USD
    max_negotiation_rounds: 5
  optimization:
    auto_optimize: true
    min_data_points: 100
    optimization_interval_hours: 12
  outreach:
    follow_up_interval_days: 7
    max_concurrent_outreach: 10
    max_follow_ups: 3
    templates:
      follow_up: Hi {name}, just following up on our previous message...
      initial_contact: Hi {name}, we love your content...
  performance:
    metrics:
    - impressions
    - reach
    - engagement
    - clicks
    - conversions
    - roi
    reporting_interval_hours: 24
  relationship_management:
    check_in_interval_days: 30
    crm_sync_interval_hours: 24
    loyalty_program_enabled: true
  vetting:
    audience_quality_weight: 0.3
    authenticity_threshold: 0.7
    brand_safety_check: true
    brand_safety_weight: 0.2
    content_quality_weight: 0.3
    engagement_quality_weight: 0.2
```

---

## Integration Settings

```yaml
integrations:
  instagram:
    api_version: v18.0
    rate_limit_per_hour: 200
    webhook_verify_token: ''
  tiktok:
    api_version: v2
    rate_limit_per_hour: 1000
  youtube:
    api_version: v3
    rate_limit_per_quota: 10000
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
cd ~/GRC_Claw/projects/influencer-marketing
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

*Generated for `influencer-marketing` — GRC_Claw Configuration Guide*
