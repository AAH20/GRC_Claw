# Social Media Manager — Configuration Guide

> Comprehensive social media management platform for content creation, scheduling, engagement, and analytics across major platforms.

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

The **social-media-manager** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/social-media-manager/
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
| `app.name` | `social-media-manager` |
| `app.version` | `0.1.0` |
| `app.env` | `development` |
| `app.log_level` | `INFO` |
| `app.host` | `0.0.0.0` |
| `app.port` | `8000` |
| `agents.content_creation.enabled` | `True` |
| `agents.content_creation.model` | `gpt-4` |
| `agents.content_creation.temperature` | `0.7` |
| `agents.content_creation.max_tokens` | `1000` |
| `agents.scheduling.enabled` | `True` |
| `agents.scheduling.model` | `gpt-4` |
| `agents.scheduling.temperature` | `0.3` |
| `agents.scheduling.max_tokens` | `500` |
| `agents.engagement.enabled` | `True` |
| `agents.engagement.model` | `gpt-4` |
| `agents.engagement.temperature` | `0.5` |
| `agents.engagement.max_tokens` | `800` |
| `agents.social_listening.enabled` | `True` |
| `agents.social_listening.model` | `gpt-4` |
| `agents.social_listening.temperature` | `0.2` |
| `agents.social_listening.max_tokens` | `600` |
| `agents.influencer_identification.enabled` | `True` |
| `agents.influencer_identification.model` | `gpt-4` |
| `agents.influencer_identification.temperature` | `0.4` |
| `agents.influencer_identification.max_tokens` | `700` |
| `agents.performance_analytics.enabled` | `True` |
| `agents.performance_analytics.model` | `gpt-4` |
| `agents.performance_analytics.temperature` | `0.1` |
| `agents.performance_analytics.max_tokens` | `1200` |
| `platforms.twitter.enabled` | `True` |
| `platforms.twitter.api_version` | `2` |
| `platforms.twitter.rate_limit` | `300` |
| `platforms.instagram.enabled` | `True` |
| `platforms.instagram.api_version` | `v18.0` |
| `platforms.instagram.rate_limit` | `200` |
| `platforms.facebook.enabled` | `True` |
| `platforms.facebook.api_version` | `v18.0` |
| `platforms.facebook.rate_limit` | `200` |
| `platforms.linkedin.enabled` | `True` |
| `platforms.linkedin.api_version` | `v2` |
| `platforms.linkedin.rate_limit` | `100` |
| `platforms.tiktok.enabled` | `True` |
| `platforms.tiktok.api_version` | `v1` |
| `platforms.tiktok.rate_limit` | `100` |
| `integrations.twitter.base_url` | `https://api.twitter.com/2` |
| `integrations.twitter.auth_type` | `oauth2` |
| `integrations.instagram.base_url` | `https://graph.instagram.com` |
| `integrations.instagram.auth_type` | `oauth2` |
| `integrations.facebook.base_url` | `https://graph.facebook.com` |
| `integrations.facebook.auth_type` | `oauth2` |
| `integrations.linkedin.base_url` | `https://api.linkedin.com/v2` |
| `integrations.linkedin.auth_type` | `oauth2` |
| `integrations.tiktok.base_url` | `https://open-api.tiktok.com` |
| `integrations.tiktok.auth_type` | `oauth2` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `APP_ENV` | `development` | Application |
| `LOG_LEVEL` | `DEBUG` | Application |
| `SECRET_KEY` | `change-me-in-production` | Application |
| `HOST` | `0.0.0.0` | Server |
| `PORT` | `8000` | Server |
| `OPENAI_API_KEY` | `sk-your-openai-api-key` | LangChain / LLM |
| `LANGCHAIN_API_KEY` | `lsv2-your-langsmith-key` | LangChain / LLM |
| `LANGCHAIN_TRACING_V2` | `true` | LangChain / LLM |
| `LANGCHAIN_PROJECT` | `social-media-manager` | LangChain / LLM |
| `TWITTER_API_KEY` | `your-twitter-api-key` | Twitter/X |
| `TWITTER_API_SECRET` | `your-twitter-api-secret` | Twitter/X |
| `TWITTER_ACCESS_TOKEN` | `your-twitter-access-token` | Twitter/X |
| `TWITTER_ACCESS_TOKEN_SECRET` | `your-twitter-access-token-secret` | Twitter/X |
| `TWITTER_BEARER_TOKEN` | `your-twitter-bearer-token` | Twitter/X |
| `INSTAGRAM_ACCESS_TOKEN` | `your-instagram-access-token` | Instagram |
| `INSTAGRAM_APP_ID` | `your-instagram-app-id` | Instagram |
| `INSTAGRAM_APP_SECRET` | `your-instagram-app-secret` | Instagram |
| `FACEBOOK_ACCESS_TOKEN` | `your-facebook-access-token` | Facebook |
| `FACEBOOK_APP_ID` | `your-facebook-app-id` | Facebook |
| `FACEBOOK_APP_SECRET` | `your-facebook-app-secret` | Facebook |
| `FACEBOOK_PAGE_ID` | `your-facebook-page-id` | Facebook |
| `LINKEDIN_ACCESS_TOKEN` | `your-linkedin-access-token` | LinkedIn |
| `LINKEDIN_CLIENT_ID` | `your-linkedin-client-id` | LinkedIn |
| `LINKEDIN_CLIENT_SECRET` | `your-linkedin-client-secret` | LinkedIn |
| `TIKTOK_ACCESS_TOKEN` | `your-tiktok-access-token` | TikTok |
| `TIKTOK_APP_ID` | `your-tiktok-app-id` | TikTok |
| `TIKTOK_APP_SECRET` | `your-tiktok-app-secret` | TikTok |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis (for caching / task queue) |
| `DATABASE_URL` | `postgresql://user:password@localhost:5432/smm` | Database (optional, for persistent storage) |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: social-media-manager
  version: 0.1.0
  env: development
  log_level: INFO
  host: 0.0.0.0
  port: 8000
