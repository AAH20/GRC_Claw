# Pricing Optimizer — Troubleshooting Guide

> **Project:** `pricing-optimizer`
> **Description:** AI-powered pricing optimization for e-commerce with market analysis, A/B testing, and performance monitoring.
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

This troubleshooting guide covers the most common issues encountered when operating the **Pricing Optimizer** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Market Analyzer | Market Analyzer | `/api/v1/agents/market-analyzer/health` |
| Price Recommender | Price Recommender | `/api/v1/agents/price-recommender/health` |
| A/B Test Manager | A/B Test Manager | `/api/v1/agents/a/b-test-manager/health` |
| Competitor Monitor | Competitor Monitor | `/api/v1/agents/competitor-monitor/health` |
| Performance Tracker | Performance Tracker | `/api/v1/agents/performance-tracker/health` |

### Key Integrations

- **E-commerce Platforms**
- **Competitor Price Trackers**
- **Inventory Systems**
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

### Issue 1: Price recommendations causing margin erosion

**Symptoms:**
- Prices dropping below cost
- Margin percentages declining
- Competitive pricing too aggressive

**Solutions:**
1. Verify margin floor configuration
1. Check competitor price weighting
1. Validate demand elasticity model
1. Review price change approval workflow

**Debugging Steps:**
```bash
Check margin floors: GET /api/v1/pricing/margin-floors
```

```bash
Verify competitor weighting: GET /api/v1/pricing/competitor-weight
```

```bash
Test elasticity model: POST /api/v1/pricing/elasticity/test
```

```bash
Review approval workflow: GET /api/v1/pricing/approvals
```

---

### Issue 2: A/B test results inconclusive

**Symptoms:**
- Tests running too long without significance
- Sample sizes insufficient
- Test variants not properly randomized

**Solutions:**
1. Verify statistical significance calculation
1. Check sample size requirements
1. Validate randomization algorithm
1. Review test duration limits

**Debugging Steps:**
```bash
Check test status: GET /api/v1/pricing/ab-tests
```

```bash
Verify significance calc: GET /api/v1/pricing/significance
```

```bash
Test randomization: POST /api/v1/pricing/randomization/test
```

```bash
Review test config: GET /api/v1/pricing/test-config
```

---

### Issue 3: Competitor price data staleness

**Symptoms:**
- Competitor prices not updating
- Price matching decisions based on old data
- Competitor tracking coverage gaps

**Solutions:**
1. Verify competitor tracking job status
1. Check data source API connectivity
1. Validate price extraction logic
1. Review competitor coverage configuration

**Debugging Steps:**
```bash
Check tracking jobs: GET /api/v1/pricing/competitor-jobs
```

```bash
Verify data sources: GET /api/v1/pricing/data-sources
```

```bash
Test price extraction: POST /api/v1/pricing/extraction/test
```

```bash
Review coverage: GET /api/v1/pricing/competitor-coverage
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
docker logs --tail 500 pricing-optimizer-app

# Filter for errors
docker logs pricing-optimizer-app 2>&1 | grep -i error

# Search for specific patterns
docker logs pricing-optimizer-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs pricing-optimizer-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats pricing-optimizer-app

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
psql -h localhost -U pricing-optimizer -d pricing-optimizer_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/pricing-optimizer` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull pricing-optimizer:latest` |
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
