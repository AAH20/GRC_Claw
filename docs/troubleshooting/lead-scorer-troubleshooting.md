# Lead Scorer — Troubleshooting Guide

> **Project:** `lead-scorer`
> **Description:** 7-agent system for automated lead intelligence, scoring, qualification, churn prediction, and next-best-action recommendations.
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

This troubleshooting guide covers the most common issues encountered when operating the **Lead Scorer** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Lead Intelligence Agent | Lead Intelligence Agent | `/api/v1/agents/lead-intelligence-agent/health` |
| Scoring Agent | Scoring Agent | `/api/v1/agents/scoring-agent/health` |
| Qualification Agent | Qualification Agent | `/api/v1/agents/qualification-agent/health` |
| Churn Prediction Agent | Churn Prediction Agent | `/api/v1/agents/churn-prediction-agent/health` |
| Next-Best-Action Agent | Next-Best-Action Agent | `/api/v1/agents/next-best-action-agent/health` |
| Enrichment Agent | Enrichment Agent | `/api/v1/agents/enrichment-agent/health` |
| Routing Agent | Routing Agent | `/api/v1/agents/routing-agent/health` |

### Key Integrations

- **Salesforce**
- **HubSpot**
- **Pipedrive**
- **LinkedIn Sales Navigator**
- **Clearbit**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Lead scores not updating in real-time

**Symptoms:**
- Stale lead scores displayed
- Score changes not reflected in CRM
- Webhook delivery failures

**Solutions:**
1. Verify webhook endpoint connectivity
1. Check event processing queue depth
1. Validate scoring model version deployment
1. Review CRM sync job status

**Debugging Steps:**
```bash
Check webhook delivery logs: GET /api/v1/webhooks/deliveries
```

```bash
Monitor queue depth: GET /api/v1/queue/status
```

```bash
Verify model version: GET /api/v1/models/active
```

```bash
Test CRM sync: POST /api/v1/crm/sync/test
```

---

### Issue 2: Scoring model producing biased results

**Symptoms:**
- Certain segments consistently scored lower
- Score distribution skewed
- False positive rate increasing

**Solutions:**
1. Audit training data for representation bias
1. Review feature engineering pipeline
1. Check for data leakage in model training
1. Implement fairness constraints in scoring algorithm

**Debugging Steps:**
```bash
Analyze score distribution: GET /api/v1/scores/distribution
```

```bash
Review feature importance: GET /api/v1/models/feature-importance
```

```bash
Check training data stats: GET /api/v1/models/training-stats
```

```bash
Run bias audit: POST /api/v1/models/bias-audit
```

---

### Issue 3: Churn prediction accuracy degradation

**Symptoms:**
- Churn predictions missing actual churns
- Model confidence scores dropping
- False negative rate increasing

**Solutions:**
1. Retrain model with recent data
1. Check for concept drift in input features
1. Validate data pipeline freshness
1. Review feature store for missing data

**Debugging Steps:**
```bash
Check model performance metrics: GET /api/v1/models/churn/metrics
```

```bash
Analyze feature drift: GET /api/v1/models/churn/drift
```

```bash
Verify data freshness: GET /api/v1/data/freshness
```

```bash
Trigger retraining: POST /api/v1/models/churn/retrain
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
docker logs --tail 500 lead-scorer-app

# Filter for errors
docker logs lead-scorer-app 2>&1 | grep -i error

# Search for specific patterns
docker logs lead-scorer-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs lead-scorer-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats lead-scorer-app

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
psql -h localhost -U lead-scorer -d lead-scorer_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/lead-scorer` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull lead-scorer:latest` |
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
