# Account-Based Marketing — Troubleshooting Guide

> **Project:** `account-based-marketing`
> **Description:** AI-powered ABM platform with 6 specialized agents for end-to-end account-based marketing orchestration.
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

This troubleshooting guide covers the most common issues encountered when operating the **Account-Based Marketing** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Account Intelligence Agent | Account Intelligence Agent | `/api/v1/agents/account-intelligence-agent/health` |
| Target Account Selector | Target Account Selector | `/api/v1/agents/target-account-selector/health` |
| Campaign Orchestrator | Campaign Orchestrator | `/api/v1/agents/campaign-orchestrator/health` |
| Engagement Tracker | Engagement Tracker | `/api/v1/agents/engagement-tracker/health` |
| Content Personalizer | Content Personalizer | `/api/v1/agents/content-personalizer/health` |
| ROI Analyzer | ROI Analyzer | `/api/v1/agents/roi-analyzer/health` |

### Key Integrations

- **CRM Systems**
- **Ad Platforms**
- **Intent Data Providers**
- **Sales Engagement Platforms**
- **ABM Platforms**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Target account list not refreshing

**Symptoms:**
- Stale account recommendations
- Intent data not updating
- Account scoring frozen

**Solutions:**
1. Verify intent data source connectivity
1. Check account scoring model refresh
1. Validate ICP matching algorithm
1. Review account list update frequency

**Debugging Steps:**
```bash
Check intent data: GET /api/v1/abm/intent-data
```

```bash
Verify scoring refresh: GET /api/v1/abm/scoring/refresh
```

```bash
Test ICP matching: POST /api/v1/abm/icp/test
```

```bash
Review update frequency: GET /api/v1/abm/config/update-frequency
```

---

### Issue 2: Account engagement tracking gaps

**Symptoms:**
- Website visits not attributed to accounts
- Engagement scoring incomplete
- Multi-threader engagement not consolidated

**Solutions:**
1. Verify IP-to-account resolution
1. Check tracking pixel deployment
1. Validate engagement data consolidation
1. Review account-level attribution

**Debugging Steps:**
```bash
Check IP resolution: GET /api/v1/abm/ip-resolution
```

```bash
Verify tracking: GET /api/v1/abm/tracking/status
```

```bash
Test consolidation: POST /api/v1/abm/consolidation/test
```

```bash
Review attribution: GET /api/v1/abm/attribution
```

---

### Issue 3: Personalization not scaling across accounts

**Symptoms:**
- Generic content served to target accounts
- Personalization API timeouts
- Account-specific content not generating

**Solutions:**
1. Verify personalization engine capacity
1. Check account data completeness
1. Validate content template mapping
1. Review personalization fallback strategy

**Debugging Steps:**
```bash
Check engine capacity: GET /api/v1/abm/personalization/capacity
```

```bash
Verify account data: GET /api/v1/abm/accounts/data-completeness
```

```bash
Test template mapping: POST /api/v1/abm/templates/test
```

```bash
Review fallback: GET /api/v1/abm/personalization/fallback
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
docker logs --tail 500 account-based-marketing-app

# Filter for errors
docker logs account-based-marketing-app 2>&1 | grep -i error

# Search for specific patterns
docker logs account-based-marketing-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs account-based-marketing-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats account-based-marketing-app

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
psql -h localhost -U account-based-marketing -d account-based-marketing_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/account-based-marketing` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull account-based-marketing:latest` |
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
