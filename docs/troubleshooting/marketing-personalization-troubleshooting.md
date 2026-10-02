# Marketing Personalization — Troubleshooting Guide

> **Project:** `marketing-personalization`
> **Description:** AI-powered marketing personalization platform for campaign management, audience segmentation, and performance optimization.
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

This troubleshooting guide covers the most common issues encountered when operating the **Marketing Personalization** platform. It provides systematic diagnostic procedures, solutions, and debugging steps to quickly identify and resolve problems.

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
| Personalization Engine | Personalization Engine | `/api/v1/agents/personalization-engine/health` |
| Audience Segmenter | Audience Segmenter | `/api/v1/agents/audience-segmenter/health` |
| Campaign Optimizer | Campaign Optimizer | `/api/v1/agents/campaign-optimizer/health` |
| Content Adapter | Content Adapter | `/api/v1/agents/content-adapter/health` |
| Performance Analyzer | Performance Analyzer | `/api/v1/agents/performance-analyzer/health` |

### Key Integrations

- **CDP Systems**
- **CRM Platforms**
- **Email Platforms**
- **Web Personalization Tools**
- **Ad Platforms**

### System Dependencies

- **LangChain DeepAgents** — Agent orchestration framework
- **grc-marketing-core** — Shared marketing library
- **FastAPI** — API server
- **Redis** — Session and cache management
- **PostgreSQL** — Primary data store
- **Docker/Kubernetes** — Container orchestration

---

## Common Issues & Solutions

### Issue 1: Personalization rules conflicting

**Symptoms:**
- Contradictory content served
- Rule priority confusion
- Segment overlap causing conflicts

**Solutions:**
1. Verify rule priority configuration
1. Check segment overlap handling
1. Validate rule conflict resolution
1. Review personalization decision tree

**Debugging Steps:**
```bash
Check rule priorities: GET /api/v1/personalization/priorities
```

```bash
Verify segment overlap: GET /api/v1/personalization/overlap
```

```bash
Test conflict resolution: POST /api/v1/personalization/conflict-test
```

```bash
Review decision tree: GET /api/v1/personalization/decision-tree
```

---

### Issue 2: Real-time personalization latency

**Symptoms:**
- Content loading slowly
- Personalization API timeouts
- Fallback content served too frequently

**Solutions:**
1. Verify personalization API performance
1. Check caching strategy
1. Validate CDN configuration
1. Review timeout and fallback settings

**Debugging Steps:**
```bash
Check API performance: GET /api/v1/personalization/performance
```

```bash
Verify caching: GET /api/v1/personalization/caching
```

```bash
Test CDN config: GET /api/v1/personalization/cdn
```

```bash
Review timeouts: GET /api/v1/personalization/timeouts
```

---

### Issue 3: Personalization data quality issues

**Symptoms:**
- Irrelevant content recommendations
- Outdated customer preferences
- Incomplete customer profiles

**Solutions:**
1. Verify data source freshness
1. Check customer profile completeness
1. Validate preference inference logic
1. Review data quality monitoring

**Debugging Steps:**
```bash
Check data freshness: GET /api/v1/personalization/data-freshness
```

```bash
Verify profile completeness: GET /api/v1/personalization/profiles
```

```bash
Test inference: POST /api/v1/personalization/inference/test
```

```bash
Review monitoring: GET /api/v1/personalization/monitoring
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
docker logs --tail 500 marketing-personalization-app

# Filter for errors
docker logs marketing-personalization-app 2>&1 | grep -i error

# Search for specific patterns
docker logs marketing-personalization-app 2>&1 | grep -i "timeout\|exception\|failed"

# Check agent-specific logs
docker logs marketing-personalization-app 2>&1 | grep -i "agent"
```

### Performance Diagnostics

```bash
# Check resource usage
docker stats marketing-personalization-app

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
psql -h localhost -U marketing-personalization -d marketing-personalization_db -c "SELECT 1"
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
| Log rotation | Daily | `logrotate /etc/logrotate.d/marketing-personalization` |
| Database vacuum | Weekly | `VACUUM ANALYZE;` |
| Cache flush | Weekly | `redis-cli FLUSHDB` |
| Dependency update | Monthly | `pip install --upgrade -r requirements.txt` |
| Security patch | As needed | `docker pull marketing-personalization:latest` |
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
