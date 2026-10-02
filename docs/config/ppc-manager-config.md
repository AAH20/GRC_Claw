# Ppc Manager — Configuration Guide

> Pay-per-click management platform for Google Ads, Meta Ads, LinkedIn Ads, and TikTok Ads with automated bidding and optimization.

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

The **ppc-manager** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/ppc-manager/
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
| `app.name` | `ppc-manager` |
| `app.version` | `0.1.0` |
| `app.log_level` | `info` |
| `app.environment` | `development` |
| `server.host` | `0.0.0.0` |
| `server.port` | `8000` |
| `server.workers` | `1` |
| `agents.keyword_research.model` | `gpt-4o` |
| `agents.keyword_research.max_tokens` | `2048` |
| `agents.keyword_research.temperature` | `0.3` |
| `agents.keyword_research.max_keywords` | `100` |
| `agents.bid_management.model` | `gpt-4o` |
| `agents.bid_management.max_tokens` | `1024` |
| `agents.bid_management.temperature` | `0.2` |
| `agents.bid_management.min_bid` | `0.01` |
| `agents.bid_management.max_bid` | `100.0` |
| `agents.ad_creative.model` | `gpt-4o` |
| `agents.ad_creative.max_tokens` | `2048` |
| `agents.ad_creative.temperature` | `0.7` |
| `agents.ad_creative.max_variants` | `5` |
| `agents.landing_page_optimization.model` | `gpt-4o` |
| `agents.landing_page_optimization.max_tokens` | `2048` |
| `agents.landing_page_optimization.temperature` | `0.3` |
| `agents.budget_allocation.model` | `gpt-4o` |
| `agents.budget_allocation.max_tokens` | `1024` |
| `agents.budget_allocation.temperature` | `0.2` |
| `agents.budget_allocation.min_budget` | `1.0` |
| `agents.performance_analytics.model` | `gpt-4o` |
| `agents.performance_analytics.max_tokens` | `4096` |
| `agents.performance_analytics.temperature` | `0.1` |
| `integrations.google_ads.developer_token` | `${GOOGLE_ADS_DEVELOPER_TOKEN}` |
| `integrations.google_ads.client_id` | `${GOOGLE_ADS_CLIENT_ID}` |
| `integrations.google_ads.client_secret` | `${GOOGLE_ADS_CLIENT_SECRET}` |
| `integrations.google_ads.refresh_token` | `${GOOGLE_ADS_REFRESH_TOKEN}` |
| `integrations.google_ads.login_customer_id` | `${GOOGLE_ADS_LOGIN_CUSTOMER_ID}` |
| `integrations.meta_ads.access_token` | `${META_ACCESS_TOKEN}` |
| `integrations.meta_ads.app_id` | `${META_APP_ID}` |
| `integrations.meta_ads.app_secret` | `${META_APP_SECRET}` |
| `integrations.meta_ads.ad_account_id` | `${META_AD_ACCOUNT_ID}` |
| `integrations.linkedin_ads.access_token` | `${LINKEDIN_ACCESS_TOKEN}` |
| `integrations.linkedin_ads.ad_account_id` | `${LINKEDIN_AD_ACCOUNT_ID}` |
| `integrations.tiktok_ads.access_token` | `${TIKTOK_ACCESS_TOKEN}` |
| `integrations.tiktok_ads.advertiser_id` | `${TIKTOK_ADVERTISER_ID}` |
| `retry.max_attempts` | `3` |
| `retry.backoff_factor` | `2.0` |
| `retry.max_wait` | `60` |
| `rate_limit.requests_per_minute` | `60` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `APP_NAME` | `ppc-manager` | Application |
| `APP_ENV` | `development` | Application |
| `LOG_LEVEL` | `info` | Application |
| `HOST` | `0.0.0.0` | Server |
| `PORT` | `8000` | Server |
| `OPENAI_API_KEY` | `sk-your-openai-api-key` | LLM |
| `OPENAI_MODEL` | `gpt-4o` | LLM |
| `GOOGLE_ADS_DEVELOPER_TOKEN` | `your-developer-token` | Google Ads API |
| `GOOGLE_ADS_CLIENT_ID` | `your-client-id` | Google Ads API |
| `GOOGLE_ADS_CLIENT_SECRET` | `your-client-secret` | Google Ads API |
| `GOOGLE_ADS_REFRESH_TOKEN` | `your-refresh-token` | Google Ads API |
| `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | `your-login-customer-id` | Google Ads API |
| `META_ACCESS_TOKEN` | `your-meta-access-token` | Meta Ads API |
| `META_APP_ID` | `your-app-id` | Meta Ads API |
| `META_APP_SECRET` | `your-app-secret` | Meta Ads API |
| `META_AD_ACCOUNT_ID` | `act_your-ad-account-id` | Meta Ads API |
| `LINKEDIN_ACCESS_TOKEN` | `your-linkedin-access-token` | LinkedIn Ads API |
| `LINKEDIN_AD_ACCOUNT_ID` | `your-ad-account-id` | LinkedIn Ads API |
| `TIKTOK_ACCESS_TOKEN` | `your-tiktok-access-token` | TikTok Ads API |
| `TIKTOK_ADVERTISER_ID` | `your-advertiser-id` | TikTok Ads API |
| `PROMETHEUS_PORT` | `9090` | Observability |
| `ENABLE_METRICS` | `true` | Observability |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: ppc-manager
  version: 0.1.0
  log_level: info
  environment: development
server:
  host: 0.0.0.0
  port: 8000
  workers: 1
agents:
  keyword_research:
    model: gpt-4o
    max_tokens: 2048
    temperature: 0.3
    max_keywords: 100
  bid_management:
    model: gpt-4o
    max_tokens: 1024
    temperature: 0.2
    min_bid: 0.01
    max_bid: 100.0
  ad_creative:
    model: gpt-4o
    max_tokens: 2048
    temperature: 0.7
    max_variants: 5
  landing_page_optimization:
    model: gpt-4o
    max_tokens: 2048
    temperature: 0.3
  budget_allocation:
    model: gpt-4o
    max_tokens: 1024
    temperature: 0.2
    min_budget: 1.0
  performance_analytics:
    model: gpt-4o
    max_tokens: 4096
    temperature: 0.1
integrations:
  google_ads:
    developer_token: ${GOOGLE_ADS_DEVELOPER_TOKEN}
    client_id: ${GOOGLE_ADS_CLIENT_ID}
    client_secret: ${GOOGLE_ADS_CLIENT_SECRET}
    refresh_token: ${GOOGLE_ADS_REFRESH_TOKEN}
    login_customer_id: ${GOOGLE_ADS_LOGIN_CUSTOMER_ID}
  meta_ads:
    access_token: ${META_ACCESS_TOKEN}
    app_id: ${META_APP_ID}
    app_secret: ${META_APP_SECRET}
    ad_account_id: ${META_AD_ACCOUNT_ID}
  linkedin_ads:
    access_token: ${LINKEDIN_ACCESS_TOKEN}
    ad_account_id: ${LINKEDIN_AD_ACCOUNT_ID}
  tiktok_ads:
    access_token: ${TIKTOK_ACCESS_TOKEN}
    advertiser_id: ${TIKTOK_ADVERTISER_ID}
retry:
  max_attempts: 3
  backoff_factor: 2.0
  max_wait: 60
rate_limit:
  requests_per_minute: 60
```

