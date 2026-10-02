# Customer Segmentation — Troubleshooting Guide

> **Project:** `customer-segmentation`
> **Description:** AI-powered customer segmentation platform for data collection, analysis, strategy formulation, and performance tracking.
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

This troubleshooting guide covers the most common issues encountered when operating the **Customer Segmentation** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Segmentation Engine | Segmentation Engine | `/api/v1/agents/segmentation-engine/health` |
| Strategy Agent | Strategy Agent | `/api/v1/agents/strategy-agent/health` |
| Performance Tracker | Performance Tracker | `/api/v1/agents/performance-tracker/health` |
| Insight Generator | Insight Generator | `/api/v1/agents/insight-generator/health` |

### Key Integrations

- **CRM Systems**
- **Analytics Platforms**
- **CDP Systems**
- **Data Warehouses**
- **ML Platforms**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Segment sizes becoming unbalanced

**Symptoms:**
- One segment dominating population
- Small segments disappearing
- Segment boundaries shifting unexpectedly

**Solutions:**
1. Verify segmentation algorithm parameters
1. Check data distribution changes
1. Validate minimum segment size thresholds
1. Review segment stability metrics

**Debugging Steps:**
```bash
Check segment sizes: GET /api/v1/segmentation/sizes
```

```bash
Verify algorithm params: GET /api/v1/segmentation/params
```

```bash
Test stability: POST /api/v1/segmentation/stability/test
```

```bash
Review thresholds: GET /api/v1/segmentation/thresholds
```

---

### Issue 2: Segment profiles not updating

**Symptoms:**
- Stale customer attributes in segments
- New customers not assigned to segments
- Segment migration not occurring

**Solutions:**
1. Verify segment refresh schedule
1. Check customer data pipeline
1. Validate segment assignment logic
1. Review segment update triggers

**Debugging Steps:**
```bash
Check refresh schedule: GET /api/v1/segmentation/refresh
```

```bash
Verify data pipeline: GET /api/v1/segmentation/pipeline
```

```bash
Test assignment: POST /api/v1/segmentation/assign/test
```

```bash
Review triggers: GET /api/v1/segmentation/triggers
```

---

### Issue 3: Segment-based campaigns underperforming

**Symptoms:**
- Low engagement within segments
- Segment conversion rates declining
- Cross-segment cannibalization

**Solutions:**
1. Verify segment definition relevance
1. Check campaign targeting accuracy
1. Validate segment-specific messaging
1. Review segment performance benchmarks

**Debugging Steps:**
```bash
Check segment definitions: GET /api/v1/segmentation/definitions
```

```bash
Verify targeting: GET /api/v1/segmentation/targeting
```

```bash
Test messaging: POST /api/v1/segmentation/messaging/test
```

```bash
Review benchmarks: GET /api/v1/segmentation/benchmarks
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
docker logs --tail 500 customer-segmentation-app

# Filter for errors
docker logs customer-segmentation-app 2>&1 | grep -i error

# Search for specific patterns
docker logs customer-segmentation-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs customer-segmentation-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats customer-segmentation-app

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
psql -h localhost -U customer-segmentation -d customer-segmentation_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/customer-segmentation` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull customer-segmentation:latest` |
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
