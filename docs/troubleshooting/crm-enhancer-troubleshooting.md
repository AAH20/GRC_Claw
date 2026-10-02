# CRM Enhancer — Troubleshooting Guide

> **Project:** `crm-enhancer`
> **Description:** AI-powered CRM enhancement platform integrating with Salesforce, HubSpot, and Pipedrive.
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

This troubleshooting guide covers the most common issues encountered when operating the **CRM Enhancer** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Data Enrichment Agent | Data Enrichment Agent | `/api/v1/agents/data-enrichment-agent/health` |
| Contact Deduplication Agent | Contact Deduplication Agent | `/api/v1/agents/contact-deduplication-agent/health` |
| Pipeline Analysis Agent | Pipeline Analysis Agent | `/api/v1/agents/pipeline-analysis-agent/health` |
| Activity Logger | Activity Logger | `/api/v1/agents/activity-logger/health` |
| Insight Generator | Insight Generator | `/api/v1/agents/insight-generator/health` |

### Key Integrations

- **Salesforce API**
- **HubSpot API**
- **Pipedrive API**
- **Clearbit**
- **ZoomInfo**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: CRM data sync failures

**Symptoms:**
- Contacts not appearing in CRM
- Duplicate records created
- Field mapping errors

**Solutions:**
1. Verify CRM API authentication
1. Check field mapping configuration
1. Validate data transformation rules
1. Review sync job error logs

**Debugging Steps:**
```bash
Check CRM connection: GET /api/v1/crm/connection-status
```

```bash
Review field mappings: GET /api/v1/crm/field-mappings
```

```bash
Check sync job logs: GET /api/v1/crm/sync-logs
```

```bash
Test single record sync: POST /api/v1/crm/sync/test
```

---

### Issue 2: Data enrichment returning incomplete results

**Symptoms:**
- Missing company information
- Enrichment API timeouts
- Stale enrichment data

**Solutions:**
1. Verify enrichment API credentials
1. Check enrichment data source coverage
1. Validate enrichment trigger conditions
1. Review enrichment cache TTL settings

**Debugging Steps:**
```bash
Check enrichment API status: GET /api/v1/enrichment/status
```

```bash
Test enrichment lookup: POST /api/v1/enrichment/test
```

```bash
Review cache settings: GET /api/v1/config/enrichment-cache
```

```bash
Check data source coverage: GET /api/v1/enrichment/coverage
```

---

### Issue 3: Pipeline insights not generating

**Symptoms:**
- Pipeline analysis reports empty
- Stage transition predictions missing
- Forecast accuracy declining

**Solutions:**
1. Verify pipeline data completeness
1. Check ML model deployment status
1. Validate stage definition mapping
1. Review insight generation triggers

**Debugging Steps:**
```bash
Check pipeline data: GET /api/v1/crm/pipeline/data
```

```bash
Verify model status: GET /api/v1/models/pipeline/status
```

```bash
Review stage mappings: GET /api/v1/crm/stage-mappings
```

```bash
Test insight generation: POST /api/v1/insights/generate
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
docker logs --tail 500 crm-enhancer-app

# Filter for errors
docker logs crm-enhancer-app 2>&1 | grep -i error

# Search for specific patterns
docker logs crm-enhancer-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs crm-enhancer-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats crm-enhancer-app

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
psql -h localhost -U crm-enhancer -d crm-enhancer_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/crm-enhancer` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull crm-enhancer:latest` |
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
