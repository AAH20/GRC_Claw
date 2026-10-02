# Ecommerce Marketing — Configuration Guide

> E-commerce marketing platform for product recommendations, cart abandonment, email, social, and analytics.

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

The **ecommerce-marketing** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/ecommerce-marketing/
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
| `app.name` | `ecommerce-marketing` |
| `app.version` | `0.1.0` |
| `app.environment` | `development` |
| `app.log_level` | `INFO` |
| `app.host` | `0.0.0.0` |
| `app.port` | `8000` |
| `agents.product_recommendations.model` | `gpt-4o` |
| `agents.product_recommendations.max_recommendations` | `10` |
| `agents.product_recommendations.cache_ttl` | `300` |
| `agents.product_recommendations.min_confidence` | `0.7` |
| `agents.cart_abandonment.model` | `gpt-4o` |
| `agents.cart_abandonment.recovery_window_hours` | `48` |
| `agents.cart_abandonment.max_reminders` | `3` |
| `agents.cart_abandonment.reminder_intervals` | `1, 24, 48` |
| `agents.email.model` | `gpt-4o` |
| `agents.email.max_subject_length` | `100` |
| `agents.email.ab_test_enabled` | `True` |
| `agents.email.ab_test_split` | `0.5` |
| `agents.social.model` | `gpt-4o` |
| `agents.social.platforms` | `twitter, facebook, instagram, linkedin` |
| `agents.social.max_post_length` | `280` |
| `agents.social.schedule_lookahead_days` | `7` |
| `agents.analytics.model` | `gpt-4o` |
| `agents.analytics.metrics_retention_days` | `90` |
| `agents.analytics.realtime_enabled` | `True` |
| `integrations.shopify.api_version` | `2024-01` |
| `integrations.shopify.rate_limit` | `2` |
| `integrations.shopify.timeout` | `30` |
| `integrations.shopify.retry_attempts` | `3` |
| `integrations.woocommerce.api_version` | `v3` |
| `integrations.woocommerce.rate_limit` | `10` |
| `integrations.woocommerce.timeout` | `30` |
| `integrations.woocommerce.retry_attempts` | `3` |
| `integrations.stripe.api_version` | `2024-06-20` |
| `integrations.stripe.rate_limit` | `100` |
| `integrations.stripe.timeout` | `30` |
| `integrations.stripe.retry_attempts` | `3` |
| `cache.backend` | `redis` |
| `cache.ttl` | `300` |
| `cache.max_size` | `10000` |
| `monitoring.prometheus_enabled` | `True` |
| `monitoring.metrics_port` | `9090` |
| `monitoring.health_check_interval` | `30` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `ENVIRONMENT` | `development` | Application |
| `LOG_LEVEL` | `DEBUG` | Application |
| `SECRET_KEY` | `change-me-in-production` | Application |
| `OPENAI_API_KEY` | `sk-your-openai-api-key` | OpenAI |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI |
| `SHOPIFY_API_KEY` | `your-shopify-api-key` | Shopify |
| `SHOPIFY_API_SECRET` | `your-shopify-api-secret` | Shopify |
| `SHOPIFY_STORE_URL` | `your-store.myshopify.com` | Shopify |
| `SHOPIFY_ACCESS_TOKEN` | `your-shopify-access-token` | Shopify |
| `WOOCOMMERCE_API_KEY` | `your-woocommerce-api-key` | WooCommerce |
| `WOOCOMMERCE_API_SECRET` | `your-woocommerce-api-secret` | WooCommerce |
| `WOOCOMMERCE_STORE_URL` | `https://your-store.com` | WooCommerce |
| `STRIPE_SECRET_KEY` | `sk_test_your-stripe-secret-key` | Stripe |
| `STRIPE_WEBHOOK_SECRET` | `whsec_your-webhook-secret` | Stripe |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis |
| `PROMETHEUS_ENABLED` | `true` | Monitoring |
| `SENTRY_DSN` | `` | Monitoring |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: ecommerce-marketing
  version: 0.1.0
  environment: development
  log_level: INFO
  host: 0.0.0.0
  port: 8000
