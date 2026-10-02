# SEO Optimizer — Troubleshooting Guide

> **Project:** `seo-optimizer`
> **Description:** AI-powered SEO optimization platform for keyword research, content optimization, technical SEO, and monitoring.
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

This troubleshooting guide covers the most common issues encountered when operating the **SEO Optimizer** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Keyword Researcher | Keyword Researcher | `/api/v1/agents/keyword-researcher/health` |
| Content Optimizer | Content Optimizer | `/api/v1/agents/content-optimizer/health` |
| Technical SEO Auditor | Technical SEO Auditor | `/api/v1/agents/technical-seo-auditor/health` |
| Link Building Agent | Link Building Agent | `/api/v1/agents/link-building-agent/health` |
| Rank Tracker | Rank Tracker | `/api/v1/agents/rank-tracker/health` |

### Key Integrations

- **Google Search Console**
- **Google Analytics**
- **Ahrefs API**
- **SEMrush API**
- **Screaming Frog**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Rank tracking data not updating

**Symptoms:**
- Rankings showing stale data
- SERP feature tracking missing
- Keyword position changes not detected

**Solutions:**
1. Verify rank tracking API connectivity
1. Check keyword database sync status
1. Validate SERP parsing logic
1. Review tracking frequency configuration

**Debugging Steps:**
```bash
Check rank tracking status: GET /api/v1/seo/ranks/status
```

```bash
Verify keyword sync: GET /api/v1/seo/keywords/sync-status
```

```bash
Test SERP parsing: POST /api/v1/seo/serp/test-parse
```

```bash
Review tracking config: GET /api/v1/config/rank-tracking
```

---

### Issue 2: Technical SEO audit false positives

**Symptoms:**
- Valid pages flagged as broken
- Canonical issues reported incorrectly
- Mobile usability errors on valid pages

**Solutions:**
1. Verify crawler user-agent configuration
1. Check for JavaScript rendering issues
1. Validate canonical detection logic
1. Review mobile viewport detection

**Debugging Steps:**
```bash
Check crawler config: GET /api/v1/seo/crawler/config
```

```bash
Test page rendering: POST /api/v1/seo/crawler/test-page
```

```bash
Review canonical detection: GET /api/v1/seo/canonicals
```

```bash
Check mobile detection: GET /api/v1/seo/mobile-audit
```

---

### Issue 3: Keyword research returning irrelevant results

**Symptoms:**
- Keywords with low search volume
- Irrelevant keyword suggestions
- Difficulty scores inaccurate

**Solutions:**
1. Verify keyword API data quality
1. Check search volume data freshness
1. Validate keyword clustering algorithm
1. Review competitor keyword analysis

**Debugging Steps:**
```bash
Check keyword data source: GET /api/v1/seo/keywords/source
```

```bash
Verify search volume data: GET /api/v1/seo/keywords/volume
```

```bash
Test clustering: POST /api/v1/seo/keywords/cluster-test
```

```bash
Review competitor analysis: GET /api/v1/seo/competitors/keywords
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
docker logs --tail 500 seo-optimizer-app

# Filter for errors
docker logs seo-optimizer-app 2>&1 | grep -i error

# Search for specific patterns
docker logs seo-optimizer-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs seo-optimizer-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats seo-optimizer-app

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
psql -h localhost -U seo-optimizer -d seo-optimizer_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/seo-optimizer` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull seo-optimizer:latest` |
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
