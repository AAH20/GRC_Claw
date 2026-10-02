# Product Recommendations — Troubleshooting Guide

> **Project:** `product-recommendations`
> **Description:** Agentic AI product recommendations engine for e-commerce platforms.
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

This troubleshooting guide covers the most common issues encountered when operating the **Product Recommendations** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Recommendation Engine | Recommendation Engine | `/api/v1/agents/recommendation-engine/health` |
| Personalization Agent | Personalization Agent | `/api/v1/agents/personalization-agent/health` |
| Inventory Filter | Inventory Filter | `/api/v1/agents/inventory-filter/health` |
| A/B Testing Agent | A/B Testing Agent | `/api/v1/agents/a/b-testing-agent/health` |
| Analytics Agent | Analytics Agent | `/api/v1/agents/analytics-agent/health` |

### Key Integrations

- **E-commerce Platforms**
- **CDP Systems**
- **Inventory Management**
- **Analytics Platforms**
- **ML Model Serving**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Recommendations showing out-of-stock items

**Symptoms:**
- Customers clicking unavailable products
- Inventory sync delays
- Recommendation relevance dropping

**Solutions:**
1. Verify inventory sync frequency
1. Check real-time inventory API
1. Validate recommendation filtering logic
1. Review cache invalidation strategy

**Debugging Steps:**
```bash
Check inventory sync: GET /api/v1/recs/inventory-sync
```

```bash
Verify real-time inventory: GET /api/v1/recs/inventory/realtime
```

```bash
Test filtering: POST /api/v1/recs/filter-test
```

```bash
Review cache config: GET /api/v1/config/cache
```

---

### Issue 2: Cold start problem for new users

**Symptoms:**
- New visitors getting generic recommendations
- Low conversion on first visit
- Personalization not kicking in

**Solutions:**
1. Verify fallback recommendation strategy
1. Check behavioral tracking implementation
1. Validate session-based recommendations
1. Review popularity-based fallback

**Debugging Steps:**
```bash
Check fallback strategy: GET /api/v1/recs/fallback
```

```bash
Verify tracking: GET /api/v1/recs/tracking
```

```bash
Test session recs: POST /api/v1/recs/session-test
```

```bash
Review popularity config: GET /api/v1/recs/popularity
```

---

### Issue 3: Recommendation diversity issues

**Symptoms:**
- Same products recommended repeatedly
- Filter bubble effect
- Cross-category recommendations missing

**Solutions:**
1. Verify diversity injection algorithm
1. Check category coverage in training data
1. Validate exploration vs exploitation balance
1. Review serendipity settings

**Debugging Steps:**
```bash
Check diversity config: GET /api/v1/recs/diversity
```

```bash
Review category coverage: GET /api/v1/recs/categories
```

```bash
Test exploration: POST /api/v1/recs/exploration-test
```

```bash
Review serendipity: GET /api/v1/recs/serendipity
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
docker logs --tail 500 product-recommendations-app

# Filter for errors
docker logs product-recommendations-app 2>&1 | grep -i error

# Search for specific patterns
docker logs product-recommendations-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs product-recommendations-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats product-recommendations-app

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
psql -h localhost -U product-recommendations -d product-recommendations_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/product-recommendations` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull product-recommendations:latest` |
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
