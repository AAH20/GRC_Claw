# Account Based Marketing — Configuration Guide

> Account-based marketing platform for account identification, intent scoring, buying committee mapping, and personalized campaigns.

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

The **account-based-marketing** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/account-based-marketing/
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
| `app.name` | `ABM Platform` |
| `app.version` | `0.1.0` |
| `app.environment` | `development` |
| `app.log_level` | `DEBUG` |
| `server.host` | `0.0.0.0` |
| `server.port` | `8000` |
| `server.workers` | `4` |
| `agents.account_identification.max_accounts` | `100` |
| `agents.account_identification.min_score_threshold` | `0.6` |
| `agents.account_identification.data_sources` | `salesforce, hubspot, linkedin` |
| `agents.intent_scoring.model` | `gpt-4` |
| `agents.intent_scoring.scoring_window_days` | `30` |
| `agents.intent_scoring.intent_signals` | `website_visits, content_downloads, email_engagement, ad_clicks, social_engagement` |
| `agents.buying_committee_mapper.max_contacts_per_account` | `20` |
| `agents.buying_committee_mapper.roles_to_identify` | `champion, decision_maker, influencer, blocker, user` |
| `agents.content_personalization.model` | `gpt-4` |
| `agents.content_personalization.content_types` | `email, landing_page, ad_copy, social_post, direct_mail` |
| `agents.channel_orchestrator.channels` | `email, linkedin_ads, google_ads, direct_mail, web_personalization` |
| `agents.channel_orchestrator.max_touchpoints_per_week` | `5` |
| `agents.performance_analytics.attribution_model` | `multi_touch` |
| `agents.performance_analytics.metrics` | `impressions, clicks, engagement_rate, pipeline_generated, revenue_influenced, roi` |
| `integrations.salesforce.api_version` | `v58.0` |
| `integrations.salesforce.timeout_seconds` | `30` |
| `integrations.salesforce.retry_attempts` | `3` |
| `integrations.hubspot.api_version` | `v3` |
| `integrations.hubspot.timeout_seconds` | `30` |
| `integrations.hubspot.retry_attempts` | `3` |
| `integrations.linkedin_ads.api_version` | `v2` |
| `integrations.linkedin_ads.timeout_seconds` | `30` |
| `integrations.linkedin_ads.retry_attempts` | `3` |
| `rate_limiting.requests_per_minute` | `100` |
| `rate_limiting.burst_size` | `20` |

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
| `SALESFORCE_CLIENT_ID` | `your-salesforce-client-id` | Salesforce |
| `SALESFORCE_CLIENT_SECRET` | `your-salesforce-client-secret` | Salesforce |
| `SALESFORCE_USERNAME` | `your-salesforce-username` | Salesforce |
| `SALESFORCE_PASSWORD` | `your-salesforce-password` | Salesforce |
| `SALESFORCE_SECURITY_TOKEN` | `your-salesforce-security-token` | Salesforce |
| `SALESFORCE_DOMAIN` | `login` | Salesforce |
| `HUBSPOT_API_KEY` | `your-hubspot-api-key` | HubSpot |
| `HUBSPOT_PORTAL_ID` | `your-hubspot-portal-id` | HubSpot |
| `LINKEDIN_CLIENT_ID` | `your-linkedin-client-id` | LinkedIn Ads |
| `LINKEDIN_CLIENT_SECRET` | `your-linkedin-client-secret` | LinkedIn Ads |
| `LINKEDIN_ACCESS_TOKEN` | `your-linkedin-access-token` | LinkedIn Ads |
| `LINKEDIN_AD_ACCOUNT_ID` | `your-linkedin-ad-account-id` | LinkedIn Ads |
| `OPENAI_API_KEY` | `your-openai-api-key` | LLM |
| `OPENAI_MODEL` | `gpt-4` | LLM |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis (for caching) |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: ABM Platform
  version: 0.1.0
  environment: development
  log_level: DEBUG
server:
  host: 0.0.0.0
  port: 8000
  workers: 4
