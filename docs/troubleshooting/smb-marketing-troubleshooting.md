# SMB Marketing — Troubleshooting Guide

> **Project:** `smb-marketing`
> **Description:** Agentic AI marketing platform for small businesses with simplified workflows and budget optimization.
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

This troubleshooting guide covers the most common issues encountered when operating the **SMB Marketing** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Campaign Builder | Campaign Builder | `/api/v1/agents/campaign-builder/health` |
| Budget Optimizer | Budget Optimizer | `/api/v1/agents/budget-optimizer/health` |
| Content Creator | Content Creator | `/api/v1/agents/content-creator/health` |
| Local SEO Agent | Local SEO Agent | `/api/v1/agents/local-seo-agent/health` |
| Review Manager | Review Manager | `/api/v1/agents/review-manager/health` |

### Key Integrations

- **Google Business Profile**
- **Facebook**
- **Instagram**
- **Google Ads**
- **Local Directories**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Budget allocation too aggressive for SMB scale

**Symptoms:**
- Daily budgets exhausted quickly
- Campaigns paused due to budget limits
- ROI negative due to overspend

**Solutions:**
1. Verify SMB-specific budget caps
1. Check budget pacing for small accounts
1. Validate cost-per-acquisition targets
1. Review budget recommendation algorithm

**Debugging Steps:**
```bash
Check budget caps: GET /api/v1/smb/budget-caps
```

```bash
Verify pacing: GET /api/v1/smb/pacing
```

```bash
Test CPA targets: POST /api/v1/smb/cpa/test
```

```bash
Review algorithm: GET /api/v1/smb/algorithm
```

---

### Issue 2: Local SEO optimization not effective

**Symptoms:**
- Local pack rankings not improving
- Google Business Profile issues
- Local citation inconsistencies

**Solutions:**
1. Verify GBP optimization
1. Check local citation consistency
1. Validate review generation strategy
1. Review local keyword targeting

**Debugging Steps:**
```bash
Check GBP: GET /api/v1/smb/gbp
```

```bash
Verify citations: GET /api/v1/smb/citations
```

```bash
Test reviews: POST /api/v1/smb/reviews/test
```

```bash
Review keywords: GET /api/v1/smb/keywords
```

---

### Issue 3: Multi-location management complexity

**Symptoms:**
- Location-specific campaigns conflicting
- Inconsistent branding across locations
- Reporting not aggregating correctly

**Solutions:**
1. Verify multi-location campaign structure
1. Check brand consistency rules
1. Validate location-level reporting
1. Review location hierarchy configuration

**Debugging Steps:**
```bash
Check structure: GET /api/v1/smb/structure
```

```bash
Verify branding: GET /api/v1/smb/branding
```

```bash
Test reporting: POST /api/v1/smb/reporting/test
```

```bash
Review hierarchy: GET /api/v1/smb/hierarchy
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
docker logs --tail 500 smb-marketing-app

# Filter for errors
docker logs smb-marketing-app 2>&1 | grep -i error

# Search for specific patterns
docker logs smb-marketing-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs smb-marketing-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats smb-marketing-app

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
psql -h localhost -U smb-marketing -d smb-marketing_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/smb-marketing` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull smb-marketing:latest` |
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
