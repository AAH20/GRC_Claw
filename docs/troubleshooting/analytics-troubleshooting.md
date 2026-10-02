# Analytics & Attribution — Troubleshooting Guide

> **Project:** `analytics`
> **Description:** Agentic AI marketing analytics and attribution platform with multi-touch attribution and predictive forecasting.
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

This troubleshooting guide covers the most common issues encountered when operating the **Analytics & Attribution** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Data Collector | Data Collector | `/api/v1/agents/data-collector/health` |
| Attribution Engine | Attribution Engine | `/api/v1/agents/attribution-engine/health` |
| Forecast Generator | Forecast Generator | `/api/v1/agents/forecast-generator/health` |
| Report Builder | Report Builder | `/api/v1/agents/report-builder/health` |
| Anomaly Detector | Anomaly Detector | `/api/v1/agents/anomaly-detector/health` |

### Key Integrations

- **Google Analytics**
- **Mixpanel**
- **Amplitude**
- **Segment**
- **Snowflake**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Attribution model producing inconsistent results

**Symptoms:**
- Same journey attributed differently across reports
- Attribution weights not summing to 100%
- Cross-device attribution gaps

**Solutions:**
1. Verify attribution model configuration
1. Check identity resolution logic
1. Validate cross-device tracking setup
1. Review attribution window settings

**Debugging Steps:**
```bash
Check attribution config: GET /api/v1/analytics/attribution/config
```

```bash
Test identity resolution: POST /api/v1/analytics/identity/test
```

```bash
Verify cross-device tracking: GET /api/v1/analytics/cross-device
```

```bash
Review attribution windows: GET /api/v1/analytics/attribution/windows
```

---

### Issue 2: Data pipeline delays and gaps

**Symptoms:**
- Dashboard showing stale data
- Missing events in attribution
- Data freshness indicators red

**Solutions:**
1. Verify data source connectivity
1. Check ETL pipeline job status
1. Validate event schema compatibility
1. Review data retention policies

**Debugging Steps:**
```bash
Check pipeline status: GET /api/v1/analytics/pipeline/status
```

```bash
Verify data sources: GET /api/v1/analytics/sources
```

```bash
Check event schema: GET /api/v1/analytics/schema
```

```bash
Review data freshness: GET /api/v1/analytics/freshness
```

---

### Issue 3: Forecast accuracy degradation

**Symptoms:**
- Predictions diverging from actuals
- Confidence intervals too wide
- Seasonal patterns not captured

**Solutions:**
1. Retrain forecasting models
1. Check for data quality issues
1. Validate feature engineering pipeline
1. Review model hyperparameters

**Debugging Steps:**
```bash
Check model performance: GET /api/v1/analytics/forecast/metrics
```

```bash
Review feature pipeline: GET /api/v1/analytics/features
```

```bash
Validate training data: GET /api/v1/analytics/training-data
```

```bash
Check model config: GET /api/v1/models/forecast/config
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
docker logs --tail 500 analytics-app

# Filter for errors
docker logs analytics-app 2>&1 | grep -i error

# Search for specific patterns
docker logs analytics-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs analytics-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats analytics-app

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
psql -h localhost -U analytics -d analytics_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/analytics` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull analytics:latest` |
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