agents:
  account_identification:
    max_accounts: 100
    min_score_threshold: 0.6
    data_sources:
      - salesforce
      - hubspot
      - linkedin
  intent_scoring:
    model: gpt-4
    scoring_window_days: 30
    intent_signals:
      - website_visits
      - content_downloads
      - email_engagement
      - ad_clicks
      - social_engagement
  buying_committee_mapper:
    max_contacts_per_account: 20
    roles_to_identify:
      - champion
      - decision_maker
      - influencer
      - blocker
      - user
  content_personalization:
    model: gpt-4
    content_types:
      - email
      - landing_page
      - ad_copy
      - social_post
      - direct_mail
  channel_orchestrator:
    channels:
      - email
      - linkedin_ads
      - google_ads
      - direct_mail
      - web_personalization
    max_touchpoints_per_week: 5
  performance_analytics:
    attribution_model: multi_touch
    metrics:
      - impressions
      - clicks
      - engagement_rate
      - pipeline_generated
      - revenue_influenced
      - roi
integrations:
  salesforce:
    api_version: v58.0
    timeout_seconds: 30
    retry_attempts: 3
  hubspot:
    api_version: v3
    timeout_seconds: 30
    retry_attempts: 3
  linkedin_ads:
    api_version: v2
    timeout_seconds: 30
    retry_attempts: 3
rate_limiting:
  requests_per_minute: 100
  burst_size: 20
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
SALESFORCE_CLIENT_ID=your-salesforce-client-id
SALESFORCE_CLIENT_SECRET=your-salesforce-client-secret
SALESFORCE_USERNAME=your-salesforce-username
SALESFORCE_PASSWORD=your-salesforce-password
SALESFORCE_SECURITY_TOKEN=your-salesforce-security-token
SALESFORCE_DOMAIN=login

# HubSpot
HUBSPOT_API_KEY=your-hubspot-api-key
HUBSPOT_PORTAL_ID=your-hubspot-portal-id

# LinkedIn Ads
LINKEDIN_CLIENT_ID=your-linkedin-client-id
LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret
LINKEDIN_ACCESS_TOKEN=your-linkedin-access-token
LINKEDIN_AD_ACCOUNT_ID=your-linkedin-ad-account-id

# LLM
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4

# Redis (for caching)
REDIS_URL=redis://localhost:6379/0

```

---

## Agent Configuration

```yaml
agents:
  account_identification:
    data_sources:
    - salesforce
    - hubspot
    - linkedin
    max_accounts: 100
    min_score_threshold: 0.6
  buying_committee_mapper:
    max_contacts_per_account: 20
    roles_to_identify:
    - champion
    - decision_maker
    - influencer
    - blocker
    - user
  channel_orchestrator:
    channels:
    - email
    - linkedin_ads
    - google_ads
    - direct_mail
    - web_personalization
    max_touchpoints_per_week: 5
  content_personalization:
    content_types:
    - email
    - landing_page
    - ad_copy
    - social_post
    - direct_mail
    model: gpt-4
  intent_scoring:
    intent_signals:
    - website_visits
    - content_downloads
    - email_engagement
    - ad_clicks
    - social_engagement
    model: gpt-4
    scoring_window_days: 30
  performance_analytics:
    attribution_model: multi_touch
    metrics:
    - impressions
    - clicks
    - engagement_rate
    - pipeline_generated
    - revenue_influenced
    - roi
```

---

## Integration Settings

```yaml
integrations:
  hubspot:
    api_version: v3
    retry_attempts: 3
    timeout_seconds: 30
  linkedin_ads:
    api_version: v2
    retry_attempts: 3
    timeout_seconds: 30
  salesforce:
    api_version: v58.0
    retry_attempts: 3
    timeout_seconds: 30
```

---

## Security Configuration

No explicit security configuration found. See environment variables for API keys and secrets.

---

## Monitoring & Observability

No explicit monitoring configuration found.

---

## Rate Limiting & Caching

### rate_limiting

```yaml
rate_limiting:
  burst_size: 20
  requests_per_minute: 100
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/account-based-marketing
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

*Generated for `account-based-marketing` — GRC_Claw Configuration Guide*
