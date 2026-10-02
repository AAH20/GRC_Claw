# Pricing Optimizer — Configuration Guide

> Dynamic pricing optimization platform with market intelligence, elasticity modeling, and automated price testing.

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

The **pricing-optimizer** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/pricing-optimizer/
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
| `app.name` | `pricing-optimizer` |
| `app.version` | `0.1.0` |
| `app.environment` | `development` |
| `app.log_level` | `INFO` |
| `server.host` | `0.0.0.0` |
| `server.port` | `8000` |
| `server.workers` | `4` |
| `agents.market_intelligence.update_interval_minutes` | `60` |
| `agents.market_intelligence.max_competitors` | `10` |
| `agents.market_intelligence.data_sources` | `shopify, woocommerce, stripe` |
| `agents.pricing_engine.min_margin_percent` | `10.0` |
| `agents.pricing_engine.max_price_change_percent` | `25.0` |
| `agents.pricing_engine.elasticity_model` | `log_linear` |
| `agents.pricing_engine.optimization_strategy` | `profit_maximization` |
| `agents.testing.min_sample_size` | `100` |
| `agents.testing.confidence_level` | `0.95` |
| `agents.testing.max_test_duration_days` | `14` |
| `agents.implementation.batch_size` | `50` |
| `agents.implementation.rollback_on_failure` | `True` |
| `agents.implementation.dry_run` | `False` |
| `agents.monitoring.metrics_interval_minutes` | `5` |
| `agents.monitoring.anomaly_threshold_std` | `2.0` |
| `agents.monitoring.alert_channels` | `webhook` |
| `integrations.shopify.api_version` | `2024-01` |
| `integrations.shopify.rate_limit_per_second` | `2` |
| `integrations.shopify.timeout_seconds` | `30` |
| `integrations.woocommerce.api_version` | `v3` |
| `integrations.woocommerce.rate_limit_per_second` | `2` |
| `integrations.woocommerce.timeout_seconds` | `30` |
| `integrations.stripe.api_version` | `2023-10-16` |
| `integrations.stripe.rate_limit_per_second` | `10` |
| `integrations.stripe.timeout_seconds` | `30` |
| `cache.backend` | `redis` |
| `cache.ttl_seconds` | `300` |
| `cache.redis_url` | `redis://localhost:6379/0` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `ENVIRONMENT` | `development` | Application |
| `LOG_LEVEL` | `DEBUG` | Application |
| `SECRET_KEY` | `change-me-in-production` | Application |
| `OPENAI_API_KEY` | `sk-your-key-here` | OpenAI (for LangChain/DeepAgents) |
| `OPENAI_MODEL` | `gpt-4` | OpenAI (for LangChain/DeepAgents) |
| `SHOPIFY_SHOP_URL` | `https://your-store.myshopify.com` | Shopify |
| `SHOPIFY_ACCESS_TOKEN` | `shpat-your-token` | Shopify |
| `SHOPIFY_API_VERSION` | `2024-01` | Shopify |
| `WOOCOMMERCE_URL` | `https://your-store.com` | WooCommerce |
| `WOOCOMMERCE_API_KEY` | `ck-your-key` | WooCommerce |
| `WOOCOMMERCE_API_SECRET` | `cs-your-secret` | WooCommerce |
| `STRIPE_SECRET_KEY` | `sk_test_your-key` | Stripe |
| `STRIPE_WEBHOOK_SECRET` | `whsec_your-secret` | Stripe |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis |
| `PROMETHEUS_PORT` | `9090` | Monitoring |
| `SENTRY_DSN` | `` | Monitoring |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: pricing-optimizer
  version: 0.1.0
  environment: development
  log_level: INFO
server:
  host: 0.0.0.0
  port: 8000
  workers: 4
agents:
  market_intelligence:
    update_interval_minutes: 60
    max_competitors: 10
    data_sources:
      - shopify
      - woocommerce
      - stripe
  pricing_engine:
    min_margin_percent: 10.0
    max_price_change_percent: 25.0
    elasticity_model: log_linear
    optimization_strategy: profit_maximization
  testing:
    min_sample_size: 100
    confidence_level: 0.95
    max_test_duration_days: 14
  implementation:
    batch_size: 50
    rollback_on_failure: True
    dry_run: False
  monitoring:
    metrics_interval_minutes: 5
    anomaly_threshold_std: 2.0
    alert_channels:
      - webhook
integrations:
  shopify:
    api_version: 2024-01
    rate_limit_per_second: 2
    timeout_seconds: 30
  woocommerce:
    api_version: v3
    rate_limit_per_second: 2
    timeout_seconds: 30
  stripe:
    api_version: 2023-10-16
    rate_limit_per_second: 10
    timeout_seconds: 30
cache:
  backend: redis
  ttl_seconds: 300
  redis_url: redis://localhost:6379/0
```

---

## Example .env File

```bash
# Application
ENVIRONMENT=development
LOG_LEVEL=DEBUG
SECRET_KEY=change-me-in-production

# OpenAI (for LangChain/DeepAgents)
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4

# Shopify
SHOPIFY_SHOP_URL=https://your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat-your-token
SHOPIFY_API_VERSION=2024-01

# WooCommerce
WOOCOMMERCE_URL=https://your-store.com
WOOCOMMERCE_API_KEY=ck-your-key
WOOCOMMERCE_API_SECRET=cs-your-secret

# Stripe
STRIPE_SECRET_KEY=sk_test_your-key
STRIPE_WEBHOOK_SECRET=whsec_your-secret

# Redis
REDIS_URL=redis://localhost:6379/0

# Monitoring
PROMETHEUS_PORT=9090
SENTRY_DSN=

```

---

## Agent Configuration

```yaml
agents:
  implementation:
    batch_size: 50
    dry_run: false
    rollback_on_failure: true
  market_intelligence:
    data_sources:
    - shopify
    - woocommerce
    - stripe
    max_competitors: 10
    update_interval_minutes: 60
  monitoring:
    alert_channels:
    - webhook
    anomaly_threshold_std: 2.0
    metrics_interval_minutes: 5
  pricing_engine:
    elasticity_model: log_linear
    max_price_change_percent: 25.0
    min_margin_percent: 10.0
    optimization_strategy: profit_maximization
  testing:
    confidence_level: 0.95
    max_test_duration_days: 14
    min_sample_size: 100
```

---

## Integration Settings

```yaml
integrations:
  shopify:
    api_version: 2024-01
    rate_limit_per_second: 2
    timeout_seconds: 30
  stripe:
    api_version: '2023-10-16'
    rate_limit_per_second: 10
    timeout_seconds: 30
  woocommerce:
    api_version: v3
    rate_limit_per_second: 2
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

### cache

```yaml
cache:
  backend: redis
  redis_url: redis://localhost:6379/0
  ttl_seconds: 300
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/pricing-optimizer
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

*Generated for `pricing-optimizer` — GRC_Claw Configuration Guide*