agents:
  content_creation:
    enabled: True
    model: gpt-4
    temperature: 0.7
    max_tokens: 1000
  scheduling:
    enabled: True
    model: gpt-4
    temperature: 0.3
    max_tokens: 500
  engagement:
    enabled: True
    model: gpt-4
    temperature: 0.5
    max_tokens: 800
  social_listening:
    enabled: True
    model: gpt-4
    temperature: 0.2
    max_tokens: 600
  influencer_identification:
    enabled: True
    model: gpt-4
    temperature: 0.4
    max_tokens: 700
  performance_analytics:
    enabled: True
    model: gpt-4
    temperature: 0.1
    max_tokens: 1200
platforms:
  twitter:
    enabled: True
    api_version: 2
    rate_limit: 300
  instagram:
    enabled: True
    api_version: v18.0
    rate_limit: 200
  facebook:
    enabled: True
    api_version: v18.0
    rate_limit: 200
  linkedin:
    enabled: True
    api_version: v2
    rate_limit: 100
  tiktok:
    enabled: True
    api_version: v1
    rate_limit: 100
integrations:
  twitter:
    base_url: https://api.twitter.com/2
    auth_type: oauth2
  instagram:
    base_url: https://graph.instagram.com
    auth_type: oauth2
  facebook:
    base_url: https://graph.facebook.com
    auth_type: oauth2
  linkedin:
    base_url: https://api.linkedin.com/v2
    auth_type: oauth2
  tiktok:
    base_url: https://open-api.tiktok.com
    auth_type: oauth2
```

---

## Example .env File

```bash
# Application
APP_ENV=development
LOG_LEVEL=DEBUG
SECRET_KEY=change-me-in-production

# Server
HOST=0.0.0.0
PORT=8000

# LangChain / LLM
OPENAI_API_KEY=sk-your-openai-api-key
LANGCHAIN_API_KEY=lsv2-your-langsmith-key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=social-media-manager

# Twitter/X
TWITTER_API_KEY=your-twitter-api-key
TWITTER_API_SECRET=your-twitter-api-secret
TWITTER_ACCESS_TOKEN=your-twitter-access-token
TWITTER_ACCESS_TOKEN_SECRET=your-twitter-access-token-secret
TWITTER_BEARER_TOKEN=your-twitter-bearer-token

# Instagram
INSTAGRAM_ACCESS_TOKEN=your-instagram-access-token
INSTAGRAM_APP_ID=your-instagram-app-id
INSTAGRAM_APP_SECRET=your-instagram-app-secret

# Facebook
FACEBOOK_ACCESS_TOKEN=your-facebook-access-token
FACEBOOK_APP_ID=your-facebook-app-id
FACEBOOK_APP_SECRET=your-facebook-app-secret
FACEBOOK_PAGE_ID=your-facebook-page-id

# LinkedIn
LINKEDIN_ACCESS_TOKEN=your-linkedin-access-token
LINKEDIN_CLIENT_ID=your-linkedin-client-id
LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret

# TikTok
TIKTOK_ACCESS_TOKEN=your-tiktok-access-token
TIKTOK_APP_ID=your-tiktok-app-id
TIKTOK_APP_SECRET=your-tiktok-app-secret

# Redis (for caching / task queue)
REDIS_URL=redis://localhost:6379/0

# Database (optional, for persistent storage)
DATABASE_URL=postgresql://user:password@localhost:5432/smm

```

---

## Agent Configuration

```yaml
agents:
  content_creation:
    enabled: true
    max_tokens: 1000
    model: gpt-4
    temperature: 0.7
  engagement:
    enabled: true
    max_tokens: 800
    model: gpt-4
    temperature: 0.5
  influencer_identification:
    enabled: true
    max_tokens: 700
    model: gpt-4
    temperature: 0.4
  performance_analytics:
    enabled: true
    max_tokens: 1200
    model: gpt-4
    temperature: 0.1
  scheduling:
    enabled: true
    max_tokens: 500
    model: gpt-4
    temperature: 0.3
  social_listening:
    enabled: true
    max_tokens: 600
    model: gpt-4
    temperature: 0.2
```

---

## Integration Settings

```yaml
integrations:
  facebook:
    auth_type: oauth2
    base_url: https://graph.facebook.com
  instagram:
    auth_type: oauth2
    base_url: https://graph.instagram.com
  linkedin:
    auth_type: oauth2
    base_url: https://api.linkedin.com/v2
  tiktok:
    auth_type: oauth2
    base_url: https://open-api.tiktok.com
  twitter:
    auth_type: oauth2
    base_url: https://api.twitter.com/2
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
cd ~/GRC_Claw/projects/social-media-manager
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

*Generated for `social-media-manager` — GRC_Claw Configuration Guide*
