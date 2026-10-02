# Business Intelligence — Troubleshooting Guide

> **Project:** `business-intelligence`
> **Description:** Agentic AI business intelligence platform integrating with Tableau, Power BI, and Looker.
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

This troubleshooting guide covers the most common issues encountered when operating the **Business Intelligence** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Data Analyzer | Data Analyzer | `/api/v1/agents/data-analyzer/health` |
| Report Generator | Report Generator | `/api/v1/agents/report-generator/health` |
| Insight Engine | Insight Engine | `/api/v1/agents/insight-engine/health` |
| Query Optimizer | Query Optimizer | `/api/v1/agents/query-optimizer/health` |
| Alert Manager | Alert Manager | `/api/v1/agents/alert-manager/health` |

### Key Integrations

- **Tableau**
- **Power BI**
- **Looker**
- **Data Warehouses**
- **SQL Databases**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Report generation failures

**Symptoms:**
- Reports timing out
- Data source connection errors
- Visualization rendering issues

**Solutions:**
1. Verify data source connectivity
1. Check query performance
1. Validate report template configuration
1. Review report generation queue

**Debugging Steps:**
```bash
Check data sources: GET /api/v1/bi/data-sources
```

```bash
Verify query performance: GET /api/v1/bi/query-performance
```

```bash
Test templates: POST /api/v1/bi/templates/test
```

```bash
Review queue: GET /api/v1/bi/queue
```

---

### Issue 2: Data warehouse sync delays

**Symptoms:**
- Stale data in reports
- ETL job failures
- Data freshness indicators red

**Solutions:**
1. Verify ETL job status
1. Check data warehouse connectivity
1. Validate sync schedule
1. Review data pipeline monitoring

**Debugging Steps:**
```bash
Check ETL jobs: GET /api/v1/bi/etl-jobs
```

```bash
Verify warehouse: GET /api/v1/bi/warehouse
```

```bash
Test sync: POST /api/v1/bi/sync/test
```

```bash
Review monitoring: GET /api/v1/bi/monitoring
```

---

### Issue 3: Insight generation not actionable

**Symptoms:**
- Generic insights not specific to business
- Alert fatigue from too many notifications
- Insight relevance scoring low

**Solutions:**
1. Verify insight generation prompts
1. Check business context integration
1. Validate alert threshold configuration
1. Review insight feedback loop

**Debugging Steps:**
```bash
Check prompts: GET /api/v1/bi/prompts
```

```bash
Verify context: GET /api/v1/bi/context
```

```bash
Test thresholds: POST /api/v1/bi/thresholds/test
```

```bash
Review feedback: GET /api/v1/bi/feedback
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
docker logs --tail 500 business-intelligence-app

# Filter for errors
docker logs business-intelligence-app 2>&1 | grep -i error

# Search for specific patterns
docker logs business-intelligence-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs business-intelligence-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats business-intelligence-app

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
psql -h localhost -U business-intelligence -d business-intelligence_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/business-intelligence` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull business-intelligence:latest` |
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