agents:
  product_recommendations:
    model: gpt-4o
    max_recommendations: 10
    cache_ttl: 300
    min_confidence: 0.7
  cart_abandonment:
    model: gpt-4o
    recovery_window_hours: 48
    max_reminders: 3
    reminder_intervals:
      - 1
      - 24
      - 48
  email:
    model: gpt-4o
    max_subject_length: 100
    ab_test_enabled: True
    ab_test_split: 0.5
  social:
    model: gpt-4o
    platforms:
      - twitter
      - facebook
      - instagram
      - linkedin
    max_post_length: 280
    schedule_lookahead_days: 7
  analytics:
    model: gpt-4o
    metrics_retention_days: 90
    realtime_enabled: True
integrations:
  shopify:
    api_version: 2024-01
    rate_limit: 2
    timeout: 30
    retry_attempts: 3
  woocommerce:
    api_version: v3
    rate_limit: 10
    timeout: 30
    retry_attempts: 3
  stripe:
    api_version: 2024-06-20
    rate_limit: 100
    timeout: 30
    retry_attempts: 3
cache:
  backend: redis
  ttl: 300
  max_size: 10000
monitoring:
  prometheus_enabled: True
  metrics_port: 9090
  health_check_interval: 30
```

---

## Example .env File

```bash
# Application
ENVIRONMENT=development
LOG_LEVEL=DEBUG
SECRET_KEY=change-me-in-production

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o

# Shopify
SHOPIFY_API_KEY=your-shopify-api-key
SHOPIFY_API_SECRET=your-shopify-api-secret
SHOPIFY_STORE_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=your-shopify-access-token

# WooCommerce
WOOCOMMERCE_API_KEY=your-woocommerce-api-key
WOOCOMMERCE_API_SECRET=your-woocommerce-api-secret
WOOCOMMERCE_STORE_URL=https://your-store.com

# Stripe
STRIPE_SECRET_KEY=sk_test_your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret

# Redis
REDIS_URL=redis://localhost:6379/0

# Monitoring
PROMETHEUS_ENABLED=true
SENTRY_DSN=

```

---

## Agent Configuration

```yaml
agents:
  analytics:
    metrics_retention_days: 90
    model: gpt-4o
    realtime_enabled: true
  cart_abandonment:
    max_reminders: 3
    model: gpt-4o
    recovery_window_hours: 48
    reminder_intervals:
    - 1
    - 24
    - 48
  email:
    ab_test_enabled: true
    ab_test_split: 0.5
    max_subject_length: 100
    model: gpt-4o
  product_recommendations:
    cache_ttl: 300
    max_recommendations: 10
    min_confidence: 0.7
    model: gpt-4o
  social:
    max_post_length: 280
    model: gpt-4o
    platforms:
    - twitter
    - facebook
    - instagram
    - linkedin
    schedule_lookahead_days: 7
```

---

## Integration Settings

```yaml
integrations:
  shopify:
    api_version: 2024-01
    rate_limit: 2
    retry_attempts: 3
    timeout: 30
  stripe:
    api_version: '2024-06-20'
    rate_limit: 100
    retry_attempts: 3
    timeout: 30
  woocommerce:
    api_version: v3
    rate_limit: 10
    retry_attempts: 3
    timeout: 30
```

---

## Security Configuration

No explicit security configuration found. See environment variables for API keys and secrets.

---

## Monitoring & Observability

### monitoring

```yaml
monitoring:
  health_check_interval: 30
  metrics_port: 9090
  prometheus_enabled: true
```

---

## Rate Limiting & Caching

### cache

```yaml
cache:
  backend: redis
  max_size: 10000
  ttl: 300
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/ecommerce-marketing
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

*Generated for `ecommerce-marketing` — GRC_Claw Configuration Guide*