---

## Example .env File

```bash
# Application
APP_NAME=ppc-manager
APP_ENV=development
LOG_LEVEL=info

# Server
HOST=0.0.0.0
PORT=8000

# LLM
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o

# Google Ads API
GOOGLE_ADS_DEVELOPER_TOKEN=your-developer-token
GOOGLE_ADS_CLIENT_ID=your-client-id
GOOGLE_ADS_CLIENT_SECRET=your-client-secret
GOOGLE_ADS_REFRESH_TOKEN=your-refresh-token
GOOGLE_ADS_LOGIN_CUSTOMER_ID=your-login-customer-id

# Meta Ads API
META_ACCESS_TOKEN=your-meta-access-token
META_APP_ID=your-app-id
META_APP_SECRET=your-app-secret
META_AD_ACCOUNT_ID=act_your-ad-account-id

# LinkedIn Ads API
LINKEDIN_ACCESS_TOKEN=your-linkedin-access-token
LINKEDIN_AD_ACCOUNT_ID=your-ad-account-id

# TikTok Ads API
TIKTOK_ACCESS_TOKEN=your-tiktok-access-token
TIKTOK_ADVERTISER_ID=your-advertiser-id

# Observability
PROMETHEUS_PORT=9090
ENABLE_METRICS=true

```

---

## Agent Configuration

```yaml
agents:
  ad_creative:
    max_tokens: 2048
    max_variants: 5
    model: gpt-4o
    temperature: 0.7
  bid_management:
    max_bid: 100.0
    max_tokens: 1024
    min_bid: 0.01
    model: gpt-4o
    temperature: 0.2
  budget_allocation:
    max_tokens: 1024
    min_budget: 1.0
    model: gpt-4o
    temperature: 0.2
  keyword_research:
    max_keywords: 100
    max_tokens: 2048
    model: gpt-4o
    temperature: 0.3
  landing_page_optimization:
    max_tokens: 2048
    model: gpt-4o
    temperature: 0.3
  performance_analytics:
    max_tokens: 4096
    model: gpt-4o
    temperature: 0.1
```

---

## Integration Settings

```yaml
integrations:
  google_ads:
    client_id: ${GOOGLE_ADS_CLIENT_ID}
    client_secret: ${GOOGLE_ADS_CLIENT_SECRET}
    developer_token: ${GOOGLE_ADS_DEVELOPER_TOKEN}
    login_customer_id: ${GOOGLE_ADS_LOGIN_CUSTOMER_ID}
    refresh_token: ${GOOGLE_ADS_REFRESH_TOKEN}
  linkedin_ads:
    access_token: ${LINKEDIN_ACCESS_TOKEN}
    ad_account_id: ${LINKEDIN_AD_ACCOUNT_ID}
  meta_ads:
    access_token: ${META_ACCESS_TOKEN}
    ad_account_id: ${META_AD_ACCOUNT_ID}
    app_id: ${META_APP_ID}
    app_secret: ${META_APP_SECRET}
  tiktok_ads:
    access_token: ${TIKTOK_ACCESS_TOKEN}
    advertiser_id: ${TIKTOK_ADVERTISER_ID}
```

---

## Security Configuration

No explicit security configuration found. See environment variables for API keys and secrets.

---

## Monitoring & Observability

No explicit monitoring configuration found.

---

## Rate Limiting & Caching

### rate_limit

```yaml
rate_limit:
  requests_per_minute: 60
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/ppc-manager
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

*Generated for `ppc-manager` — GRC_Claw Configuration Guide*
