# Campaign Optimizer — Troubleshooting Guide

> **Project:** `campaign-optimizer`
> **Description:** Multi-agent AI marketing platform for autonomous campaign strategy, optimization, and governance.
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

This troubleshooting guide covers the most common issues encountered when operating the **Campaign Optimizer** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Strategy Agent | Strategy Agent | `/api/v1/agents/strategy-agent/health` |
| Budget Allocation Agent | Budget Allocation Agent | `/api/v1/agents/budget-allocation-agent/health` |
| Audience Targeting Agent | Audience Targeting Agent | `/api/v1/agents/audience-targeting-agent/health` |
| Creative Optimization Agent | Creative Optimization Agent | `/api/v1/agents/creative-optimization-agent/health` |
| Performance Analysis Agent | Performance Analysis Agent | `/api/v1/agents/performance-analysis-agent/health` |

### Key Integrations

- **Google Ads**
- **Meta Ads**
- **LinkedIn Ads**
- **TikTok Ads**
- **CRM Systems**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Campaign budget overallocation causing overspend

**Symptoms:**
- Daily spend exceeds budget by >20%
- Budget pacing alerts firing
- Unexpected cost spikes in ad platforms

**Solutions:**
1. Verify budget allocation weights in config.yaml
1. Check for race conditions in concurrent budget updates
1. Review agent decision logs for anomalous allocation decisions
1. Implement budget guardrails with hard caps

**Debugging Steps:**
```bash
Check agent decision logs at /var/log/campaign-optimizer/decisions/
```

```bash
Query budget allocation API: GET /api/v1/budget/status
```

```bash
Review recent config changes: git log --oneline -20 -- config/
```

```bash
Validate budget pacing algorithm output against actual spend
```

---

### Issue 2: Agent loop stuck in optimization cycle

**Symptoms:**
- Campaign stuck in 'optimizing' state
- No new creative variants generated
- Agent heartbeat missing

**Solutions:**
1. Restart the optimization agent container
1. Check for deadlock in agent communication queue
1. Verify LangChain DeepAgents session state
1. Clear stuck sessions from Redis

**Debugging Steps:**
```bash
Check agent health: GET /api/v1/agents/health
```

```bash
Inspect Redis for stuck session keys: KEYS session:*
```

```bash
Review agent logs for timeout patterns: grep 'timeout' logs/agent.log
```

```bash
Force session reset: POST /api/v1/sessions/reset
```

---

### Issue 3: Attribution data mismatch between platforms

**Symptoms:**
- Conversion counts differ across ad platforms
- ROAS calculations inconsistent
- Attribution model producing illogical results

**Solutions:**
1. Verify UTM parameter consistency across campaigns
1. Check attribution window configuration
1. Validate data pipeline ETL jobs
1. Reconcile platform APIs with internal data warehouse

**Debugging Steps:**
```bash
Compare UTM parameters: SELECT utm_source, COUNT(*) FROM events GROUP BY utm_source
```

```bash
Check attribution window: GET /api/v1/attribution/config
```

```bash
Validate ETL pipeline: GET /api/v1/pipeline/status
```

```bash
Run attribution reconciliation: POST /api/v1/attribution/reconcile
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
docker logs --tail 500 campaign-optimizer-app

# Filter for errors
docker logs campaign-optimizer-app 2>&1 | grep -i error

# Search for specific patterns
docker logs campaign-optimizer-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs campaign-optimizer-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats campaign-optimizer-app

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
psql -h localhost -U campaign-optimizer -d campaign-optimizer_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/campaign-optimizer` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull campaign-optimizer:latest` |
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
