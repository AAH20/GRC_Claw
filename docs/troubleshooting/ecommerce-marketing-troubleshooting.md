# E-commerce Marketing — Troubleshooting Guide

> **Project:** `ecommerce-marketing`
> **Description:** AI-powered e-commerce marketing automation platform for product promotion, cart recovery, and customer engagement.
> **Last Updated:** 2026-10-02

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Common Issues & Solutions](#common-issues--solutions)
4. [Debugging Steps](#debugging-steps)
5. [Preventive Measures](#preventive-measures)
6. [Escalation Procedures](#escalation-procedures)
7. [Additional Resources](#additional-resources)

---

## Overview

This troubleshooting guide covers the most common issues encountered when operating the **E-commerce Marketing** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

### Quick Health Check

```bash
# Check overall system health
curl -s http://localhost:8080/api/v1/health | jq .

# Check agent status
curl -s http://localhost:8080/api/v1/agents/status | jq .

# Check recent errors
curl -s "http://localhost:8080/api/v1/logs?level=error&limit=20" | jq .
```

---

## Architecture

### Core Agents

| Agent | Role | Health Endpoint |
|-------|------|-----------------|
| Product Promoter | Product Promoter | `/api/v1/agents/product-promoter/health` |
| Cart Recovery Agent | Cart Recovery Agent | `/api/v1/agents/cart-recovery-agent/health` |
| Recommendation Engine | Recommendation Engine | `/api/v1/agents/recommendation-engine/health` |
| Review Manager | Review Manager | `/api/v1/agents/review-manager/health` |
| Loyalty Optimizer | Loyalty Optimizer | `/api/v1/agents/loyalty-optimizer/health` |

### Key Integrations

- **Shopify**
- **WooCommerce**
- **Magento**
- **BigCommerce**
- **Payment Gateways**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Cart abandonment emails not sending

**Symptoms:**
- Abandoned carts not triggering emails
- Email personalization missing product details
- Send timing not optimized

**Solutions:**
1. Verify cart abandonment detection
1. Check email trigger configuration
1. Validate product data in email templates
1. Review send timing optimization

**Debugging Steps:**
```bash
Check detection: GET /api/v1/ecommerce/detection
```

```bash
Verify triggers: GET /api/v1/ecommerce/triggers
```

```bash
Test templates: POST /api/v1/ecommerce/templates/test
```

```bash
Review timing: GET /api/v1/ecommerce/timing
```

---

### Issue 2: Product recommendation relevance low

**Symptoms:**
- Customers ignoring recommendations
- Cross-sell conversion low
- Recommendation diversity poor

**Solutions:**
1. Verify recommendation algorithm
1. Check product catalog data quality
1. Validate customer behavior tracking
1. Review recommendation placement strategy

**Debugging Steps:**
```bash
Check algorithm: GET /api/v1/ecommerce/algorithm
```

```bash
Verify catalog: GET /api/v1/ecommerce/catalog
```

```bash
Test tracking: POST /api/v1/ecommerce/tracking/test
```

```bash
Review placement: GET /api/v1/ecommerce/placement
```

---

### Issue 3: Promotional pricing conflicts

**Symptoms:**
- Discounts stacking incorrectly
- Margin erosion from promotions
- Price display inconsistencies

**Solutions:**
1. Verify promotion rule engine
1. Check discount stacking rules
1. Validate margin protection
1. Review price display logic

**Debugging Steps:**
```bash
Check rules: GET /api/v1/ecommerce/rules
```

```bash
Verify stacking: GET /api/v1/ecommerce/stacking
```

```bash
Test margin: POST /api/v1/ecommerce/margin/test
```

```bash
Review display: GET /api/v1/ecommerce/display
```

---

## Debugging Steps

### General Diagnostic Procedure

1. **Identify the symptom** — Determine which of the common issues above matches the observed behavior.
2. **Check system health** — Run the quick health check commands to verify overall system status.
3. **Review logs** — Examine application logs for error patterns and stack traces.
4. **Verify integrations** — Test connectivity to all external services and APIs.
5. **Isolate the component** — Narrow down whether the issue is in the agent, API, data layer, or integration.
6. **Apply the solution** — Follow the specific solution steps for the identified issue.
7. **Verify resolution** — Confirm the issue is resolved and monitor for recurrence.

### Log Analysis

```bash
# View recent application logs
docker logs --tail 500 ecommerce-marketing-app

# Filter for errors
docker logs ecommerce-marketing-app 2>&1 | grep -i error

# Search for specific patterns
docker logs ecommerce-marketing-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs ecommerce-marketing-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats ecommerce-marketing-app

# Check database connection pool
curl -s http://localhost:8080/api/v1/db/pool-status | jq .

# Check cache hit rates
curl -s http://localhost:8080/api/v1/cache/stats | jq .

# Profile agent execution time
curl -s http://localhost:8080/api/v1/agents/execution-times | jq .
```

### Network Diagnostics

```bash
# Test external API connectivity
curl -s -o /dev/null -w "%{http_code}" https://api.example.com/health

# Check DNS resolution
dig +short api.example.com

# Verify firewall rules
sudo iptables -L -n | grep 8080

# Test database connectivity
psql -h localhost -U ecommerce-marketing -d ecommerce-marketing_db -c "SELECT 1"
```

---

## Preventive Measures

### Monitoring & Alerting

- Set up health check endpoints with automated alerting
- Monitor agent execution times and failure rates
- Track API response times and error rates
- Alert on resource utilization thresholds (CPU > 80%, memory > 85%)
- Monitor queue depths and processing lag

### Maintenance Schedule

| Task | Frequency | Command |
|------|-----------|---------|
| Log rotation | Daily | `logrotate /etc/logrotate.d/ecommerce-marketing` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull ecommerce-marketing:latest` |
| Backup verification | Weekly | `/opt/scripts/verify-backup.sh` |

### Configuration Management

- Version control all configuration files
- Use environment-specific config overrides
- Implement configuration validation on startup
- Maintain configuration change audit trail
- Use feature flags for gradual rollouts

---

## Escalation Procedures

### Severity Levels

| Level | Description | Response Time | Escalation Path |
|-------|-------------|---------------|-----------------|
| P1 — Critical | System down or data loss | 15 minutes | On-call → Engineering Lead → CTO |
| P2 — High | Major feature impaired | 1 hour | On-call → Engineering Lead |
| P3 — Medium | Minor feature issue | 4 hours | Support → Engineering |
| P4 — Low | Cosmetic or enhancement | 24 hours | Support queue |

### Escalation Contacts

- **L1 Support:** support@grc-claw.com
- **L2 Engineering:** engineering@grc-claw.com
- **L3 On-Call:** oncall@grc-claw.com
- **Emergency:** +1-555-GRC-CLAW

### Information to Collect When Escalating

1. Exact error messages and stack traces
2. Timestamp of when the issue started
3. Recent deployments or configuration changes
4. Affected user/customer count
5. System resource utilization metrics
6. Relevant log excerpts
7. Steps already attempted

---

## Additional Resources

- [GRC_Claw Documentation](../README.md)
- [Architecture Overview](../ARCHITECTURE.md)
- [API Reference](../api-reference.md)
- [Deployment Guide](../deployment.md)
- [Security Audit](../SECURITY-AUDIT.md)
- [Performance Benchmarks](../PERFORMANCE-V17.md)

---

*This guide is maintained by the GRC_Claw engineering team. For contributions or corrections, please submit a pull request or contact the team.*
