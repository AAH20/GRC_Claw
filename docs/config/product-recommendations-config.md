# Product Recommendations — Configuration Guide

> AI-powered product recommendation engine with cross-sell, bundle optimization, and A/B testing capabilities.

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

The **product-recommendations** is configured through a combination of YAML configuration files and environment variables. Environment variables take precedence over YAML defaults.

### Configuration Sources (in order of precedence):

1. **Environment variables** (highest priority)
2. **`.env` file** in project root
3. **`config/config.yaml`** or **`config.yaml`**
4. **Default values** (lowest priority)

### File Locations:

```
~/GRC_Claw/projects/product-recommendations/
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
| `app.name` | `product-recommendations` |
| `app.version` | `0.1.0` |
| `app.environment` | `development` |
| `app.log_level` | `info` |
| `app.host` | `0.0.0.0` |
| `app.port` | `8000` |
| `agents.data_collection.batch_size` | `100` |
| `agents.data_collection.max_retries` | `3` |
| `agents.data_collection.timeout_seconds` | `30` |
| `agents.data_collection.cache_ttl_seconds` | `300` |
| `agents.analysis.min_confidence` | `0.7` |
| `agents.analysis.max_segments` | `10` |
| `agents.analysis.trend_lookback_days` | `30` |
| `agents.recommendation.max_recommendations` | `10` |
| `agents.recommendation.min_score` | `0.3` |
| `agents.recommendation.diversity_factor` | `0.2` |
| `agents.recommendation.cache_ttl_seconds` | `600` |
| `agents.cross_sell.max_suggestions` | `5` |
| `agents.cross_sell.min_association_confidence` | `0.5` |
| `agents.cross_sell.bundle_discount_threshold` | `0.1` |
| `agents.optimization.ab_test_split` | `0.5` |
| `agents.optimization.min_sample_size` | `100` |
| `agents.optimization.significance_level` | `0.05` |
| `agents.performance_analytics.metrics_retention_days` | `90` |
| `agents.performance_analytics.report_interval_hours` | `24` |
| `agents.performance_analytics.alert_thresholds.ctr` | `0.02` |
| `agents.performance_analytics.alert_thresholds.conversion_rate` | `0.05` |
| `agents.performance_analytics.alert_thresholds.revenue_per_session` | `50.0` |
| `integrations.shopify.api_version` | `2024-01` |
| `integrations.shopify.rate_limit_per_second` | `2` |
| `integrations.shopify.webhook_secret_header` | `X-Shopify-Hmac-Sha256` |
| `integrations.woocommerce.api_version` | `v3` |
| `integrations.woocommerce.rate_limit_per_second` | `10` |
| `integrations.woocommerce.verify_ssl` | `True` |
| `integrations.magento.api_version` | `V1` |
| `integrations.magento.rate_limit_per_second` | `5` |
| `integrations.magento.verify_ssl` | `True` |
| `cache.backend` | `redis` |
| `cache.ttl_seconds` | `300` |
| `cache.max_entries` | `10000` |
| `monitoring.prometheus_enabled` | `True` |
| `monitoring.metrics_port` | `9090` |
| `monitoring.health_check_interval_seconds` | `30` |

---

## Environment Variables

Set these in your `.env` file or export them in your shell:

| Variable | Default Value | Section |
|----------|---------------|---------|
| `ENVIRONMENT` | `development` | Application |
| `LOG_LEVEL` | `info` | Application |
| `SECRET_KEY` | `change-me-in-production` | Application |
| `HOST` | `0.0.0.0` | Server |
| `PORT` | `8000` | Server |
| `SHOPIFY_SHOP_URL` | `https://your-store.myshopify.com` | Shopify |
| `SHOPIFY_API_KEY` | `your-shopify-api-key` | Shopify |
| `SHOPIFY_API_SECRET` | `your-shopify-api-secret` | Shopify |
| `SHOPIFY_ACCESS_TOKEN` | `your-shopify-access-token` | Shopify |
| `SHOPIFY_API_VERSION` | `2024-01` | Shopify |
| `WOOCOMMERCE_URL` | `https://your-store.com` | WooCommerce |
| `WOOCOMMERCE_CONSUMER_KEY` | `your-woocommerce-consumer-key` | WooCommerce |
| `WOOCOMMERCE_CONSUMER_SECRET` | `your-woocommerce-consumer-secret` | WooCommerce |
| `WOOCOMMERCE_API_VERSION` | `v3` | WooCommerce |
| `MAGENTO_URL` | `https://your-magento-store.com` | Magento |
| `MAGENTO_ACCESS_TOKEN` | `your-magento-access-token` | Magento |
| `MAGENTO_API_VERSION` | `V1` | Magento |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis |
| `REDIS_PASSWORD` | `` | Redis |
| `OPENAI_API_KEY` | `your-openai-api-key` | LangChain / LLM |
| `LANGCHAIN_API_KEY` | `your-langchain-api-key` | LangChain / LLM |
| `LANGCHAIN_TRACING_V2` | `false` | LangChain / LLM |
| `LANGCHAIN_PROJECT` | `product-recommendations` | LangChain / LLM |
| `PROMETHEUS_ENABLED` | `true` | Monitoring |
| `METRICS_PORT` | `9090` | Monitoring |

---

## Full Configuration File

Complete `config.yaml` with all default values:

```yaml
app:
  name: product-recommendations
  version: 0.1.0
  environment: development
  log_level: info
  host: 0.0.0.0
  port: 8000
agents:
  data_collection:
    batch_size: 100
    max_retries: 3
    timeout_seconds: 30
    cache_ttl_seconds: 300
  analysis:
    min_confidence: 0.7
    max_segments: 10
    trend_lookback_days: 30
  recommendation:
    max_recommendations: 10
    min_score: 0.3
    diversity_factor: 0.2
    cache_ttl_seconds: 600
  cross_sell:
    max_suggestions: 5
    min_association_confidence: 0.5
    bundle_discount_threshold: 0.1
  optimization:
    ab_test_split: 0.5
    min_sample_size: 100
    significance_level: 0.05
  performance_analytics:
    metrics_retention_days: 90
    report_interval_hours: 24
    alert_thresholds:
      ctr: 0.02
      conversion_rate: 0.05
      revenue_per_session: 50.0
integrations:
  shopify:
    api_version: 2024-01
    rate_limit_per_second: 2
    webhook_secret_header: X-Shopify-Hmac-Sha256
  woocommerce:
    api_version: v3
    rate_limit_per_second: 10
    verify_ssl: True
  magento:
    api_version: V1
    rate_limit_per_second: 5
    verify_ssl: True
cache:
  backend: redis
  ttl_seconds: 300
  max_entries: 10000
monitoring:
  prometheus_enabled: True
  metrics_port: 9090
  health_check_interval_seconds: 30
```

---

## Example .env File

```bash
# Application
ENVIRONMENT=development
LOG_LEVEL=info
SECRET_KEY=change-me-in-production

# Server
HOST=0.0.0.0
PORT=8000

# Shopify
SHOPIFY_SHOP_URL=https://your-store.myshopify.com
SHOPIFY_API_KEY=your-shopify-api-key
SHOPIFY_API_SECRET=your-shopify-api-secret
SHOPIFY_ACCESS_TOKEN=your-shopify-access-token
SHOPIFY_API_VERSION=2024-01

# WooCommerce
WOOCOMMERCE_URL=https://your-store.com
WOOCOMMERCE_CONSUMER_KEY=your-woocommerce-consumer-key
WOOCOMMERCE_CONSUMER_SECRET=your-woocommerce-consumer-secret
WOOCOMMERCE_API_VERSION=v3

# Magento
MAGENTO_URL=https://your-magento-store.com
MAGENTO_ACCESS_TOKEN=your-magento-access-token
MAGENTO_API_VERSION=V1

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=

# LangChain / LLM
OPENAI_API_KEY=your-openai-api-key
LANGCHAIN_API_KEY=your-langchain-api-key
LANGCHAIN_TRACING_V2=false
LANGCHAIN_PROJECT=product-recommendations

# Monitoring
PROMETHEUS_ENABLED=true
METRICS_PORT=9090

```

---

## Agent Configuration

```yaml
agents:
  analysis:
    max_segments: 10
    min_confidence: 0.7
    trend_lookback_days: 30
  cross_sell:
    bundle_discount_threshold: 0.1
    max_suggestions: 5
    min_association_confidence: 0.5
  data_collection:
    batch_size: 100
    cache_ttl_seconds: 300
    max_retries: 3
    timeout_seconds: 30
  optimization:
    ab_test_split: 0.5
    min_sample_size: 100
    significance_level: 0.05
  performance_analytics:
    alert_thresholds:
      conversion_rate: 0.05
      ctr: 0.02
      revenue_per_session: 50.0
    metrics_retention_days: 90
    report_interval_hours: 24
  recommendation:
    cache_ttl_seconds: 600
    diversity_factor: 0.2
    max_recommendations: 10
    min_score: 0.3
```

---

## Integration Settings

```yaml
integrations:
  magento:
    api_version: V1
    rate_limit_per_second: 5
    verify_ssl: true
  shopify:
    api_version: 2024-01
    rate_limit_per_second: 2
    webhook_secret_header: X-Shopify-Hmac-Sha256
  woocommerce:
    api_version: v3
    rate_limit_per_second: 10
    verify_ssl: true
```

---

## Security Configuration

No explicit security configuration found. See environment variables for API keys and secrets.

---

## Monitoring & Observability

### monitoring

```yaml
monitoring:
  health_check_interval_seconds: 30
  metrics_port: 9090
  prometheus_enabled: true
```

---

## Rate Limiting & Caching

### cache

```yaml
cache:
  backend: redis
  max_entries: 10000
  ttl_seconds: 300
```

---

## Quick Start

### 1. Copy the environment template:

```bash
cd ~/GRC_Claw/projects/product-recommendations
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

*Generated for `product-recommendations` — GRC_Claw Configuration Guide*
